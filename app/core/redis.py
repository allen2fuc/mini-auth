"""Redis 异步客户端 (单例)"""
import logging
from typing import Optional

import redis.asyncio as aioredis

from .config import settings

logger = logging.getLogger(__name__)

_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await _client.ping()
        logger.info("redis connected: %s", settings.REDIS_URL)
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None