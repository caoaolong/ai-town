"""Dev 路由 - 与 v1 相同的接口，但直接返回 JSON 字符串"""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.routers.structed_schema import AITodoListResponse
from app.services.player_service import player_service
from app.services.prompt_service import prompt_service
from app.services.ws_manager import set_websocket, send_message

logger = logging.getLogger(__name__)

router = APIRouter()


# ── player ──────────────────────────────────────────────────────────

class TodoListRequest(BaseModel):
    player_id: str
    day: int


@router.post(
    "/player/todo_list",
    tags=["dev", "player"],
    summary="[DEV] 获取玩家待办事项列表（原始 JSON）",
)
async def player_todolist(request: TodoListRequest):
    player = player_service.get_player(request.player_id)
    if player is None:
        return {"error": "player not found"}
    response = await player(
        prompt_service.player_todolist_prompt(request.day),
        structured_model=AITodoListResponse,
    )
    return {
        "player_id": request.player_id,
        "data": response.metadata,
    }


# ── prompt ──────────────────────────────────────────────────────────

@router.get(
    "/prompt/player_system_prompt",
    tags=["dev", "prompt"],
    summary="[DEV] 获取玩家的系统提示词（原始 JSON）",
)
def get_prompt(intro: str):
    return {"result": prompt_service.player_system_prompt(intro)}


# ── websocket ───────────────────────────────────────────────────────

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 主入口（单客户端）"""
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
