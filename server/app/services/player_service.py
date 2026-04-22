"""玩家服务 - 管理 AI 玩家的创建和存储"""

from typing import Optional
from app.agents.player_agent import PlayerAgent
from agentscope.model import DashScopeChatModel
from app.config import Config


class PlayerService:
    """玩家服务类 - 单例模式管理所有玩家"""
    
    _instance = None
    _players: dict[str, PlayerAgent] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def create_player(self, player_id: str, name: str, sys_prompt: str) -> PlayerAgent:
        """
        创建新玩家
        
        Args:
            player_id: 玩家 ID
            name: 玩家名称
            
        Returns:
            创建的 PlayerAgent 实例
        """
        if player_id in self._players:
            return self._players[player_id]
        
        # 创建模型配置
        model = DashScopeChatModel(
            model_name=Config.LLM_MODEL,
            api_key=Config.LLM_API_KEY,
        )
        
        player = PlayerAgent(player_id=player_id, name=name, sys_prompt=sys_prompt, model=model)
        self._players[player_id] = player
        
        # 注册默认技能
        self._register_default_skills(player)
        
        return player
    
    def _register_default_skills(self, player: PlayerAgent):
        """注册默认技能"""
        # 默认技能：观察、移动、对话
        default_skills = ["observe", "move", "talk"]
        player.add_skills(default_skills)
    
    def get_player(self, player_id: str) -> Optional[PlayerAgent]:
        """获取玩家"""
        return self._players.get(player_id)
    
    def get_all_players(self) -> dict[str, PlayerAgent]:
        """获取所有玩家"""
        return self._players
    
    def remove_player(self, player_id: str) -> bool:
        """移除玩家"""
        if player_id in self._players:
            del self._players[player_id]
            return True
        return False


# 全局服务实例
player_service = PlayerService()
