from fastapi import APIRouter
from pydantic import BaseModel
from agentscope.message import Msg
from agentscope.pipeline import MsgHub

router = APIRouter()


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    user_id: str | None = None


class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str
    success: bool = True


@router.post("/chat", tags=["chat"], response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(reply=f"Echo: {request.message}")
