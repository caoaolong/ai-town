"""公共依赖项"""

from fastapi import Header
from typing import Optional


async def get_mode(x_mode: Optional[str] = Header(None, alias="X-Mode")) -> str:
    """
    从请求头获取 mode 参数

    Header: X-Mode: simple | detailed | ...
    """
    return x_mode or "default"
