"""认证路由: /verify  /login  /logout"""
import logging
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import captcha, login_guard, sessions
from app.core.config import settings
from app.core.db import get_session
from app.core.deps import client_ip
from app.core.templates import templates
from app.modules.user import curd as user_crud
from app.modules.user.schemas import UserRead

router = APIRouter()
logger = logging.getLogger(__name__)

_ERROR_MESSAGES = {
    "invalid": "用户名或密码错误",
    "captcha": "验证码错误或已过期",
    "rate_limited": "登录尝试过于频繁,请稍后再试",
}


def _build_original_url(request: Request) -> str:
    h = request.headers
    proto = h.get("x-forwarded-proto", "http")
    host = h.get("x-forwarded-host", "localhost")
    uri = h.get("x-forwarded-uri", "/")
    return f"{proto}://{host}{uri}"


def _login_redirect(rd: str, error: str | None = None) -> RedirectResponse:
    params: dict[str, str] = {"rd": rd}
    if error:
        params["error"] = error
    return RedirectResponse(
        url=f"/login?{urlencode(params)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


async def _login_context(request: Request, rd: str, error: str | None) -> dict:
    ip = client_ip(request)
    need_captcha = await login_guard.captcha_required(ip)
    captcha_id = None
    if need_captcha:
        captcha_id, _ = await captcha.create()
    return {
        "rd": rd,
        "captcha_required": need_captcha,
        "captcha_id": captcha_id,
        "error": _ERROR_MESSAGES.get(error) if error else None,
        "fail_count": await login_guard.get_fail_count(ip),
    }


@router.get("/verify")
async def verify(
    request: Request,
    session_id: Optional[str] = Cookie(default=None, alias=settings.COOKIE_NAME),
):
    """Traefik ForwardAuth 校验入口"""
    user = await sessions.get_session(session_id)
    if not user:
        original = _build_original_url(request)
        login_url = (
            f"{settings.AUTH_PUBLIC_URL}/login?{urlencode({'rd': original})}"
        )
        return RedirectResponse(url=login_url, status_code=status.HTTP_302_FOUND)

    resp = Response(status_code=status.HTTP_200_OK)
    resp.headers["X-Forwarded-User"] = user["username"]
    resp.headers["X-Forwarded-Email"] = user.get("email") or ""
    resp.headers["X-Forwarded-Groups"] = "admin" if user.get("is_admin") else "user"
    return resp


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    rd: str = "/",
    error: str | None = None,
):
    sid = request.cookies.get(settings.COOKIE_NAME)
    if sid and await sessions.get_session(sid):
        return RedirectResponse(url=rd, status_code=status.HTTP_302_FOUND)
    ctx = await _login_context(request, rd, error)
    return templates.TemplateResponse(request, "login.html", ctx)


@router.get("/login/captcha")
async def captcha_image(cid: str):
    code = await captcha.peek(cid)
    if not code:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    svg = captcha.render_svg(code)
    return Response(content=svg, media_type="image/svg+xml")


@router.post("/login/captcha/refresh")
async def captcha_refresh(request: Request):
    ip = client_ip(request)
    if not await login_guard.captcha_required(ip):
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    captcha_id, _ = await captcha.create()
    return {"id": captcha_id, "url": f"/login/captcha?cid={captcha_id}"}


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    rd: str = Form("/"),
    remember: str | None = Form(None),
    captcha_id: str | None = Form(None),
    captcha_code: str | None = Form(None),
    db: AsyncSession = Depends(get_session),
):
    ip = client_ip(request)

    if await login_guard.is_rate_limited(ip):
        logger.warning("LOGIN_RATE_LIMIT ip=%s user=%s", ip, username)
        return _login_redirect(rd, "rate_limited")

    if await login_guard.captcha_required(ip):
        if not await captcha.verify(captcha_id, captcha_code):
            await login_guard.record_failure(ip)
            logger.warning("LOGIN_CAPTCHA_FAIL user=%s ip=%s", username, ip)
            return _login_redirect(rd, "captcha")

    user = await user_crud.authenticate(db, username, password)
    if not user:
        fail_count = await login_guard.record_failure(ip)
        logger.warning(
            "LOGIN_FAIL user=%s ip=%s fails=%s", username, ip, fail_count
        )
        return _login_redirect(rd, "invalid")

    await login_guard.clear_failures(ip)

    remember_me = remember == "on"
    max_age = settings.REMEMBER_ME_MAX_AGE if remember_me else settings.COOKIE_MAX_AGE
    session_ttl = max_age

    sid = await sessions.create_session(user.model_dump(), ttl=session_ttl)
    logger.info(
        "LOGIN_OK user=%s admin=%s ip=%s rd=%s remember=%s",
        user.username, user.is_admin, ip, rd, remember_me,
    )

    resp = RedirectResponse(url=rd, status_code=status.HTTP_303_SEE_OTHER)
    resp.set_cookie(
        key=settings.COOKIE_NAME,
        value=sid,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        domain=settings.COOKIE_DOMAIN,
        max_age=max_age,
        path="/",
    )
    return resp


@router.get("/logout")
async def logout(
    request: Request,
    session_id: Optional[str] = Cookie(default=None, alias=settings.COOKIE_NAME),
):
    if session_id:
        user = await sessions.get_session(session_id)
        await sessions.delete_session(session_id)
        if user:
            logger.info("LOGOUT user=%s ip=%s", user["username"], client_ip(request))

    resp = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    resp.delete_cookie(
        settings.COOKIE_NAME, domain=settings.COOKIE_DOMAIN, path="/"
    )
    return resp
