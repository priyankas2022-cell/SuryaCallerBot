"""Redis-based transfer event coordination service

Handles transfer event publishing, subscription, and context storage
"""

import asyncio
import time
from typing import Dict, Optional

import redis.asyncio as aioredis
from loguru import logger

from api.constants import REDIS_URL
from api.services.telephony.transfer_event_protocol import (
    TransferContext,
    TransferEvent,
    TransferEventType,
    TransferRedisChannels,
)


class CallTransferManager:
    """Manages call transfer events and context storage using Redis."""

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self._redis_client = redis_client
        self._pubsub_connections: Dict[str, aioredis.client.PubSub] = {}

    async def _get_redis(self) -> aioredis.Redis:
        """Get Redis client instance."""
        if not self._redis_client:
            self._redis_client = await aioredis.from_url(
                REDIS_URL, decode_responses=True
            )
        return self._redis_client

    async def store_transfer_context(
        self, context: TransferContext, ttl: int = 300
    ) -> None:
        """Store transfer context in Redis with TTL.

        Args:
            context: Transfer context data
            ttl: Time to live in seconds (default 5 minutes)
        """
        try:
            redis = await self._get_redis()
            key = TransferRedisChannels.transfer_context_key(context.transfer_id)
            await redis.setex(key, ttl, context.to_json())
            logger.debug(f"Stored transfer context for {context.transfer_id}")
        except Exception as e:
            logger.error(f"Failed to store transfer context: {e}")

    async def get_transfer_context(self, transfer_id: str) -> Optional[TransferContext]:
        """Retrieve transfer context from Redis.

        Args:
            transfer_id: Transfer identifier

        Returns:
            Transfer context if found, None otherwise
        """
        try:
            redis = await self._get_redis()
            key = TransferRedisChannels.transfer_context_key(transfer_id)
            data = await redis.get(key)
            if data:
                return TransferContext.from_json(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get transfer context: {e}")
            return None

    async def remove_transfer_context(self, transfer_id: str) -> None:
        """Remove transfer context from Redis.

        Args:
            transfer_id: Transfer identifier
        """
        try:
            redis = await self._get_redis()
            key = TransferRedisChannels.transfer_context_key(transfer_id)
            await redis.delete(key)
            logger.debug(f"Removed transfer context for {transfer_id}")
        except Exception as e:
            logger.error(f"Failed to remove transfer context: {e}")

    async def publish_transfer_event(self, event: TransferEvent) -> None:
        """Publish transfer event to Redis channel.

        Also durably stores the event for a short TTL so that
        wait_for_transfer_completion can pick it up even if it was published
        before the subscriber started listening (pub/sub messages are
        otherwise lost in that case).

        Args:
            event: Transfer event to publish
        """
        try:
            # Add timestamp if not present
            if event.timestamp is None:
                event.timestamp = time.time()

            redis = await self._get_redis()
            event_json = event.to_json()

            result_key = TransferRedisChannels.transfer_result_key(event.transfer_id)
            await redis.setex(result_key, 60, event_json)

            channel = TransferRedisChannels.transfer_events(event.transfer_id)
            await redis.publish(channel, event_json)
            logger.info(f"Published {event.type} event for {event.transfer_id}")
        except Exception as e:
            logger.error(f"Failed to publish transfer event: {e}")

    _TERMINAL_EVENT_TYPES = [
        TransferEventType.TRANSFER_ANSWERED,  # Call answered = transfer successful
        TransferEventType.TRANSFER_COMPLETED,
        TransferEventType.TRANSFER_FAILED,
        TransferEventType.TRANSFER_CANCELLED,
        TransferEventType.TRANSFER_TIMEOUT,
    ]

    async def _get_durable_terminal_result(
        self, transfer_id: str
    ) -> Optional[TransferEvent]:
        """Check the durably-stored result for an already-completed transfer.

        Providers that redirect a live call synchronously (e.g. Vobiz) can
        publish the completion event before we start listening for it, which
        would otherwise be silently lost (Redis pub/sub does not queue
        messages for late subscribers).
        """
        redis = await self._get_redis()
        result_key = TransferRedisChannels.transfer_result_key(transfer_id)
        data = await redis.get(result_key)
        if not data:
            return None
        try:
            event = TransferEvent.from_json(data)
            if event.type in self._TERMINAL_EVENT_TYPES:
                return event
        except Exception as e:
            logger.error(f"Failed to parse durable transfer result: {e}")
        return None

    async def wait_for_transfer_completion(
        self, transfer_id: str, timeout_seconds: float = 30.0
    ) -> Optional[TransferEvent]:
        """Wait for transfer completion event using Redis pub/sub.

        Args:
            transfer_id: Transfer identifier to wait for
            timeout_seconds: Maximum time to wait

        Returns:
            Transfer completion event if received, None on timeout
        """
        channel = TransferRedisChannels.transfer_events(transfer_id)
        redis = await self._get_redis()
        pubsub = redis.pubsub()

        try:
            # Fast path: the result may already be in before we even subscribe.
            early_result = await self._get_durable_terminal_result(transfer_id)
            if early_result:
                logger.info(f"Transfer result for {transfer_id} already available")
                return early_result

            await pubsub.subscribe(channel)
            logger.info(
                f"Waiting for transfer completion on {channel} (timeout: {timeout_seconds}s)"
            )

            # Close the narrow race between the check above and subscribe()
            # completing.
            post_subscribe_result = await self._get_durable_terminal_result(transfer_id)
            if post_subscribe_result:
                logger.info(f"Transfer result for {transfer_id} already available")
                return post_subscribe_result

            # Wait for completion event with timeout
            async def wait_for_message():
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            event = TransferEvent.from_json(message["data"])
                            logger.info(
                                f"Received {event.type} event for {transfer_id}"
                            )

                            # Check if this is a completion event
                            if event.type in self._TERMINAL_EVENT_TYPES:
                                return event
                        except Exception as e:
                            logger.error(f"Failed to parse transfer event: {e}")
                            continue
                return None

            # Wait with timeout
            result = await asyncio.wait_for(wait_for_message(), timeout=timeout_seconds)
            return result

        except asyncio.TimeoutError:
            logger.debug(f"Transfer completion wait timed out for {transfer_id}")
            return None
        except Exception as e:
            logger.error(f"Error waiting for transfer completion: {e}")
            return None
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub connection: {e}")

    async def cleanup(self):
        """Clean up Redis connections."""
        try:
            # Close pubsub connections
            for pubsub in self._pubsub_connections.values():
                try:
                    await pubsub.close()
                except:
                    pass
            self._pubsub_connections.clear()

            # Close main Redis connection
            if self._redis_client:
                await self._redis_client.close()
                self._redis_client = None
        except Exception as e:
            logger.error(f"Error during transfer coordinator cleanup: {e}")


# Global call transfer manager instance
_call_transfer_manager: Optional[CallTransferManager] = None


async def get_call_transfer_manager() -> CallTransferManager:
    """Get or create the global call transfer manager instance."""
    global _call_transfer_manager
    if not _call_transfer_manager:
        _call_transfer_manager = CallTransferManager()
    return _call_transfer_manager
