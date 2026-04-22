from contextlib import asynccontextmanager
import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.player_service import player_service
import agentscope
from app.middleware.request_audit import RequestAuditMiddleware
from app.routers import admin, chat, health, player


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _studio_url = (os.getenv("AGENTSCOPE_STUDIO_URL") or "").strip() or None
    _project = (os.getenv("AGENTSCOPE_PROJECT") or "").strip() or None
    agentscope.init(project=_project, studio_url=_studio_url)
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
