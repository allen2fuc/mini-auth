"""Pydantic schemas - 接口入参校验"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=4, max_length=128)
    email: Optional[str] = Field(default=None, max_length=128)
    is_admin: bool = False
    is_active: bool = True

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_to_none(cls, v: object) -> object:
        return None if v == "" else v


class UserUpdate(BaseModel):
    email: Optional[str] = Field(default=None, max_length=128)
    password: Optional[str] = Field(default=None, min_length=4, max_length=128)
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None

    @field_validator("email", "password", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="用户 ID")
    username: str = Field(max_length=64, description="用户名")
    email: Optional[str] = Field(default=None, max_length=128, description="邮箱")
    is_admin: bool = Field(description="是否为管理员")
    is_active: bool = Field(description="是否启用")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class UserUpdateResponse(BaseModel):
    user: UserRead
    reauth_required: bool = Field(
        default=False,
        description="当前操作者需重新登录（修改了自身的密码/权限/启用状态）",
    )