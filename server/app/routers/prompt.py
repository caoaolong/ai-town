"""提示词路由 - 处理提示词相关的 HTTP 请求"""
from app.services.prompt_service import prompt_service
from fastapi import APIRouter, Depends
from app.deps import get_mode

router = APIRouter()

@router.get(
        "/prompt/player_system_prompt",
        tags=["prompt"],
        summary="获取玩家的系统提示词"
)
def get_prompt(intro: str, mode: str = Depends(get_mode)) -> str:
    return prompt_service.player_system_prompt(intro)