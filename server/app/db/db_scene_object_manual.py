from app.db.supabase_client import get_supabase
from postgrest.types import JSON

def query_scene_object(name: str) -> JSON:
    """查询场景对象信息"""
    supabase = get_supabase()
    response = supabase.table("scene_object_manual").select("*").eq("name", name).limit(1).execute()
    return response.data[0]