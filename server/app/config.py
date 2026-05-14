import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 项目根目录 (server/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Config:
    """应用配置"""
    
    # LLM API 配置
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_API_BASE = os.getenv("LLM_API_BASE", None)
    
    # 服务配置
    HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    PORT = int(os.getenv("SERVER_PORT", "8000"))

