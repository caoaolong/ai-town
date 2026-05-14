"""DataService - 将 data 目录下的 JSON 文件转换为 Markdown 表格字符串"""

import json
import logging
from typing import Any

from app.config import PROJECT_ROOT

logger = logging.getLogger(__name__)


class DataService:
    DATA_DIR = PROJECT_ROOT / "data"

    def get_data_by_name(self, name: str) -> Any:
        """根据文件名（不含 .json 后缀）读取对应的 JSON 文件"""
        file_path = self.DATA_DIR / f"{name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def find_object_by_action_id(self, action_id: str) -> dict[str, Any] | None:
        """根据 action_id 查找对应的对象（搜索 manual.json 和 skill.json）"""
        # manual.json: action_id 嵌套在 action_list 中
        manual = self.get_data_by_name("manual")
        for obj in manual:
            for action in obj.get("action_list", []):
                if action.get("action_id") == action_id:
                    return obj
        # skill.json: action_id 在顶层
        skills = self.get_data_by_name("skill")
        for skill in skills:
            if skill.get("action_id") == action_id:
                return skill
        return None


data_service = DataService()