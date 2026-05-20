"""FastAPI 入口"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.lifespan import lifespan

from app.core.logger import setup_logging
from app.core.middlewares import register_middlewares
from app.modules.admin.api import router as admin_router
from app.modules.auth.api import router as auth_router

docs = {}
if not settings.ENABLE_DOCS:
    docs = {
    "docs_url": None,
    "redoc_url": None,
    "openapi_url": None,
}

setup_logging()
app = FastAPI(title="Mini Auth", description="Mini Auth", lifespan=lifespan, **docs)

# 静态资源
app.mount("/static", StaticFiles(directory="static"), name="static")

register_middlewares(app)

# 业务路由
app.include_router(auth_router, tags=["auth"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])


@app.get("/")
async def root():
    return RedirectResponse(url="/login")


@app.get("/health")
async def health():
    return {"status": "ok"}