"""WebSocket 连接管理器

提供广播、单播等消息推送能力，供其他 service 调用。
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """管理所有活跃的 WebSocket 连接"""

    def __init__(self):
        # 所有活跃连接
        self._active_connections: set[WebSocket] = set()
        # player_id -> WebSocket 的映射（用于定向推送）
        self._player_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """接受新连接并加入连接池"""
        await websocket.accept()
        self._active_connections.add(websocket)
        logger.info(f"WebSocket 客户端已连接，当前连接数: {len(self._active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """移除断开的连接"""
        self._active_connections.discard(websocket)
        # 清理 player_id 映射
        for pid, ws in list(self._player_connections.items()):
            if ws is websocket:
                del self._player_connections[pid]
                break
        logger.info(f"WebSocket 客户端已断开，当前连接数: {len(self._active_connections)}")

    def bind_player(self, player_id: str, websocket: WebSocket) -> None:
        """将 player_id 与当前连接绑定，支持定向推送"""
        self._player_connections[player_id] = websocket
        logger.info(f"Player {player_id} 已绑定 WebSocket")

    def unbind_player(self, player_id: str) -> None:
        """解绑 player_id"""
        self._player_connections.pop(player_id, None)

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """向指定连接发送消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"向单个客户端发送消息失败: {e}")

    async def send_to_player(self, player_id: str, message: dict[str, Any]) -> bool:
        """向指定 player_id 推送消息"""
        websocket = self._player_connections.get(player_id)
        if websocket is None:
            logger.debug(f"Player {player_id} 当前不在线，消息未送达")
            return False
        await self.send_personal_message(message, websocket)
        return True

    async def broadcast(self, message: dict[str, Any]) -> None:
        """向所有活跃连接广播消息"""
        if not self._active_connections:
            return

        # 并发发送，失败不阻断其他连接
        results = await asyncio.gather(
            *[self._safe_send(ws, message) for ws in self._active_connections],
            return_exceptions=True,
        )
        failed = sum(1 for r in results if isinstance(r, Exception))
        if failed:
            logger.warning(f"广播消息失败 {failed}/{len(results)} 个客户端")

    async def _safe_send(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """安全发送，捕获异常"""
        try:
            await websocket.send_json(message)
        except Exception:
            # 发送失败时标记为待清理
            self._active_connections.discard(websocket)
            raise


# 全局单例
ws_manager = ConnectionManager()
