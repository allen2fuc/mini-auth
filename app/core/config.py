"""统一配置 - 全部走环境变量,容器友好"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 经过 Traefik 暴露的公网登录页地址 (verify 重定向时拼接)
    AUTH_PUBLIC_URL: str = "http://auth.localhost"  # 公网登录页地址

    # 存储
    DB_URL: str = "sqlite+aiosqlite:///auth.db"  # 数据库地址

    REDIS_URL: str = "redis://localhost:6379/0"  # Redis 地址

    # Cookie
    COOKIE_NAME: str = "mini_auth_session"     # 会话名称
    COOKIE_DOMAIN: str | None = None           # 域名
    COOKIE_SECURE: bool = False                # 是否使用 HTTPS
    COOKIE_MAX_AGE: int = 3600 * 8             # 会话有效期（秒，默认 8 小时）

    # Session
    SESSION_TTL: int = 3600 * 8                # 会话有效期（秒，默认 8 小时）
    REMEMBER_ME_MAX_AGE: int = 3600 * 24 * 30  # 记住我时长（秒，默认 30 天）

    # 登录防护
    LOGIN_RATE_LIMIT: int = 10         # 每窗口最大请求数
    LOGIN_RATE_WINDOW: int = 60        # 频率限制窗口（秒）
    LOGIN_FAIL_CAPTCHA_AFTER: int = 3  # 几次失败后出验证码
    LOGIN_FAIL_WINDOW: int = 900       # 失败计数窗口（秒）
    CAPTCHA_TTL: int = 300             # 验证码有效期（秒）

    # 日志
    LOG_DIR: Path = Path("logs")           # 日志目录
    LOG_FILE_NAME: str = "app.log"         # 日志文件名
    LOG_LEVEL: str = "INFO"                # 日志级别
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 日志文件最大大小（字节）
    LOG_BACKUP_COUNT: int = 10             # 日志文件备份数量


settings = Settings()