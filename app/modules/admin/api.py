"""管理后台: /admin (页面) + /admin/api/users (CRUD)"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import sessions
from app.core.db import get_session
from app.core.deps import require_admin
from app.core.templates import templates
from app.modules.user import curd as user_crud
from app.modules.user.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter()
logger = logging.getLogger(__name__)


# ============ 页面 ============
@router.get("/", response_class=HTMLResponse)
async def admin_page(request: Request, admin: dict = Depends(require_admin)):
    return templates.TemplateResponse(
        request, "admin.html", {"current_user": admin}
    )


# ============ JSON API ============
@router.get("/api/users", response_model=dict[str, list[UserRead]])
async def api_list(
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    users = await user_crud.list_all(db)
    # return {"users": [u.to_public() for u in users]}
    return {"users": users}


@router.post("/api/users", status_code=status.HTTP_201_CREATED, response_model=UserRead)
async def api_create(
    payload: UserCreate,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    if await user_crud.get_by_username(db, payload.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username_exists")
    user = await user_crud.create(db, payload)
    logger.info(
        "ADMIN_CREATE_USER by=%s target=%s admin=%s",
        admin["username"], user.username, user.is_admin,
    )
    return user


@router.patch("/api/users/{user_id}", response_model=UserRead)
async def api_update(
    user_id: int,
    payload: UserUpdate,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    target = await user_crud.get_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    # 防止把最后一个活跃管理员降级/停用
    if target.is_admin and target.is_active:
        will_lose_admin_status = (
            payload.is_admin is False or payload.is_active is False
        )
        if will_lose_admin_status:
            others = await user_crud.count_active_admins(db, exclude_id=user_id)
            if others == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="last_admin")

    updated = await user_crud.update(db, target, payload)

    # 改了 admin/active/password 时撤销已有 session,立即生效
    if (
        payload.is_admin is not None
        or payload.is_active is not None
        or payload.password
    ):
        await sessions.delete_user_sessions(user_id)

    changed_fields = [
        k for k, v in payload.model_dump().items() if v is not None
    ]
    logger.info(
        "ADMIN_UPDATE_USER by=%s target=%s fields=%s",
        admin["username"], updated.username, changed_fields,
    )
    return updated


@router.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete(
    user_id: int,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_session),
):
    target = await user_crud.get_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if target.id == admin["id"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot_delete_self")
    if target.is_admin:
        others = await user_crud.count_active_admins(db, exclude_id=user_id)
        if others == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="last_admin")

    await user_crud.delete(db, target)
    await sessions.delete_user_sessions(user_id)
    logger.info(
        "ADMIN_DELETE_USER by=%s target=%s",
        admin["username"], target.username,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)