"""PromptService - 管理提示词"""

from agentscope.message import Msg
import logging
from app.services.data_service import data_service

logger = logging.getLogger(__name__)


class PromptService:
    def player_system_prompt(self, intro: str) -> str:
        return f"""{intro}
---
以下是小镇的基本信息
```
{data_service.get_data_by_name("manual")}
```
---
以下是你的固有能力
```
{data_service.get_data_by_name("skill")}
```"""
    
    def player_todolist_prompt(self, day: int) -> Msg:
        return Msg(
        role="system", 
        name="系统", 
        content=f"今天是第{day}天，请制定你今天的计划表")

prompt_service = PromptService()