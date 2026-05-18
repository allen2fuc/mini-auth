import time
from typing import Callable
from fastapi import FastAPI, Request

from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import logging

logger = logging.getLogger(__name__)

def register_middlewares(app: FastAPI):

    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable):
        start_time = time.time()
        logger.info(f"Request: {request.method} {request.url} {request.client.host}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code} {time.time() - start_time}s")
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])