# AI Town Server

基于 FastAPI 的游戏后端服务。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

**方式一：使用启动脚本**
```bash
start.bat
```

**方式二：使用 uvicorn**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**方式三：直接运行**
```bash
python main.py
```

### 3. HTTP 桌面小工具（可选）

在 `server` 目录执行：

```bash
python admin_console.py
```

- **仅**提供本机 **启动 / 关闭** 由该窗口拉起的 `uvicorn`（`SERVER_HOST` / `SERVER_PORT`，工作目录为 `server/`）；用 TCP 探测端口是否已监听；**在窗口内显示 uvicorn 标准输出日志**。
- **关闭桌面窗口或 Web 会话断开时**，会先尝试停止由本工具拉起的 HTTP 子进程（桌面端拦截关闭事件后再真正退出）。
- 默认 **桌面窗口**（`FLET_APP`）。浏览器调试：环境变量 `FLET_ADMIN_VIEW=web`，端口 `FLET_ADMIN_PORT`（默认 `8550`）。
- 工具内 **「启动 AgentScope Studio」** 会在本机执行 `as_studio`（未装全局命令时尝试 `npx -y @agentscope/studio`），就绪后一般会**自动打开浏览器**；可用 `AGENTSCOPE_AS_STUDIO` 覆盖整条启动命令。与后端一致的 Studio 根地址仍用 `AGENTSCOPE_STUDIO_URL`（默认 `http://localhost:3000`）。关闭管理台窗口时会尝试结束由本工具拉起的 `as_studio` 子进程。

后端另提供管理用 REST（与桌面工具无关）：`GET /admin/status`、`POST /admin/pause`、`POST /admin/resume`、`GET /admin/logs`。

启动 HTTP 时，服务端在 **lifespan** 中依次：**可选**连接 AgentScope Studio，再读取 `data/players.json`（JSON 数组，元素含 `id`、`name`）创建玩家；`GET /players` 返回当前已加载的角色列表。

- **AgentScope Studio**：设置环境变量 `AGENTSCOPE_STUDIO_URL`（例如 `http://localhost:3000`，须与本机 Studio 实际地址一致）后，启动时会执行 `agentscope.init(studio_url=...)`，trace、token 等会进入 Studio UI。若 Studio 未启动或网络失败，会在**标准输出**打印 `[agentscope] …` 并写日志，**不阻塞**服务启动。可选：`AGENTSCOPE_PROJECT`（默认 `ai-town`）、`AGENTSCOPE_RUN_NAME`、`AGENTSCOPE_LOGGING_LEVEL`（默认 `INFO`）、`AGENTSCOPE_STUDIO_HTTP_TIMEOUT`（默认 `3,20` 秒，格式为「连接,读取」）。**注意**：`admin_console` 里启动 `as_studio`**不会**给 uvicorn 写入环境变量；用管理台拉起 HTTP 时，若需连接 Studio，请在启动 `python admin_console.py` 的终端里先 `set`/`export` 好 `AGENTSCOPE_STUDIO_URL` 等变量。

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 欢迎信息 |
| GET | `/health` | 健康检查 |
| GET | `/ready` | 就绪检查 |
| GET | `/players` | 获取全部角色列表（启动时从 `data/players.json` 加载） |
| GET | `/admin/status` | 暂停状态与运行时长 |
| POST | `/admin/pause` | 暂停业务 API（白名单路径仍可用） |
| POST | `/admin/resume` | 恢复业务 API |
| GET | `/admin/logs` | 最近请求日志 |

## 项目结构

```
server/
├── main.py              # 应用入口
├── requirements.txt     # 依赖列表
├── admin_console.py     # 启停本机 uvicorn 并显示其日志的 Flet 小工具（可选）
├── data/
│   └── players.json     # 启动时加载的角色列表（id + name）
├── start.bat           # 启动脚本
└── app/
    ├── __init__.py
    ├── bootstrap_agentscope.py  # 启动时可选 agentscope.init(studio_url=...)
    ├── bootstrap_players.py    # 启动时从 players.json 创建玩家
    ├── admin_runtime.py      # 暂停开关与请求日志缓冲
    ├── middleware/
    │   └── request_audit.py  # 请求审计与暂停拦截
    └── routers/
        ├── __init__.py
        ├── admin.py
        ├── health.py
        ├── chat.py
        └── player.py
```
