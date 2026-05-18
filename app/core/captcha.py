"""图形验证码 - 答案存 Redis"""
import random
import secrets
import string

from .config import settings
from .redis import get_redis

KEY_PREFIX = "miniauth:captcha:"
_CHARS = string.ascii_uppercase + string.digits


def _key(cid: str) -> str:
    return f"{KEY_PREFIX}{cid}"


def _random_code(length: int = 4) -> str:
    return "".join(random.choices(_CHARS, k=length))


def render_svg(code: str) -> str:
    """简单 SVG 验证码,无额外图片依赖"""
    w, h = 120, 40
    lines = []
    for _ in range(4):
        x1, y1 = random.randint(0, w), random.randint(0, h)
        x2, y2 = random.randint(0, w), random.randint(0, h)
        color = f"#{random.randint(0, 0xFFFFFF):06x}"
        lines.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1" opacity="0.5"/>'
        )
    chars = []
    for i, ch in enumerate(code):
        x = 18 + i * 24
        y = 26 + random.randint(-4, 4)
        rotate = random.randint(-18, 18)
        color = f"#{random.randint(0x333333, 0x666666):06x}"
        chars.append(
            f'<text x="{x}" y="{y}" fill="{color}" font-size="22" font-family="monospace" '
            f'font-weight="bold" transform="rotate({rotate} {x} {y})">{ch}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<rect width="100%" height="100%" fill="#f8fafc"/>'
        f'{"".join(lines)}{"".join(chars)}</svg>'
    )


async def create() -> tuple[str, str]:
    """返回 (captcha_id, code)"""
    cid = secrets.token_urlsafe(16)
    code = _random_code()
    r = await get_redis()
    await r.set(_key(cid), code.upper(), ex=settings.CAPTCHA_TTL)
    return cid, code


async def verify(cid: str | None, answer: str | None) -> bool:
    if not cid or not answer:
        return False
    r = await get_redis()
    expected = await r.get(_key(cid))
    await r.delete(_key(cid))
    if not expected:
        return False
    return expected == answer.strip().upper()


async def peek(cid: str) -> str | None:
    """仅读取,不删除 (渲染图片用)"""
    r = await get_redis()
    return await r.get(_key(cid))
