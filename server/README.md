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

启动 HTTP 时，服务端在 **lifespan** 中执行 `agentscope.init` 并读取 `data/players.json`（JSON 数组，含 `id`、`name` 及可选 `system_prompt` / `sys_prompt`）创建玩家；`GET /players` 返回当前已加载的角色列表。

- **AgentScope / Studio**：`agentscope.init` 使用 **`project=AITOWN`**（可通过环境变量 `AGENTSCOPE_PROJECT` 覆盖）；`studio_url` 取自 `AGENTSCOPE_STUDIO_URL`，未设置则为不连 Studio。trace、token 等在有 Studio 时进入 Studio UI。

后端另提供管理用 REST：`GET /admin/status`、`POST /admin/pause`、`POST /admin/resume`、`GET /admin/logs`。

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
