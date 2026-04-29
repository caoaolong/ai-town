import sys
from pathlib import Path

# 将项目根目录加入 sys.path，支持从任意位置直接运行此脚本
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from app.db.db_scene_object_manual import query_scene_object

if __name__ == "__main__":
    print(query_scene_object("小绿树"))
