"""Supabase 客户端工具"""

from supabase import create_client, Client
from app.config import Config

# 全局 Supabase 客户端实例
_supabase_client: Client | None = None


def get_supabase() -> Client:
    """获取或初始化 Supabase 客户端（单例模式）

    Returns:
        Client: Supabase 客户端实例

    Raises:
        RuntimeError: 当 Supabase 配置未设置时
    """
    global _supabase_client

    if _supabase_client is None:
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            raise RuntimeError(
                "Supabase 配置缺失，请在 .env 中设置 SUPABASE_URL 和 SUPABASE_KEY"
            )
        _supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    return _supabase_client


def reset_supabase() -> None:
    """重置 Supabase 客户端（主要用于测试）"""
    global _supabase_client
    _supabase_client = None
