"""PromptService - 管理提示词"""

import json
import logging
from pathlib import Path
from typing import Any
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

prompt_service = PromptService()