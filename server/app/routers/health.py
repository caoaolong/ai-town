from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "message": "Service is running"}


@router.get("/ready", tags=["health"])
async def readiness_check():
    """就绪检查接口"""
    return {"ready": True}
