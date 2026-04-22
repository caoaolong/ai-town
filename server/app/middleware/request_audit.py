"""记录请求日志；在暂停模式下对非白名单路径返回 503"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app import admin_runtime


def _skip_request_audit(method: str, path: str) -> bool:
    """控制台轮询接口，避免日志刷屏"""
    if method != "GET":
        return False
    return path.startswith("/admin/logs") or path.startswith("/admin/status")


class RequestAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        start = time.perf_counter()
        if admin_runtime.is_paused() and not admin_runtime.should_allow_when_paused(path):
            duration_ms = (time.perf_counter() - start) * 1000.0
            if not _skip_request_audit(request.method, path):
                admin_runtime.append_request_log(
                    {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "method": request.method,
                        "path": path,
                        "status": 503,
                        "ms": round(duration_ms, 2),
                        "client": request.client.host if request.client else "",
                        "error": False,
                        "paused_block": True,
                    }
                )
            return JSONResponse(
                status_code=503,
                content={"detail": "服务已暂停，仅管理接口与文档可用"},
            )

        response: Response
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000.0
            if not _skip_request_audit(request.method, path):
                admin_runtime.append_request_log(
                    {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "method": request.method,
                        "path": path,
                        "status": 500,
                        "ms": round(duration_ms, 2),
                        "client": request.client.host if request.client else "",
                        "error": True,
                    }
                )
            raise

        duration_ms = (time.perf_counter() - start) * 1000.0
        if not _skip_request_audit(request.method, path):
            admin_runtime.append_request_log(
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "method": request.method,
                    "path": path,
                    "status": response.status_code,
                    "ms": round(duration_ms, 2),
                    "client": request.client.host if request.client else "",
                    "error": False,
                }
            )
        return response
