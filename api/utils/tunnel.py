"""Utility for getting the cloudflared tunnel URL at runtime."""

import asyncio
import re
from typing import Optional

import aiohttp
from loguru import logger


class TunnelURLProvider:
    """Provider for getting tunnel URLs from cloudflared service."""

    @classmethod
    async def get_tunnel_urls(cls) -> tuple[str, str]:
        """
        Get the tunnel URLs for external access from cloudflared metrics.

        Returns:
            tuple[str, str]: (https_url, wss_url) - Both URLs include full protocol

        Raises:
            ValueError: If no tunnel URL can be determined
        """
        try:
            # Try to get URL from cloudflared metrics
            urls = await cls._get_cloudflared_urls()
            if urls:
                logger.info(f"Using cloudflared tunnel: {urls[0]}")
                return urls
        except Exception as e:
            logger.warning(f"Failed to get tunnel URL from cloudflared: {e}")

        raise ValueError(
            "No Cloudflare tunnel URL available. Please ensure the cloudflared "
            "service is running or set BACKEND_API_ENDPOINT."
        )

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
                        metrics_url, timeout=aiohttp.ClientTimeout(total=2)
                    ) as response:
                        if response.status != 200:
                            continue

                        text = await response.text()

                        # Look for the tunnel URL in metrics
                        # Cloudflared exposes this in the userHostname metric
                        match = re.search(r'userHostname="([^"]+)"', text)
                        if match:
                            hostname = match.group(1)
                            # Remove https:// or wss:// if present
                            hostname = hostname.replace("https://", "").replace(
                                "wss://", ""
                            )
                            return "https://" + hostname, "wss://" + hostname

                        # Alternative: Look for trycloudflare.com domain
                        match = re.search(r"([a-z0-9-]+\.trycloudflare\.com)", text)
                        if match:
                            hostname = match.group(1)
                            hostname = hostname.replace("https://", "").replace(
                                "wss://", ""
                            )
                            return f"https://{hostname}", f"wss://{hostname}"
                except (asyncio.TimeoutError, aiohttp.ClientError):
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error querying {metrics_url}: {e}")
                    continue
        
        logger.warning("Could not find tunnel URL in cloudflared metrics on any expected endpoint")
        return None
