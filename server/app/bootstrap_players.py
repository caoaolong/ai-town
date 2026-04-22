"""应用启动时从 data/players.json 加载并创建玩家"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.services.player_service import player_service

logger = logging.getLogger(__name__)


def _players_json_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "players.json"


def load_players_at_startup() -> None:
    """读取 players.json，为每条记录调用 player_service.create_player（已存在则跳过）。"""
    path = _players_json_path()
    if not path.is_file():
        msg = f"[players] 未找到角色列表文件，跳过加载: {path}"
        print(msg, flush=True)
        logger.info(msg)
        return
    print(f"[players] 开始从 {path} 加载角色列表 …", flush=True)
    logger.info("开始从 players.json 加载角色: %s", path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as ex:
        msg = f"[players] 读取 JSON 失败: {path} — {ex}"
        print(msg, flush=True)
        logger.exception("读取 players.json 失败: %s", path)
        return
    if not isinstance(raw, list):
        msg = "[players] players.json 根节点应为 JSON 数组，已跳过"
        print(msg, flush=True)
        logger.warning(msg)
        return
    total = len(raw)
    ok = 0
    skipped = 0
    failed = 0
    for item in raw:
        if not isinstance(item, dict):
            skipped += 1
            print(f"[players] 跳过非对象项: {item!r}", flush=True)
            logger.warning("跳过非对象项: %s", item)
            continue
        pid = str(item.get("id") or item.get("player_id") or "").strip()
        name = str(item.get("name") or "").strip()
        if not pid or not name:
            skipped += 1
            print(f"[players] 跳过无效项（缺少 id 或 name）: {item!r}", flush=True)
            logger.warning("跳过无效角色项（缺少 id 或 name）: %s", item)
            continue
        try:
            player_service.create_player(player_id=pid, name=name)
            ok += 1
            msg = f"[players] 已加载角色: id={pid!r} name={name!r}"
            print(msg, flush=True)
            logger.info("已从 players.json 加载角色: %s (%s)", pid, name)
        except Exception:
            failed += 1
            print(f"[players] 创建角色失败: id={pid!r} name={name!r}", flush=True)
            logger.exception("创建角色失败 id=%s name=%s", pid, name)
    summary = f"[players] 加载结束: 共 {total} 条记录, 成功 {ok}, 跳过 {skipped}, 失败 {failed}"
    print(summary, flush=True)
    logger.info(summary)
