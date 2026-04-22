"""HTTP 服务运行时状态：暂停开关、请求日志环形缓冲（供管理 API 与中间件使用）"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any

_lock = threading.RLock()
_paused: bool = False
_started_monotonic: float = time.perf_counter()
_logs: deque[dict[str, Any]] = deque(maxlen=500)

# 暂停业务 API 时仍允许访问的前缀（管理端、文档与健康探针）
_PAUSE_ALLOW_PREFIXES: tuple[str, ...] = (
    "/admin",
    "/docs",
    "/redoc",
    "/openapi.json",
)
_PAUSE_ALLOW_PATHS: frozenset[str] = frozenset({"/", "/health", "/ready"})


def uptime_seconds() -> float:
    with _lock:
        return time.perf_counter() - _started_monotonic


def is_paused() -> bool:
    with _lock:
        return _paused


def set_paused(value: bool) -> None:
    with _lock:
        global _paused
        _paused = value


def should_allow_when_paused(path: str) -> bool:
    if path in _PAUSE_ALLOW_PATHS:
        return True
    for prefix in _PAUSE_ALLOW_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def append_request_log(entry: dict[str, Any]) -> None:
    with _lock:
        _logs.appendleft(entry)


def get_request_logs(limit: int = 200) -> list[dict[str, Any]]:
    with _lock:
        cap = max(1, min(limit, 500))
        return list(_logs)[:cap]
