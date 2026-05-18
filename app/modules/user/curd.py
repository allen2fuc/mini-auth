"""用户仓储 - 把 ORM 操作集中到这里,路由只跟它打交道"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.security import hash_password, verify_password
from .models import User
from .schemas import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


async def list_all(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).order_by(User.id))
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    return await session.get(User, user_id)


async def get_by_username(session: AsyncSession, username: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def authenticate(
    session: AsyncSession, username: str, password: str
) -> Optional[User]:
    """返回 User 或 None,只有启用且密码正确才认可"""
    user = await get_by_username(session, username)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def create(session: AsyncSession, payload: UserCreate) -> User:
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_admin=payload.is_admin,
        is_active=payload.is_active,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info("user created: id=%s username=%s admin=%s", user.id, user.username, user.is_admin)
    return user


async def update(
    session: AsyncSession, user: User, payload: UserUpdate
) -> User:
    changed = []
    if payload.email is not None:
        user.email = payload.email
        changed.append("email")
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
        changed.append("password")
    if payload.is_admin is not None:
        user.is_admin = payload.is_admin
        changed.append("is_admin")
    if payload.is_active is not None:
        user.is_active = payload.is_active
        changed.append("is_active")
    if changed:
        user.updated_at = datetime.now()
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("user updated: id=%s fields=%s", user.id, changed)
    return user


async def delete(session: AsyncSession, user: User) -> None:
    uid = user.id
    await session.delete(user)
    await session.commit()
    logger.info("user deleted: id=%s", uid)


async def count_active_admins(
    session: AsyncSession, exclude_id: Optional[int] = None
) -> int:
    """统计当前启用的管理员数量,可排除某 id"""
    stmt = select(func.count()).select_from(User).where(
        User.is_admin == True, User.is_active == True   # noqa: E712
    )
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    result = await session.execute(stmt)
    return int(result.scalar_one())


async def ensure_initial_admin(
    session: AsyncSession, username: str, password: str
) -> None:
    """启动时若无管理员则创建一个"""
    count = await count_active_admins(session)
    if count > 0:
        return
    logger.warning("no admin found, creating initial admin: %s", username)
    await create(
        session,
        UserCreate(
            username=username,
            password=password,
            is_admin=True,
            is_active=True,
        ),
    )