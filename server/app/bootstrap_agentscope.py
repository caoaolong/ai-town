"""HTTP 服务启动时可选连接 AgentScope Studio（traces、token 等进入 Studio UI）"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager

import requests

logger = logging.getLogger(__name__)


def _brief_http_error(ex: BaseException) -> str:
    """压缩 requests/urllib3 长链，突出常见本机未启动 Studio 的情况。"""
    s = str(ex).replace("\n", " ")
    low = s.lower()
    if "10061" in s or "积极拒绝" in s or "connection refused" in low:
        return "端口未接受连接（本机 Studio 未启动或端口不是 3000）"
    if "timed out" in low or "timeout" in low:
        return "连接或读取超时"
    if len(s) > 220:
        return s[:220] + "…"
    return s


def _parse_http_timeout() -> tuple[float, float]:
    """连接超时与读取超时（秒），格式「连接,读取」或单个数字表示二者相同。"""
    raw = os.getenv("AGENTSCOPE_STUDIO_HTTP_TIMEOUT", "3,20").strip()
    if not raw:
        return (3.0, 20.0)
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if len(parts) == 1:
        t = float(parts[0])
        return (t, t)
    return (float(parts[0]), float(parts[1]))


@contextmanager
def _requests_post_default_timeout(timeout: tuple[float, float]):
    """agentscope.init 内 registerRun 使用 requests.post 且未设 timeout，无 Studio 时会长时间阻塞；此处临时注入默认超时。"""
    orig = requests.post

    def wrapped(*args, **kwargs):
        kwargs.setdefault("timeout", timeout)
        return orig(*args, **kwargs)

    requests.post = wrapped
    try:
        yield
    finally:
        requests.post = orig


def _preflight_studio_http(studio_url: str, timeout: tuple[float, float]) -> None:
    """仅检测 TCP/HTTP 能否连上根路径；404 等不抛错，连接失败才抛。"""
    base = studio_url.strip().rstrip("/")
    requests.get(f"{base}/", timeout=timeout)


def init_agentscope_studio() -> None:
    """若设置了 AGENTSCOPE_STUDIO_URL，则调用 agentscope.init 注册本进程到 Studio。"""
    studio_url = os.getenv("AGENTSCOPE_STUDIO_URL", "").strip()
    if not studio_url:
        msg = (
            "[agentscope] 未设置 AGENTSCOPE_STUDIO_URL，已跳过 Studio 初始化。"
            " 说明：管理台「打开 AgentScope Studio」只会在本机打开浏览器，"
            " 不会为 FastAPI 设置 Studio 地址；请在启动 uvicorn 的同一环境中设置该变量。"
        )
        logger.warning("%s", msg)
        return

    timeout = _parse_http_timeout()
    project = os.getenv("AGENTSCOPE_PROJECT", "ai-town").strip() or "ai-town"
    run_name = os.getenv("AGENTSCOPE_RUN_NAME", "").strip() or None
    log_level = os.getenv("AGENTSCOPE_LOGGING_LEVEL", "INFO").strip() or "INFO"

    import agentscope

    kwargs: dict[str, str] = {
        "project": project,
        "studio_url": studio_url,
        "logging_level": log_level,
    }
    if run_name:
        kwargs["name"] = run_name

    logger.info(
        "[agentscope] 预检 Studio: %s（超时 connect,read=%s）",
        studio_url,
        timeout,
    )
    try:
        _preflight_studio_http(studio_url, timeout)
    except requests.RequestException as ex:
        brief = _brief_http_error(ex)
        logger.warning(
            "[agentscope] Studio 不可达，已跳过 init | url=%s | %s",
            studio_url,
            brief,
        )
        return
    except Exception:
        logger.exception(
            "[agentscope] Studio 预检未预期异常，已跳过 init | url=%s",
            studio_url,
        )
        return

    logger.info("[agentscope] 正在向 Studio 注册运行（registerRun）…")
    try:
        with _requests_post_default_timeout(timeout):
            agentscope.init(**kwargs)
    except requests.RequestException as ex:
        brief = _brief_http_error(ex)
        logger.warning(
            "[agentscope] Studio 注册失败（服务继续）| url=%s | %s",
            studio_url,
            brief,
        )
        return
    except Exception:
        logger.exception(
            "[agentscope] Studio 初始化未预期异常（服务继续）| url=%s",
            studio_url,
        )
        return
    logger.info(
        "[agentscope] 已连接 Studio: url=%s project=%s",
        studio_url,
        project,
    )
