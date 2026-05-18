from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from app.core.redis import close_redis, get_redis

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时建立 Redis 连接,验证可达
    await get_redis()
    logger.info("mini-auth started")
    yield
    await close_redis()
    logger.info("mini-auth stopped")