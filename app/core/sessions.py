"""Session: session_id -> 用户快照,存 Redis,带 TTL"""
import json
import logging
import secrets
from typing import Optional

from .config import settings
from .redis import get_redis

logger = logging.getLogger(__name__)

KEY_PREFIX = "miniauth:session:"


def _key(sid: str) -> str:
    return f"{KEY_PREFIX}{sid}"


async def create_session(user: dict, ttl: int | None = None) -> str:
    r = await get_redis()
    sid = secrets.token_urlsafe(32)
    payload = json.dumps(
        {
            "id": user["id"],
            "username": user["username"],
            "email": user.get("email"),
            "is_admin": user.get("is_admin", False),
        }
    )
    await r.set(_key(sid), payload, ex=ttl if ttl is not None else settings.SESSION_TTL)
    return sid


async def get_session(sid: Optional[str]) -> Optional[dict]:
    if not sid:
        return None
    r = await get_redis()
    raw = await r.get(_key(sid))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def delete_session(sid: Optional[str]) -> None:
    if not sid:
        return
    r = await get_redis()
    await r.delete(_key(sid))


async def delete_user_sessions(user_id: int) -> int:
    """撤销某用户所有 session - 改密码/禁用/删除时调用"""
    r = await get_redis()
    deleted = 0
    async for key in r.scan_iter(match=f"{KEY_PREFIX}*"):
        raw = await r.get(key)
        if not raw:
            continue
        try:
            data = json.loads(raw)
            if data.get("id") == user_id:
                await r.delete(key)
                deleted += 1
        except json.JSONDecodeError:
            continue
    if deleted:
        logger.info("invalidated %s session(s) for user_id=%s", deleted, user_id)
    return deleted