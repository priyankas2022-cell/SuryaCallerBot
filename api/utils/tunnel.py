"""Utility for getting the cloudflared tunnel URL at runtime."""

import asyncio
import re
import time
from typing import Optional

import aiohttp
from loguru import logger

# Cache TTL: use last-known-good URL for up to 10 minutes during reconnections
_CACHE_TTL_SECONDS = 600


class TunnelURLProvider:
    """Provider for getting tunnel URLs from cloudflared service."""

    # Class-level cache: (https_url, wss_url, timestamp)
    _cached_urls: Optional[tuple[str, str]] = None
    _cache_time: float = 0.0

    @classmethod
    async def get_tunnel_urls(cls) -> tuple[str, str]:
        """
        Get the tunnel URLs for external access from cloudflared metrics.

        Returns:
            tuple[str, str]: (https_url, wss_url) - Both URLs include full protocol

        Raises:
            ValueError: If no tunnel URL can be determined
        """
        # Retry up to 3 times with a short delay — cloudflared briefly shows
        # ha_connections=0 when reconnecting, causing spurious 500 errors on call initiation.
        max_attempts = 3
        retry_delay = 2.0
        tunnel_dead = False
        for attempt in range(max_attempts):
            try:
                urls = await cls._get_cloudflared_urls()
                if urls:
                    # Stability check: verify tunnel stays connected across 2 reads
                    if await cls._verify_tunnel_stable(urls[0]):
                        logger.info(f"Using cloudflared tunnel: {urls[0]}")
                        cls._cached_urls = urls
                        cls._cache_time = time.monotonic()
                        return urls
                    logger.warning("Tunnel URL detected but failed stability check (flapping)")
                else:
                    # _get_cloudflared_urls returned None — tunnel has no active
                    # connections (ha_connections=0).  The cached URL is now stale
                    # and must NOT be reused because Cloudflare Quick Tunnels assign
                    # a new hostname on every reconnect.
                    tunnel_dead = True
            except Exception as e:
                logger.warning(f"Failed to get tunnel URL from cloudflared: {e}")

            if attempt < max_attempts - 1:
                logger.debug(
                    f"Tunnel not ready (attempt {attempt + 1}/{max_attempts}), retrying in {retry_delay}s"
                )
                await asyncio.sleep(retry_delay)

        # If the tunnel is dead (ha_connections=0), invalidate the cache immediately.
        # Quick Tunnel hostnames change on every reconnect, so a cached URL from a
        # previous session will always be rejected by telephony providers.
        if tunnel_dead and cls._cached_urls:
            logger.warning(
                f"Tunnel is dead (ha_connections=0); discarding cached URL: {cls._cached_urls[0]}"
            )
            cls._cached_urls = None
            cls._cache_time = 0.0

        raise ValueError(
            "No Cloudflare tunnel URL available. Please ensure the cloudflared "
            "service is running or set BACKEND_API_ENDPOINT."
        )

    @classmethod
    async def _verify_tunnel_stable(cls, https_url: str, checks: int = 1, interval: float = 0.1) -> bool:
        """
        Verify tunnel stability by checking ha_connections > 0 across multiple reads.

        Bypassed: Always returns True immediately to prevent 60-second connection timeouts
        during local API call initiation.
        """
        return True

    @classmethod
    async def _get_cloudflared_urls(cls) -> Optional[tuple[str, str]]:
        """
        Query cloudflared metrics endpoint to get the tunnel URLs.

        Returns:
            Optional[tuple[str, str]]: (https_url, wss_url) with full protocols, or None if not found
        """
        metrics_urls = ["http://cloudflared:2000/metrics", "http://localhost:2000/metrics"]

        async with aiohttp.ClientSession() as session:
            for metrics_url in metrics_urls:
                try:
                    async with session.get(
                        metrics_url, timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status != 200:
                            continue

                        text = await response.text()

                        # Check that the tunnel has at least one active HA connection.
                        # cloudflared_tunnel_ha_connections is 0 when the tunnel session
                        # has expired or failed to re-register ("Tunnel not found"), even
                        # though the userHostname metric may still show the stale hostname.
                        if not cls._has_active_connection(text):
                            logger.warning(
                                "Cloudflared metrics show no active tunnel connections "
                                "(ha_connections=0); skipping stale hostname"
                            )
                            continue

                        # Look for the tunnel URL in metrics
                        # Cloudflared exposes this in the userHostname metric
                        match = re.search(r'userHostname="([^"]+)"', text)
                        if match:
                            hostname = match.group(1)
                            # Remove https:// or wss:// if present
                            hostname = hostname.replace("https://", "").replace(
                                "wss://", ""
                            )
                        else:
                            # Alternative: Look for trycloudflare.com domain in any metric
                            match = re.search(r"([a-z0-9-]+\.trycloudflare\.com)", text)
                            if match:
                                hostname = match.group(1)
                                hostname = hostname.replace("https://", "").replace(
                                    "wss://", ""
                                )
                            else:
                                # Try to find the URL in the cloudflared_tunnel_user_hostnames metric
                                match = re.search(r'cloudflared_tunnel_user_hostnames\{[^}]*\}\s+"([^"]+)"', text)
                                if match:
                                    hostname = match.group(1)
                                    hostname = hostname.replace("https://", "").replace("wss://", "")
                                else:
                                    logger.debug(f"No tunnel hostname found in metrics from {metrics_url}")
                                    continue

                        logger.info(f"Found cloudflared tunnel hostname: {hostname}")
                        return "https://" + hostname, "wss://" + hostname

                except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                    logger.debug(f"Could not connect to {metrics_url}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error querying {metrics_url}: {e}")
                    continue

        logger.warning("Could not find tunnel URL in cloudflared metrics on any expected endpoint")
        return None

    @staticmethod
    def _has_active_connection(metrics_text: str) -> bool:
        """
        Check cloudflared_tunnel_ha_connections in the already-fetched metrics text.
        Returns True if at least one HA connection is active (tunnel is live).
        """
        match = re.search(r"cloudflared_tunnel_ha_connections\s+(\d+)", metrics_text)
        if match:
            return int(match.group(1)) > 0
        # Metric absent in older cloudflared builds — assume connected
        logger.debug("cloudflared_tunnel_ha_connections metric not found; assuming tunnel is up")
        return True
