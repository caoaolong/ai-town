"""AI 玩家代理 - 基于 agentscope 的 ReActAgent"""

from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit
from agentscope.model import OpenAIChatModel


SYS_PROMPT = """你生活在I小镇中，你希望通过自己的努力能过上更加幸福快乐的生活。
"""

class PlayerAgent(ReActAgent):
    """AI 玩家代理类

    继承自 AgentScope ReActAgent，支持 Agent Skill 功能。
    """

    def __init__(
        self,
        player_id: str,
        name: str,
        sys_prompt: str,
        model: OpenAIChatModel,
    ):
        """
        初始化 AI 玩家

        Args:
            player_id: 玩家 ID
            name: 玩家名称
            sys_prompt: 系统提示词
            model: 模型配置
        """
        toolkit = Toolkit()
        # 初始化 ReActAgent 父类
        super().__init__(
            name=name,
            model=model,
            sys_prompt=sys_prompt,
            memory=InMemoryMemory(),
            formatter=DashScopeChatFormatter(),
            toolkit=toolkit,
        )

        # 玩家特有属性
        self.player_id = player_id

    def get_info(self) -> dict:
        """
        获取玩家基本信息

        Returns:
            dict: 包含玩家 ID、名称的字典
        """
        return {
            "id": self.player_id,
            "name": self.name,
        }

    async def clear_memory(self):
        """清空对话记忆"""
        await self.memory.clear()
