"""AI 玩家代理 - 基于 agentscope 的 ReActAgent"""

from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit
from pathlib import Path
from typing import Optional


class PlayerAgent:
    """AI 玩家代理类
    
    基于 AgentScope ReActAgent 实现，支持 Agent Skill 功能。
    Skills 通过 SKILL.md 文件定义，包含 YAML frontmatter 和详细的使用说明。
    """

    def __init__(self, player_id: str, name: str, sys_prompt: str, model: DashScopeChatModel):
        """
        初始化 AI 玩家

        Args:
            player_id: 玩家 ID
            name: 玩家名称
            sys_prompt: 系统提示词
            model: 模型配置
        """
        self.player_id = player_id
        self.name = name
        self.model = model
        self.sys_prompt = sys_prompt
        self.skills_dir = Path(__file__).parent.parent.parent / "skills"
        self.registered_skills = []
        self._agent = None
        self._toolkit = Toolkit()
        self._init_agent()

    def _init_agent(self):
        """初始化 ReActAgent
        
        ReActAgent 会自动将已注册的 Agent Skill 提示附加到系统提示中。
        """
        self._agent = ReActAgent(
            name=self.name,
            model=self.model,
            sys_prompt=self.sys_prompt,
            memory=InMemoryMemory(),
            formatter=DashScopeChatFormatter(),
            toolkit=self._toolkit,
        )

    def add_skill(self, skill_name: str, skill_dir: Optional[str] = None) -> bool:
        """
        添加技能

        技能通过 SKILL.md 文件定义，包含 YAML frontmatter 和指令说明。
        注册后，Agent 会自动获得该技能的使用说明。

        Args:
            skill_name: 技能名称（也是目录名）
            skill_dir: 技能目录路径，默认为 skills/{skill_name}
            
        Returns:
            bool: 是否注册成功
        """
        if skill_dir is None:
            skill_dir = str(self.skills_dir / skill_name)

        try:
            # 使用 Toolkit 的 register_agent_skill 方法注册技能
            self._toolkit.register_agent_skill(skill_dir)
            self.registered_skills.append({
                "name": skill_name,
                "dir": skill_dir
            })
            return True
        except Exception as e:
            print(f"Failed to register skill '{skill_name}': {e}")
            return False

    def add_skills(self, skill_names: list[str]) -> int:
        """
        批量添加技能

        Args:
            skill_names: 技能名称列表

        Returns:
            int: 成功注册的技能数量
        """
        count = 0
        for skill_name in skill_names:
            if self.add_skill(skill_name):
                count += 1
        return count

    def get_skills(self) -> list[dict]:
        """获取所有已注册的技能"""
        return self.registered_skills

    def get_skill_prompt(self) -> str | None:
        """
        获取所有注册技能的提示词

        这个提示词会自动被包含在 Agent 的系统提示中。

        Returns:
            str: 格式化的技能提示词文本
        """
        return self._toolkit.get_agent_skill_prompt()

    def remove_skill(self, skill_name: str) -> bool:
        """
        移除一个已注册的技能

        Args:
            skill_name: 要移除的技能名称

        Returns:
            bool: 是否移除成功
        """
        try:
            self._toolkit.remove_agent_skill(skill_name)
            self.registered_skills = [
                s for s in self.registered_skills if s["name"] != skill_name
            ]
            return True
        except Exception as e:
            print(f"Failed to remove skill '{skill_name}': {e}")
            return False

    async def chat(self, message: str) -> Msg:
        """
        处理聊天消息

        Args:
            message: 输入消息

        Returns:
            AI 回复消息
        """
        if not self._agent:
            raise ValueError("Agent not initialized")

        msg = Msg(name=self.name, content=message, role="user")
        response = await self._agent(msg)
        return response

    def get_info(self) -> dict:
        """
        获取玩家基本信息，包括已注册的技能列表

        Returns:
            dict: 包含玩家ID、名称、技能数量和技能列表的字典
        """
        return {
            "id": self.player_id,
            "name": self.name,
            "skills_count": len(self.registered_skills),
            "skills": [s["name"] for s in self.registered_skills]
        }
