"""登录防护: 频率限制与失败计数"""
from .config import settings
from .redis import get_redis

_FAIL_KEY = "miniauth:login:fails:{ip}"
_RATE_KEY = "miniauth:login:rate:{ip}"


async def is_rate_limited(ip: str) -> bool:
    r = await get_redis()
    key = _RATE_KEY.format(ip=ip)
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, settings.LOGIN_RATE_WINDOW)
    return count > settings.LOGIN_RATE_LIMIT


async def get_fail_count(ip: str) -> int:
    r = await get_redis()
    raw = await r.get(_FAIL_KEY.format(ip=ip))
    return int(raw) if raw else 0


async def captcha_required(ip: str) -> bool:
    return await get_fail_count(ip) >= settings.LOGIN_FAIL_CAPTCHA_AFTER


async def record_failure(ip: str) -> int:
    r = await get_redis()
    key = _FAIL_KEY.format(ip=ip)
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, settings.LOGIN_FAIL_WINDOW)
    return count


async def clear_failures(ip: str) -> None:
    r = await get_redis()
    await r.delete(_FAIL_KEY.format(ip=ip))
