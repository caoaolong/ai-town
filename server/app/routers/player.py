"""玩家路由 - 处理玩家相关的 HTTP 请求"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from agentscope.message import Msg
from app.routers.structed_schema import AITodoListResponse
from app.services.player_service import player_service
from app.services.prompt_service import prompt_service
from app.deps import get_mode

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class TodoListRequest(BaseModel):
    player_id: str
    day: int


class TodoListResponse(BaseModel):
    player_id: str
    data: AITodoListResponse


@router.post(
    "/player/todo_list",
    tags=["player"],
    response_model=TodoListResponse,
    summary="获取玩家待办事项列表",
)
async def player_todolist(
    request: TodoListRequest, mode: str = Depends(get_mode)
) -> TodoListResponse:
    if mode == "dev":
        return TodoListResponse(
            player_id=request.player_id,
            data={
                "todo_list": [
                    {
                        "action_id": "work_to_chop",
                        "action_label": "在林场打工",
                        "action_description": "先去林场砍树赚钱，10金币/小时，干4小时能赚40金币！虽然可能有10%概率失误赔钱，但我红毛姐运气一向不错~",
                        "action_percent": 40,
                    },
                    {
                        "action_id": "chat_with_someone",
                        "action_label": "找人聊天",
                        "action_description": "午休时间找人聊聊，看看小镇上有没有什么有趣的人和事，顺便打听打听有没有发财的机会！",
                        "action_percent": 20,
                    },
                    {
                        "action_id": "work_to_feed",
                        "action_label": "在牧场打工",
                        "action_description": "下午去牧场干活，20金币/小时，比林场赚得多！虽然失误概率20%高了点，但我红毛姐机灵着呢，应该没问题~",
                        "action_percent": 30,
                    },
                    {
                        "action_id": "shopping",
                        "action_label": "在超市购物",
                        "action_description": "忙了一天去超市逛逛，买点好吃的犒劳自己！顺便看看超市有没有什么新鲜事~",
                        "action_percent": 10,
                    },
                ]
            },
        )

    player = player_service.get_player(request.player_id)
    if player is None:
        return None
    response = await player(
        prompt_service.player_todolist_prompt(request.day),
        structured_model=AITodoListResponse,
    )
    return TodoListResponse(player_id=request.player_id, data=response.metadata)
