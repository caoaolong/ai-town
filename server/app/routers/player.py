"""玩家路由 - 处理玩家相关的 HTTP 请求"""
from fastapi import APIRouter
from pydantic import BaseModel
from agentscope.message import Msg
from app.routers.structed_schema import AITodoListResponse
from app.services.player_service import player_service

router = APIRouter()

class TodoListRequest(BaseModel):
    player_id: str
    day: int

class TodoListResponse(BaseModel):
    player_id: str
    data: AITodoListResponse


def player_todolist_prompt(request: TodoListRequest) -> Msg:
    return Msg(
        role="system", 
        name="系统", 
        content=f"今天是第{request.day}天，请制定你今天的计划表")

@router.post(
    "/player/todo_list",
    tags=["player"],
    response_model=TodoListResponse,
    summary="获取玩家待办事项列表"
)
async def player_todolist(request: TodoListRequest) -> TodoListResponse:
    player = player_service.get_player(request.player_id)
    if player is None:
        return None
    response = await player(player_todolist_prompt(request), structured_model=AITodoListResponse)
    return TodoListResponse(
        player_id=request.player_id,
        data=response.metadata
    )
    