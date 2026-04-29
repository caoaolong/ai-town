"""玩家路由 - 处理玩家相关的 HTTP 请求"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.player_service import player_service

router = APIRouter()


class CreatePlayerRequest(BaseModel):
    """创建玩家请求"""
    name: str
    sys_prompt: str


class PlayerInfo(BaseModel):
    """玩家信息响应"""
    id: str
    name: str
    skills_count: int
    skills: list[str]


@router.get(
    "/players",
    tags=["player"],
    response_model=list[PlayerInfo],
    summary="获取全部角色列表",
)
async def list_players() -> list[PlayerInfo]:
    """返回当前已加载的所有玩家（含启动时从 data/players.json 创建的角色）。"""
    players = list(player_service.get_all_players().values())
    players.sort(key=lambda p: p.player_id)
    return [PlayerInfo(**p.get_info()) for p in players]


class ChatRequest(BaseModel):
    """玩家聊天请求"""
    message: str


class ChatResponse(BaseModel):
    """玩家聊天响应"""

    reply: str


@router.post(
    "/player/{player_id}",
    tags=["player"],
    response_model=PlayerInfo,
    summary="创建 AI 玩家"
)
async def create_player(player_id: str, request: CreatePlayerRequest) -> PlayerInfo:
    """
    创建一个新的 AI 玩家
    
    使用 agentscope 的 ReActAgent 创建具备 Skills 功能的 AI 玩家
    """
    player = player_service.create_player(player_id=player_id, name=request.name, sys_prompt=request.sys_prompt)
    
    info = player.get_info()
    return PlayerInfo(**info)


@router.get(
    "/player/{player_id}",
    tags=["player"],
    response_model=PlayerInfo,
    summary="获取玩家信息"
)
async def get_player(player_id: str) -> PlayerInfo:
    """
    获取玩家的基本信息
    
    包括玩家 ID、名称、技能列表等
    """
    player = player_service.get_player(player_id)
    
    if player is None:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    
    info = player.get_info()
    return PlayerInfo(**info)


@router.post(
    "/player/{player_id}/chat",
    tags=["player"],
    response_model=ChatResponse,
    summary="与 AI 玩家对话"
)
async def player_chat(player_id: str, request: ChatRequest) -> ChatResponse:
    # TODO: 待完善
    return ChatResponse(reply="")


class PlayerState(BaseModel):
    """玩家状态提交模型"""
    player: str
    event_type: str
    data: dict

@router.post("/state", tags=["player"], summary="玩家提交当前状态")
async def player_submit_state(state: PlayerState):
    print(state)
    return {"message": f"Received state for player {state.player} with event {state.event_type}"}