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

- **仅**提供本机 **启动 / 关闭** 由该窗口拉起的 `uvicorn`（`SERVER_HOST` / `SERVER_PORT`，工作目录为 `server/`）；用 TCP 探测端口是否已监听；**窗口内分左右两栏**：一栏为 **HTTP 服务（uvicorn）日志**，一栏为 **AgentScope Studio（as_studio）日志**，互不混写。
- **关闭桌面窗口或 Web 会话断开时**，会先尝试停止由本工具拉起的 **as_studio** 与 **HTTP** 子进程（桌面端拦截关闭事件后再真正退出）。
- 默认 **桌面窗口**（`FLET_APP`）。浏览器调试：环境变量 `FLET_ADMIN_VIEW=web`，端口 `FLET_ADMIN_PORT`（默认 `8550`）。
- 工具内 **AgentScope Studio** 与 HTTP 相同，为 **一个按钮启停**：本机执行 `as_studio`（无全局命令时尝试 `npx -y @agentscope/studio`），就绪后一般会**自动打开浏览器**；可用 `AGENTSCOPE_AS_STUDIO` 覆盖启动命令。`AGENTSCOPE_STUDIO_URL`（默认 `http://localhost:3000`）须与后端 `agentscope.init` 的 Studio 地址一致。

后端另提供管理用 REST（与桌面工具无关）：`GET /admin/status`、`POST /admin/pause`、`POST /admin/resume`、`GET /admin/logs`。

启动 HTTP 时，服务端在 **lifespan** 中执行 `agentscope.init` 并读取 `data/players.json`（JSON 数组，含 `id`、`name` 及可选 `system_prompt` / `sys_prompt`）创建玩家；`GET /players` 返回当前已加载的角色列表。

- **AgentScope / Studio**：`agentscope.init` 使用 **`project=AITOWN`**（可通过环境变量 `AGENTSCOPE_PROJECT` 覆盖）；`studio_url` 取自 `AGENTSCOPE_STUDIO_URL`，未设置则为不连 Studio。trace、token 等在有 Studio 时进入 Studio UI。**注意**：`admin_console` 启停 `as_studio` **不会**给 uvicorn 写入环境变量；若需后端连 Studio，请在启动 `python admin_console.py` 的终端里先 `set`/`export` 好 `AGENTSCOPE_STUDIO_URL` 等变量。

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
├── admin_console.py     # 启停本机 uvicorn / as_studio，分栏显示二者日志的 Flet 小工具（可选）
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
