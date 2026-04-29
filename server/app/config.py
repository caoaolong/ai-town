import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用配置"""
    
    # LLM API 配置
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_API_BASE = os.getenv("LLM_API_BASE", None)
    
    # 服务配置
    HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    PORT = int(os.getenv("SERVER_PORT", "8000"))

    # Supabase 配置
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
