"""Player service for creating and storing AI-controlled players."""

import json
import logging
from pathlib import Path
from typing import Optional

from agentscope.model import OpenAIChatModel

from app.agents.player_agent import PlayerAgent
from app.config import Config

logger = logging.getLogger(__name__)


class PlayerService:
    """Singleton service that manages all AI players."""

    DEFAULT_SKILLS = ["survival_manual"]

    _instance = None
    _players: dict[str, PlayerAgent] = {}
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._load_players_from_file()
            self._initialized = True

    def _load_players_from_file(self):
        """从 players.json 文件加载玩家数据"""
        # 路径：server/data/players.json
        players_file = Path(__file__).parent.parent.parent / "data" / "players.json"
        
        if not players_file.exists():
            logger.warning(f"玩家数据文件不存在：{players_file}")
            return
        
        try:
            with open(players_file, "r", encoding="utf-8") as f:
                players_data = json.load(f)
            
            for player_data in players_data:
                player_id = player_data.get("id")
                name = player_data.get("name")
                sys_prompt = player_data.get("system_prompt", f"你是一个 AI 小镇的居民，名叫{name}。")
                
                if player_id and name:
                    self.create_player(player_id, name, sys_prompt)
            
            logger.info(f"已加载 {len(self._players)} 个 AI 玩家")
            
        except json.JSONDecodeError as e:
            logger.error(f"解析 players.json 失败：{e}")
        except Exception as e:
            logger.error(f"加载玩家数据失败：{e}")

    def create_player(self, player_id: str, name: str, sys_prompt: str) -> PlayerAgent:
        """Create a player instance or return an existing one."""
        if player_id in self._players:
            return self._players[player_id]

        # model = DashScopeChatModel(
        #     model_name=Config.LLM_MODEL,
        #     api_key=Config.LLM_API_KEY,
        # )
        model = OpenAIChatModel(
            model_name=Config.LLM_MODEL,
            api_key=Config.LLM_API_KEY,
            client_kwargs={
                "base_url": Config.LLM_API_BASE,
            },
            reasoning_effort=None
        )

        player = PlayerAgent(
            player_id=player_id,
            name=name,
            sys_prompt=sys_prompt,
            model=model,
        )
        self._players[player_id] = player
        return player

    def get_player(self, player_id: str) -> Optional[PlayerAgent]:
        """Return a player by id."""
        return self._players.get(player_id)

    def get_all_players(self) -> dict[str, PlayerAgent]:
        """Return all players."""
        return self._players

    def remove_player(self, player_id: str) -> bool:
        """Remove a player by id."""
        if player_id in self._players:
            del self._players[player_id]
            return True
        return False


player_service = PlayerService()
