from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap_agentscope import init_agentscope_studio
from app.bootstrap_players import load_players_at_startup
from app.middleware.request_audit import RequestAuditMiddleware
from app.routers import admin, chat, health, player


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 先于玩家加载：后续 create_player / ReActAgent 产生的 trace 可进入 Studio
    init_agentscope_studio()
    load_players_at_startup()
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
