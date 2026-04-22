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
    """AI 玩家代理类"""

    def __init__(self, player_id: str, name: str, sys_prompt: str, model: DashScopeChatModel):
        """
        初始化 AI 玩家

        Args:
            player_id: 玩家 ID
            name: 玩家名称
            model_config: 模型配置
        """
        self.player_id = player_id
        self.name = name
        self.model = model
        self.sys_prompt = sys_prompt
        self.skills_dir = Path(__file__).parent.parent.parent / "skills"
        self.skills = []
        self._agent = None
        self._toolkit = Toolkit()
        self._init_agent()

    def _init_agent(self):
        """初始化 ReActAgent"""
        self._agent = ReActAgent(
            name=self.name,
            model=self.model,
            sys_prompt=self.sys_prompt,
            memory=InMemoryMemory(),
            formatter=DashScopeChatFormatter(),
            toolkit=self._toolkit,
        )

    def add_skill(self, skill_name: str, skill_dir: Optional[str] = None):
        """
        添加技能

        技能通过 SKILL.md 文件定义，包含 YAML frontmatter 和指令说明

        Args:
            skill_name: 技能名称（也是目录名）
            skill_dir: 技能目录路径，默认为 skills/{skill_name}
        """
        if skill_dir is None:
            skill_dir = str(self.skills_dir / skill_name)

        # 使用 create_tool_group 来管理技能
        self._toolkit.create_tool_group(
            group_name=skill_name,
            description=f"Skill: {skill_name}",
            active=True,
            notes=f"Use this skill when you need to {skill_name}.",
        )
        self.skills.append({
            "name": skill_name,
            "dir": skill_dir
        })

    def add_skills(self, skill_names: list[str]):
        """批量添加技能"""
        for skill_name in skill_names:
            self.add_skill(skill_name)

    def get_skills(self) -> list[dict]:
        """获取所有技能"""
        return self.skills

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
        """获取玩家基本信息"""
        return {
            "id": self.player_id,
            "name": self.name,
            "skills_count": len(self.skills),
            "skills": [s["name"] for s in self.skills]
        }
