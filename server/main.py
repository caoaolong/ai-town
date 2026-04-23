from contextlib import asynccontextmanager
import asyncio
import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.player_service import player_service
import agentscope
from app.middleware.request_audit import RequestAuditMiddleware
from app.routers import admin, chat, health, player

logger = logging.getLogger(__name__)


async def _check_agentscope_ready(
    studio_url: str, timeout: float = 5.0, max_retries: int = 3
) -> bool:
    """
    检查 AgentScope Studio 是否已启动且可用
    
    Args:
        studio_url: AgentScope Studio URL（如 http://localhost:3000）
        timeout: 单次连接超时时间（秒）
        max_retries: 最大重试次数
    
    Returns:
        True 如果 AgentScope Studio 可用，False 否则
    """
    import aiohttp
    
    if not studio_url:
        logger.warning("未设置 AGENTSCOPE_STUDIO_URL，跳过 AgentScope 状态检查")
        return False
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(studio_url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                    if resp.status == 200:
                        logger.info(f"AgentScope Studio 已启动，URL: {studio_url}")
                        return True
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
            if attempt < max_retries - 1:
                logger.debug(f"AgentScope Studio 不可达（第 {attempt + 1} 次尝试），{max_retries - attempt - 1} 秒后重试...")
                await asyncio.sleep(2)
            else:
                logger.warning(f"AgentScope Studio 无法连接（已重试 {max_retries} 次），错误: {e}")
    
    return False


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _studio_url = (os.getenv("AGENTSCOPE_STUDIO_URL") or "").strip()
    _project = (os.getenv("AGENTSCOPE_PROJECT") or "").strip()
    _init_agentscope = os.getenv("INIT_AGENTSCOPE", "1").strip().lower() in ("1", "true", "yes")
    
    # 仅当显式要求时才初始化 AgentScope
    if _init_agentscope:
        agentscope_ready = await _check_agentscope_ready(_studio_url, timeout=5.0, max_retries=3)
        
        if agentscope_ready:
            try:
                agentscope.init(project=_project, studio_url=_studio_url)
                logger.info("AgentScope 已初始化")
            except Exception as e:
                logger.error(f"AgentScope 初始化失败: {e}")
        else:
            logger.warning("AgentScope Studio 未启动，跳过 agentscope.init() 初始化")
    else:
        logger.info("已禁用 AgentScope 初始化（INIT_AGENTSCOPE=0）")
    
    _players_path = Path(__file__).resolve().parent / "data" / "players.json"
    with open(_players_path, "r", encoding="utf-8") as players_file:
        players = json.load(players_file)
        for player_data in players:
            sys_prompt = player_data.get("sys_prompt") or player_data.get(
                "system_prompt", ""
            )
            player_service.create_player(
                player_id=player_data["id"],
                name=player_data["name"],
                sys_prompt=sys_prompt,
            )
    yield


app = FastAPI(
    title="AI Town Server",
    description="AI Town 游戏后端服务",
    version="0.1.0",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestAuditMiddleware)

# 注册路由
app.include_router(admin.router)
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(player.router)


@app.get("/")
async def root():
    return {"message": "Welcome to AI Town Server", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
