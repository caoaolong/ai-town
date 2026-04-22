"""管理用 HTTP 接口：服务状态、暂停/恢复、请求日志"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app import admin_runtime

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/status")
async def admin_status():
    """当前暂停状态与运行时长"""
    return {
        "paused": admin_runtime.is_paused(),
        "uptime_seconds": round(admin_runtime.uptime_seconds(), 2),
    }


@router.post("/pause")
async def admin_pause():
    """暂停业务 API（白名单路径仍可用）"""
    admin_runtime.set_paused(True)
    return {"paused": True, "message": "已暂停"}


@router.post("/resume")
async def admin_resume():
    """恢复业务 API"""
    admin_runtime.set_paused(False)
    return {"paused": False, "message": "已恢复"}


@router.get("/logs")
async def admin_logs(limit: int = Query(default=200, ge=1, le=500)):
    """最近请求日志（新到旧）"""
    return {"items": admin_runtime.get_request_logs(limit)}
