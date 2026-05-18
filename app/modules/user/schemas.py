"""Pydantic schemas - 接口入参校验"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=4, max_length=128)
    email: Optional[str] = Field(default=None, max_length=128)
    is_admin: bool = False
    is_active: bool = True


class UserUpdate(BaseModel):
    email: Optional[str] = Field(default=None, max_length=128)
    password: Optional[str] = Field(default=None, min_length=4, max_length=128)
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None

class UserRead(BaseModel):
    id: int = Field(description="用户 ID")
    username: str = Field(description="用户名")
    email: Optional[str] = Field(default=None, description="邮箱")
    is_admin: bool = Field(description="是否为管理员")
    is_active: bool = Field(description="是否启用")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")