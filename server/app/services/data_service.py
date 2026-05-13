"""DataService - 将 data 目录下的 JSON 文件转换为 Markdown 表格字符串"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DataService:
    DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

    def get_data_by_name(self, name: str) -> Any:
        """根据文件名（不含 .json 后缀）读取对应的 JSON 文件"""
        file_path = self.DATA_DIR / f"{name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)


data_service = DataService()