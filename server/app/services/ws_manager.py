"""WebSocket 连接管理器（单客户端版本）
"""
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# 当前唯一的 WebSocket 连接
_current_ws: WebSocket | None = None


def set_websocket(websocket: WebSocket | None) -> None:
    """设置当前唯一的 WebSocket 连接"""
    global _current_ws
    _current_ws = websocket
    if websocket:
        logger.info("WebSocket 客户端已设置")
    else:
        logger.info("WebSocket 客户端已清除")


async def send_message(message: dict[str, Any]) -> None:
    """向唯一的客户端发送消息"""
    if _current_ws is None:
        logger.warning("没有可用的 WebSocket 连接，消息未发送")
        return
    try:
        await _current_ws.send_json(message)
    except Exception:
        logger.exception("发送 WebSocket 消息失败")
        raise
