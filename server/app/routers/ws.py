"""WebSocket 路由 - 处理客户端长连接与消息推送"""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.ws_manager import set_websocket, send_message

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 主入口（单客户端）

    客户端连接后可通过发送 JSON 消息进行交互：
    - { "type": "ping" }                       → 心跳保活
    - { "type": "chat", "payload": {...} }     → 聊天消息（示例）
    """
    await websocket.accept()
    set_websocket(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await send_message({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = data.get("type")

            if msg_type == "ping":
                await send_message({"type": "pong"})

            elif msg_type == "chat":
                # 示例：收到聊天消息后转发
                payload = data.get("payload", {})
                await send_message(
                    {
                        "type": "chat_broadcast",
                        "sender": payload.get("sender", "anonymous"),
                        "message": payload.get("message", ""),
                    }
                )

            else:
                await send_message(
                    {"type": "error", "message": f"Unknown type: {msg_type}"}
                )

    except WebSocketDisconnect:
        set_websocket(None)
    except Exception:
        logger.exception("WebSocket 处理异常")
        set_websocket(None)
