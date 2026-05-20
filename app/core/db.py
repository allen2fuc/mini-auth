from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import settings

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .config import settings

engine = create_async_engine(
    settings.DB_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncSession:
    """FastAPI 依赖: yield 一个 AsyncSession"""
    async with AsyncSessionLocal() as session:
        yield session