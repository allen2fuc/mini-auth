"""FastAPI 公共依赖"""
from typing import Optional

from fastapi import Cookie, HTTPException, Request, status

from .config import settings
from . import sessions


async def current_user(
    session_id: Optional[str] = Cookie(default=None, alias=settings.COOKIE_NAME),
) -> Optional[dict]:
    """当前 session 对应的用户快照,无则 None"""
    return await sessions.get_session(session_id)


async def require_admin(request: Request) -> dict:
    """要求管理员,否则 303 跳转登录页 (带 rd 回跳)"""
    sid = request.cookies.get(settings.COOKIE_NAME)
    user = await sessions.get_session(sid) if sid else None
    if not user or not user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login?rd=/admin"},
        )
    return user


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "-"