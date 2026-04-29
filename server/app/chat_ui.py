"""
AI Town Chainlit 聊天界面

用于测试与 AI 小镇玩家的对话功能

使用方法:
    chainlit run app/chat_ui.py --port 8001
"""

import sys
from pathlib import Path
from typing import Optional

# 添加 server 目录到 Python 路径
server_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(server_path))

import chainlit as cl
from agentscope.message import Msg

from app.services.player_service import player_service, PlayerAgent


# 存储当前对话的玩家 Agent
current_agent: Optional[PlayerAgent] = None
current_player_id: Optional[str] = None


@cl.on_chat_start
async def on_chat_start():
    """聊天开始时的初始化"""
    global current_agent, current_player_id

    # 设置聊天标题
    cl.user_session.set("session_started", True)

    # 欢迎消息
    await cl.Message(
        content="""
# 🏠 欢迎来到 AI 小镇聊天测试界面

这是一个用于测试 AI 玩家对话功能的界面。

## 快速开始
1. 使用 `/select` 命令选择 AI 玩家
2. 或直接输入消息开始对话（默认选择第一个玩家）

输入 `/help` 查看更多命令。
        """,
    ).send()

    # 自动加载玩家列表
    await load_players()


async def load_players():
    """加载并显示玩家列表"""
    players = player_service.get_all_players()

    if not players:
        await cl.Message(
            content="""❌ 没有找到任何 AI 玩家。

可能原因：
1. `data/players.json` 文件不存在
2. 文件格式不正确
3. LLM API 配置错误

请检查服务器日志获取更多信息。
"""
        ).send()
        return

    # 创建玩家选择按钮
    actions = []
    for player_id, player in players.items():
        actions.append(
            cl.Action(
                name=f"select_{player_id}",
                payload={"player_id": player_id, "player_name": player.name},
                label=f"👤 {player.name}",
                tooltip=f"ID: {player_id}",
            )
        )

    await cl.AskActionMessage(
        content="**选择一个 AI 玩家开始对话：**",
        actions=actions,
    ).send()


@cl.action_callback("select_.*")
async def on_select_player(action: cl.Action):
    """处理玩家选择"""
    global current_agent, current_player_id

    # 从 payload 中获取玩家 ID
    player_id = action.payload.get("player_id")
    player_name = action.payload.get("player_name", "未知玩家")

    if not isinstance(player_id, str):
        await cl.Message(content="❌ 缺少 player_id").send()
        return

    # 获取玩家
    agent = player_service.get_player(player_id)

    if agent is None:
        await cl.Message(content=f"❌ 玩家 {player_id} 不存在").send()
        return

    # 设置当前玩家
    current_player_id = player_id
    current_agent = agent

    # 保存会话信息
    cl.user_session.set("current_player_id", player_id)
    cl.user_session.set("player_name", player_name)

    # 发送确认消息
    await cl.Message(
        content=f"""
## ✅ 已选择 AI 玩家

**名称:** {player_name}  
**ID:** {player_id}  
**角色:** AI 小镇居民

现在可以开始对话了！输入消息即可与 {player_name} 交流。
        """
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """处理用户消息"""
    global current_agent, current_player_id

    # 检查是否选择了玩家
    if current_agent is None:
        players = player_service.get_all_players()
        if players:
            # 自动选择第一个玩家
            first_player_id = list(players.keys())[0]
            current_player_id = first_player_id
            current_agent = players[first_player_id]

            await cl.Message(
                content=f"ℹ️ 自动选择玩家：**{current_agent.name}**\n\n使用 `/select` 可以切换玩家。"
            ).send()
        else:
            await cl.Message(
                content="❌ 请先选择一个 AI 玩家！使用 `/select` 命令。"
            ).send()
            return

    # 处理命令
    if message.content.startswith("/"):
        await handle_command(message.content)
        return

    # 显示思考中
    thinking_msg = cl.Message(content="🤔 思考中...")
    await thinking_msg.send()

    try:
        # 创建用户消息
        user_msg = Msg(name="user", content=message.content, role="user")

        # 调用 AI Agent（注意：reply 是异步方法）
        response = await current_agent.reply(user_msg)

        # 移除思考消息
        await thinking_msg.remove()

        # 获取回复内容 - 处理不同的响应格式
        if isinstance(response, Msg):
            # Msg 对象，提取 content 字段
            content = response.content
            # 如果 content 是列表，提取文本内容
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif isinstance(item, str):
                        text_parts.append(item)
                content = "".join(text_parts) if text_parts else str(content)
        elif isinstance(response, dict):
            content = response.get("content", str(response))
        else:
            content = str(response)

        # 发送回复
        await cl.Message(
            content=content,
        ).send()

    except Exception as e:
        await thinking_msg.remove()
        error_content = f"❌ 发生错误：{str(e)}"
        if "API" in str(e).upper() or "MODEL" in str(e).upper():
            error_content += "\n\n请检查 LLM API 配置是否正确。"
        await cl.Message(content=error_content).send()


async def handle_command(command: str):
    """处理聊天命令"""
    cmd_parts = command.strip().split(maxsplit=1)
    cmd_name = cmd_parts[0].lower() if cmd_parts else ""
    cmd_arg = cmd_parts[1] if len(cmd_parts) > 1 else ""

    if cmd_name == "/select":
        await load_players()

    elif cmd_name == "/help":
        help_text = """
## 📖 可用命令

| 命令 | 说明 |
|------|------|
| `/select` | 重新选择 AI 玩家 |
| `/reset` | 重置当前对话记忆 |
| `/info` | 显示当前 AI 玩家信息 |
| `/players` | 显示所有可用玩家 |
| `/help` | 显示帮助信息 |

## 💡 提示

- 直接输入消息即可与 AI 玩家对话
- 对话历史会自动保存到内存中
        """
        await cl.Message(content=help_text).send()

    elif cmd_name == "/reset":
        global current_agent
        if current_agent:
            await current_agent.clear_memory()
            await cl.Message(content="✅ 对话记忆已重置").send()
        else:
            await cl.Message(content="❌ 未选择 AI 玩家").send()

    elif cmd_name == "/info":
        if current_agent:
            info = f"""
### 👤 当前 AI 玩家

- **ID:** {current_player_id}
- **名称:** {current_agent.name}
- **状态:** 在线
            """
            await cl.Message(content=info).send()
        else:
            await cl.Message(content="❌ 未选择 AI 玩家").send()

    elif cmd_name == "/players":
        players = player_service.get_all_players()
        if players:
            text = "### 📋 可用玩家列表\n\n"
            for pid, player in players.items():
                text += f"- `{pid}` - **{player.name}**\n"
            await cl.Message(content=text).send()
        else:
            await cl.Message(content="❌ 没有可用玩家").send()

    else:
        await cl.Message(
            content=f"❌ 未知命令：{command}\n\n输入 `/help` 查看可用命令。"
        ).send()


@cl.on_settings_update
async def on_settings_update(settings):
    """设置更新时的处理"""
    pass
