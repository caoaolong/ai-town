"""WebSocket 路由 - 处理客户端长连接与消息推送"""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 主入口

    客户端连接后可通过发送 JSON 消息进行交互：
    - { "type": "bind", "player_id": "xxx" }   → 绑定玩家身份
    - { "type": "ping" }                       → 心跳保活
    - { "type": "chat", "payload": {...} }     → 聊天消息（示例）
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await ws_manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON"}, websocket
                )
                continue

            msg_type = data.get("type")

            if msg_type == "bind":
                player_id = data.get("player_id")
                if player_id:
                    ws_manager.bind_player(player_id, websocket)
                    await ws_manager.send_personal_message(
                        {"type": "bound", "player_id": player_id}, websocket
                    )
                else:
                    await ws_manager.send_personal_message(
                        {"type": "error", "message": "Missing player_id"}, websocket
                    )

            elif msg_type == "ping":
                await ws_manager.send_personal_message(
                    {"type": "pong"}, websocket
                )

            elif msg_type == "chat":
                # 示例：收到聊天消息后广播给所有人
                payload = data.get("payload", {})
                await ws_manager.broadcast(
                    {
                        "type": "chat_broadcast",
                        "sender": payload.get("sender", "anonymous"),
                        "message": payload.get("message", ""),
                    }
                )

            else:
                await ws_manager.send_personal_message(
                    {"type": "error", "message": f"Unknown type: {msg_type}"}, websocket
                )

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.exception("WebSocket 处理异常")
        ws_manager.disconnect(websocket)
