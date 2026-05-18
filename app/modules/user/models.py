"""User 模型 - SQLModel"""
from datetime import datetime
from typing import Optional, Text

from sqlmodel import Boolean, Column, DateTime, Field, Integer, SQLModel, String


class User(SQLModel, table=True):
    __tablename__ = "users"

    __table_args__ = {
        "comment": "用户表",
    }

    id: Optional[int] = Field(sa_column=Column(Integer, primary_key=True, autoincrement=True, nullable=False, comment="用户ID"))
    username: str = Field(sa_column=Column(String(64), index=True, unique=True, nullable=False, comment="用户名"))
    email: Optional[str] = Field(sa_column=Column(String(128), default=None, nullable=True, comment="邮箱"))
    password_hash: str = Field(sa_column=Column(String(128), nullable=False, comment="密码哈希"))
    is_admin: bool = Field(sa_column=Column(Boolean, default=False, nullable=False, comment="是否为管理员"))
    is_active: bool = Field(sa_column=Column(Boolean, default=True, nullable=False, comment="是否启用"))
    created_at: datetime = Field(sa_column=Column(DateTime, server_default=Text("CURRENT_TIMESTAMP"), nullable=False, comment="创建时间"))
    updated_at: datetime = Field(sa_column=Column(DateTime, server_default=Text("CURRENT_TIMESTAMP"), nullable=False, onupdate=Text("CURRENT_TIMESTAMP"), comment="更新时间"))