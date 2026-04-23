"""本机 HTTP（uvicorn）启动/关闭桌面工具，并显示服务标准输出日志。"""

from __future__ import annotations

import asyncio
import os
import shlex
import shutil
import subprocess
import sys
from collections import deque
from pathlib import Path

import flet as ft

Icons = ft.icons.Icons


def _server_root() -> Path:
    """含 main.py 的 server 目录（本文件所在目录）"""
    return Path(__file__).resolve().parent


def _server_port() -> int:
    return int(os.getenv("SERVER_PORT", "8000"))


def _server_bind_host() -> str:
    return os.getenv("SERVER_HOST", "0.0.0.0")


def _probe_host(bind: str) -> str:
    """绑定 0.0.0.0 时用本机回环探测端口是否已监听"""
    return "127.0.0.1" if bind in ("0.0.0.0", "::", "") else bind


def _agentscope_studio_url() -> str:
    """与 agentscope.init(studio_url=...) 对齐；本地 as_studio 默认多为 3000 端口。"""
    u = os.getenv("AGENTSCOPE_STUDIO_URL", "http://localhost:3000").strip()
    return u if u else "http://localhost:3000"


def _resolve_as_studio_argv() -> list[str] | None:
    """解析本机 as_studio 启动命令；不设 CREATE_NO_WINDOW，便于子进程自动打开浏览器。"""
    override = os.getenv("AGENTSCOPE_AS_STUDIO", "").strip()
    if override:
        parts = shlex.split(override, posix=os.name != "nt")
        return parts if parts else None
    w = shutil.which("as_studio")
    if w:
        return [w]
    if shutil.which("npx"):
        return ["npx", "-y", "@agentscope/studio"]
    return None


async def main(page: ft.Page) -> None:
    page.title = "HTTP 服务"
    page.padding = 16
    server_dir = _server_root()
    http_port = _server_port()
    http_bind = _server_bind_host()
    probe_host = _probe_host(http_bind)

    _http_proc_holder: list[asyncio.subprocess.Process | None] = [None]
    _btn_holder: list[ft.FilledButton | None] = [None]
    _studio_btn_holder: list[ft.FilledButton | None] = [None]
    _init_agentscope_flag: list[bool] = [True]  # 是否在启动 HTTP 时初始化 AgentScope
    _http_log_deque: deque[str] = deque(maxlen=500)
    _studio_log_deque: deque[str] = deque(maxlen=500)
    _reader_tasks: list[asyncio.Task] = []
    _studio_proc_holder: list[asyncio.subprocess.Process | None] = [None]
    _studio_reader_tasks: list[asyncio.Task] = []
    _close_shutdown_done: list[bool] = [False]
    _window_close_lock = asyncio.Lock()

    hint = ft.Text(value="", size=13, color=ft.Colors.GREY_800)
    studio_hint = ft.Text(value="", size=13, color=ft.Colors.GREY_800)
    tip = ft.Text(value="", size=12, color=ft.Colors.GREEN_800)
    http_log_field = ft.TextField(
        value="",
        label="HTTP 服务（uvicorn stdout/stderr）",
        multiline=True,
        read_only=True,
        expand=True,
        min_lines=10,
        max_lines=28,
        text_align=ft.TextAlign.START,
    )
    studio_log_field = ft.TextField(
        value="",
        label="AgentScope Studio（as_studio stdout/stderr）",
        multiline=True,
        read_only=True,
        expand=True,
        min_lines=10,
        max_lines=28,
        text_align=ft.TextAlign.START,
    )

    def _sync_ui() -> None:
        p = _http_proc_holder[0]
        btn = _btn_holder[0]
        if p is not None and p.returncode is None:
            hint.value = f"运行中  |  PID {p.pid}  |  绑定 {http_bind}:{http_port}"
            hint.color = ft.Colors.BLUE_800
            if btn is not None:
                btn.content = "关闭 HTTP 服务"
                btn.icon = Icons.STOP_CIRCLE_OUTLINED
                btn.bgcolor = ft.Colors.RED_700
                btn.color = ft.Colors.WHITE
        elif p is not None:
            hint.value = f"子进程已结束（退出码 {p.returncode}）"
            hint.color = ft.Colors.ORANGE_800
            _http_proc_holder[0] = None
            if btn is not None:
                btn.content = "启动 HTTP 服务"
                btn.icon = Icons.PLAY_ARROW
                btn.bgcolor = None
                btn.color = None
        else:
            hint.value = f"未启动  |  工作目录 {server_dir}  |  端口 {http_port}（SERVER_PORT）"
            hint.color = ft.Colors.GREY_800
            if btn is not None:
                btn.content = "启动 HTTP 服务"
                btn.icon = Icons.PLAY_ARROW
                btn.bgcolor = None
                btn.color = None

        sp = _studio_proc_holder[0]
        sbtn = _studio_btn_holder[0]
        if sp is not None and sp.returncode is None:
            studio_hint.value = (
                f"AgentScope Studio 运行中  |  PID {sp.pid}  |  {_agentscope_studio_url()}"
            )
            studio_hint.color = ft.Colors.BLUE_800
            if sbtn is not None:
                sbtn.content = "关闭 AgentScope Studio"
                sbtn.icon = Icons.STOP_CIRCLE_OUTLINED
                sbtn.bgcolor = ft.Colors.RED_700
                sbtn.color = ft.Colors.WHITE
        elif sp is not None:
            studio_hint.value = f"Studio 子进程已结束（退出码 {sp.returncode}）"
            studio_hint.color = ft.Colors.ORANGE_800
            _studio_proc_holder[0] = None
            if sbtn is not None:
                sbtn.content = "启动 AgentScope Studio"
                sbtn.icon = Icons.PLAY_ARROW
                sbtn.bgcolor = None
                sbtn.color = None
        else:
            studio_hint.value = "AgentScope Studio 未启动（as_studio / npx）"
            studio_hint.color = ft.Colors.GREY_800
            if sbtn is not None:
                sbtn.content = "启动 AgentScope Studio"
                sbtn.icon = Icons.PLAY_ARROW
                sbtn.bgcolor = None
                sbtn.color = None

    def _append_http_log_line(text: str) -> None:
        _http_log_deque.append(text)
        http_log_field.value = "\n".join(_http_log_deque)

    def _append_studio_log_line(text: str) -> None:
        _studio_log_deque.append(text)
        studio_log_field.value = "\n".join(_studio_log_deque)

    async def _drain_reader_tasks(
        tasks: list[asyncio.Task], *, per_task_timeout: float = 5.0
    ) -> None:
        """先结束子进程再调用：等待读协程自然读到 EOF 后退出，避免先 cancel 导致 Win Proactor 管道在 loop 关闭后才 __del__。"""
        for t in list(tasks):
            if t.done():
                continue
            try:
                await asyncio.wait_for(t, timeout=per_task_timeout)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                t.cancel()
                try:
                    await t
                except asyncio.CancelledError:
                    pass
                except Exception:
                    # 忽略清理过程中的其他异常，避免资源警告
                    pass
        tasks.clear()
        # 在 Windows 上，更激进地清理资源
        if sys.platform == "win32":
            await asyncio.sleep(0.1)
            # 强制垃圾回收
            import gc
            gc.collect()
            await asyncio.sleep(0.05)

    async def _pump_stdout(stream: asyncio.StreamReader) -> None:
        n = 0
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                s = line.decode("utf-8", errors="replace").rstrip("\r\n")
                if s:
                    _append_http_log_line(s)
                    n += 1
                    if n % 4 == 0:
                        page.update()
        except asyncio.CancelledError:
            raise
        except (OSError, BrokenPipeError, ConnectionResetError):
            # 管道已关闭，正常退出
            pass
        except Exception as ex:
            _append_http_log_line(f"[日志读取异常] {ex}")
        finally:
            page.update()

    async def _pump_studio_stdout(stream: asyncio.StreamReader) -> None:
        n = 0
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                s = line.decode("utf-8", errors="replace").rstrip("\r\n")
                if s:
                    _append_studio_log_line(s)
                    n += 1
                    if n % 4 == 0:
                        page.update()
        except asyncio.CancelledError:
            raise
        except (OSError, BrokenPipeError, ConnectionResetError):
            # 管道已关闭，正常退出
            pass
        except Exception as ex:
            _append_studio_log_line(f"[日志读取异常] {ex}")
        finally:
            # 子进程退出后由 _sync_ui 的 elif 分支清理 holder；此处只刷新界面
            _sync_ui()
            page.update()

    async def _flash(msg: str, *, error: bool = False) -> None:
        tip.value = msg
        tip.color = ft.Colors.RED_800 if error else ft.Colors.GREEN_800
        page.update()
        await asyncio.sleep(2.0)
        tip.value = ""
        page.update()

    async def _start_http() -> None:
        p = _http_proc_holder[0]
        if p is not None and p.returncode is None:
            return
        if p is not None:
            _http_proc_holder[0] = None
        await _drain_reader_tasks(_reader_tasks, per_task_timeout=2.0)
        main_py = server_dir / "main.py"
        if not main_py.is_file():
            await _flash(f"未找到 {main_py}", error=True)
            return
        _http_log_deque.clear()
        http_log_field.value = ""
        
        # 如果勾选了"初始化 AgentScope"，先启动 AgentScope
        if _init_agentscope_flag[0]:
            _append_http_log_line("检查 AgentScope Studio 是否已启动…")
            page.update()
            sp = _studio_proc_holder[0]
            if sp is None or sp.returncode is not None:
                # AgentScope 未启动，先启动它
                _append_http_log_line("AgentScope Studio 未启动，正在启动…")
                page.update()
                argv = _resolve_as_studio_argv()
                if not argv:
                    await _flash(
                        "未找到 as_studio 且勾选了初始化 AgentScope，请先手动启动或取消勾选",
                        error=True,
                    )
                    return
                try:
                    if sys.platform == "win32":
                        sp_proc = await asyncio.create_subprocess_exec(
                            *argv,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.STDOUT,
                            env=os.environ.copy(),
                        )
                    else:
                        sp_proc = await asyncio.create_subprocess_exec(
                            *argv,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.STDOUT,
                            env=os.environ.copy(),
                        )
                    _studio_proc_holder[0] = sp_proc
                    if sp_proc.stdout is not None:
                        t = asyncio.create_task(_pump_studio_stdout(sp_proc.stdout))
                        _studio_reader_tasks.append(t)
                    _sync_ui()
                except Exception as ex:
                    await _flash(f"启动 AgentScope Studio 失败: {ex}", error=True)
                    return
                
                # 等待 AgentScope Studio 就绪
                _append_http_log_line("等待 AgentScope Studio 就绪…")
                page.update()
                studio_url = _agentscope_studio_url()
                
                # 解析 URL 获取主机和端口
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(studio_url)
                    studio_host = parsed.hostname or "localhost"
                    studio_port = parsed.port or 3000
                except Exception:
                    studio_host = "localhost"
                    studio_port = 3000
                
                for attempt in range(15):  # 最多等待 30 秒（15 * 2）
                    try:
                        _r, w = await asyncio.wait_for(
                            asyncio.open_connection(studio_host, studio_port),
                            timeout=1.0
                        )
                        w.close()
                        try:
                            await w.wait_closed()
                        except Exception:
                            pass
                        _append_http_log_line("AgentScope Studio 已就绪")
                        page.update()
                        break
                    except (OSError, asyncio.TimeoutError, ConnectionError, ValueError):
                        if attempt < 14:
                            await asyncio.sleep(2)
                        else:
                            await _flash("AgentScope Studio 启动超时，请检查配置", error=True)
                            await _stop_as_studio(silent=True, interactive=False)
                            return
        
        _append_http_log_line("正在启动 uvicorn …")
        page.update()

        # 准备环境变量
        env = os.environ.copy()
        env["INIT_AGENTSCOPE"] = "1" if _init_agentscope_flag[0] else "0"
        
        # 检查是否正在关闭程序，如果是则不创建管道以避免资源警告
        is_shutting_down = _close_shutdown_done[0]
        
        _exec_args = (
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            http_bind,
            "--port",
            str(http_port),
        )
        try:
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_exec(
                    *_exec_args,
                    cwd=str(server_dir),
                    stdout=asyncio.subprocess.DEVNULL if is_shutting_down else asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    env=env,
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    *_exec_args,
                    cwd=str(server_dir),
                    stdout=asyncio.subprocess.DEVNULL if is_shutting_down else asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    env=env,
                )
        except Exception as ex:
            await _flash(f"启动失败: {ex}", error=True)
            return
        _http_proc_holder[0] = proc
        if proc.stdout is not None and not is_shutting_down:
            t = asyncio.create_task(_pump_stdout(proc.stdout))
            _reader_tasks.append(t)
        _sync_ui()
        page.update()
        for _ in range(50):
            await asyncio.sleep(0.2)
            if proc.returncode is not None:
                await _flash(f"进程已退出（码 {proc.returncode}），请检查端口或依赖", error=True)
                _http_proc_holder[0] = None
                _append_http_log_line(f"[进程退出] returncode={proc.returncode}")
                await _drain_reader_tasks(_reader_tasks, per_task_timeout=6.0)
                _sync_ui()
                page.update()
                return
            try:
                _r, w = await asyncio.wait_for(
                    asyncio.open_connection(probe_host, http_port), timeout=0.35
                )
                w.close()
                try:
                    await w.wait_closed()
                except Exception:
                    pass
                await _flash("端口已监听，HTTP 服务应已就绪")
                _sync_ui()
                page.update()
                return
            except (OSError, asyncio.TimeoutError, ConnectionError):
                pass
        await _flash("长时间未在端口上检测到监听，请检查配置", error=True)

    async def _stop_http(*, interactive: bool = True) -> None:
        p = _http_proc_holder[0]
        if p is None or p.returncode is not None:
            if interactive:
                await _flash("没有由本工具启动的进程可关闭", error=True)
            return
        stop_ok = True
        try:
            p.terminate()
            try:
                await asyncio.wait_for(p.wait(), timeout=8.0)
            except asyncio.TimeoutError:
                p.kill()
                await p.wait()
        except ProcessLookupError:
            pass
        except Exception as ex:
            stop_ok = False
            if interactive:
                await _flash(f"关闭异常: {ex}", error=True)
            else:
                _append_http_log_line(f"[关闭异常] {ex}")
        await _drain_reader_tasks(_reader_tasks, per_task_timeout=6.0)
        _http_proc_holder[0] = None
        await asyncio.sleep(0)
        _append_http_log_line("[已关闭本工具启动的 HTTP 子进程]")
        _sync_ui()
        page.update()
        if interactive and stop_ok:
            await _flash("已关闭本工具启动的 HTTP 子进程")

    async def _toggle_http() -> None:
        p = _http_proc_holder[0]
        if p is not None and p.returncode is None:
            await _stop_http(interactive=True)
        else:
            await _start_http()

    async def _stop_as_studio(*, silent: bool = False, interactive: bool = True) -> None:
        p = _studio_proc_holder[0]
        if p is None or p.returncode is not None:
            if interactive and not silent:
                await _flash("没有由本工具启动的 Studio 进程可关闭", error=True)
            return
        stop_ok = True
        try:
            p.terminate()
            try:
                await asyncio.wait_for(p.wait(), timeout=8.0)
            except asyncio.TimeoutError:
                p.kill()
                await p.wait()
        except ProcessLookupError:
            pass
        except Exception as ex:
            stop_ok = False
            if interactive and not silent:
                await _flash(f"关闭 Studio 异常: {ex}", error=True)
            elif not silent:
                _append_studio_log_line(f"[结束进程异常] {ex}")
        await _drain_reader_tasks(_studio_reader_tasks, per_task_timeout=6.0)
        _studio_proc_holder[0] = None
        await asyncio.sleep(0)
        if not silent:
            _append_studio_log_line("[已关闭本工具拉起的 as_studio 进程]")
        _sync_ui()
        page.update()
        if interactive and not silent and stop_ok:
            await _flash("已关闭本工具拉起的 AgentScope Studio")

    async def _start_as_studio() -> None:
        sp = _studio_proc_holder[0]
        if sp is not None and sp.returncode is None:
            return
        if sp is not None:
            _studio_proc_holder[0] = None
        argv = _resolve_as_studio_argv()
        if not argv:
            await _flash(
                "未找到 as_studio（请 npm i -g @agentscope/studio）或 npx",
                error=True,
            )
            _append_studio_log_line(
                "未解析到启动命令，可设置环境变量 AGENTSCOPE_AS_STUDIO 指定完整命令"
            )
            page.update()
            return
        url = _agentscope_studio_url()
        _append_studio_log_line(
            f"启动: {' '.join(argv)}（就绪后一般为 {url}）…"
        )
        page.update()
        try:
            # 检查是否正在关闭程序，如果是则不创建管道以避免资源警告
            is_shutting_down = _close_shutdown_done[0]
            
            if sys.platform == "win32":
                proc = await asyncio.create_subprocess_exec(
                    *argv,
                    stdout=asyncio.subprocess.DEVNULL if is_shutting_down else asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    env=os.environ.copy(),
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    *argv,
                    stdout=asyncio.subprocess.DEVNULL if is_shutting_down else asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    env=os.environ.copy(),
                )
        except Exception as ex:
            await _flash(f"启动 as_studio 失败: {ex}", error=True)
            _append_studio_log_line(f"启动失败: {ex}")
            page.update()
            return
        _studio_proc_holder[0] = proc
        if proc.stdout is not None and not is_shutting_down:
            t = asyncio.create_task(_pump_studio_stdout(proc.stdout))
            _studio_reader_tasks.append(t)
        _sync_ui()
        page.update()
        await _flash("已启动 as_studio，浏览器通常会自动打开")

    async def _toggle_studio() -> None:
        """启动或关闭 AgentScope Studio"""
        p = _studio_proc_holder[0]
        if p is not None and p.returncode is None:
            await _stop_as_studio(interactive=True)
        else:
            await _start_as_studio()

    async def _clear_http_logs() -> None:
        """清除 HTTP 服务日志"""
        _http_log_deque.clear()
        http_log_field.value = ""
        page.update()
        await _flash("HTTP 服务日志已清除")

    async def _clear_studio_logs() -> None:
        """清除 AgentScope Studio 日志"""
        _studio_log_deque.clear()
        studio_log_field.value = ""
        page.update()
        await _flash("AgentScope Studio 日志已清除")

    async def _clear_all_logs() -> None:
        """清除所有日志"""
        _http_log_deque.clear()
        _studio_log_deque.clear()
        http_log_field.value = ""
        studio_log_field.value = ""
        page.update()
        await _flash("所有日志已清除")

    async def _shutdown_before_exit() -> None:
        """窗口/会话结束前停止本工具拉起的 HTTP（不弹交互提示）。"""
        if _close_shutdown_done[0]:
            return
        _close_shutdown_done[0] = True
        
        # 停止所有子进程
        await _stop_as_studio(silent=True, interactive=False)
        await _stop_http(interactive=False)
        
        # 等待所有读取任务完成，避免管道资源警告
        try:
            await asyncio.wait_for(
                asyncio.gather(*_reader_tasks, *_studio_reader_tasks, return_exceptions=True),
                timeout=3.0
            )
        except asyncio.TimeoutError:
            # 超时后强制取消所有任务
            for task in _reader_tasks + _studio_reader_tasks:
                if not task.done():
                    task.cancel()
            try:
                await asyncio.wait_for(
                    asyncio.gather(*_reader_tasks, *_studio_reader_tasks, return_exceptions=True),
                    timeout=1.0
                )
            except asyncio.TimeoutError:
                pass
        
        # 清理任务列表
        _reader_tasks.clear()
        _studio_reader_tasks.clear()
        
        # 给事件循环更多时间来清理资源
        await asyncio.sleep(0.2)
        
        # 在 Windows 上，强制垃圾回收以清理子进程传输对象
        if sys.platform == "win32":
            import gc
            gc.collect()
            await asyncio.sleep(0.1)

    async def _on_window_event(e: ft.WindowEvent) -> None:
        if e.type != ft.WindowEventType.CLOSE:
            return
        async with _window_close_lock:
            await _shutdown_before_exit()
            w = page.window
            if w is not None:
                w.prevent_close = False
                await w.close()

    async def _on_disconnect(_: object) -> None:
        await _shutdown_before_exit()

    # 先实例化再赋值：Flet @control 生成的 __init__ 在部分 Pylance 版本下会误报「无 content/icon 参数」
    toggle_btn = ft.FilledButton()
    toggle_btn.content = "启动 HTTP 服务"
    toggle_btn.icon = Icons.PLAY_ARROW
    toggle_btn.on_click = lambda _: page.run_task(_toggle_http)

    studio_btn = ft.FilledButton()
    studio_btn.content = "启动 AgentScope Studio"
    studio_btn.icon = Icons.PLAY_ARROW
    studio_btn.tooltip = (
        "与 HTTP 相同：一键启动/关闭本机 as_studio；"
        "就绪后一般会由 Studio 自动打开浏览器；无全局命令时尝试 npx -y @agentscope/studio。"
        "可用 AGENTSCOPE_AS_STUDIO 覆盖启动命令；AGENTSCOPE_STUDIO_URL 需与后端 agentscope.init 一致。"
    )
    studio_btn.on_click = lambda _: page.run_task(_toggle_studio)

    # 清除日志按钮
    clear_http_btn = ft.OutlinedButton()
    clear_http_btn.content = "清除 HTTP 日志"
    clear_http_btn.icon = Icons.CLEAR
    clear_http_btn.tooltip = "清除 HTTP 服务日志"
    clear_http_btn.on_click = lambda _: page.run_task(_clear_http_logs)

    clear_studio_btn = ft.OutlinedButton()
    clear_studio_btn.content = "清除 Studio 日志"
    clear_studio_btn.icon = Icons.CLEAR
    clear_studio_btn.tooltip = "清除 AgentScope Studio 日志"
    clear_studio_btn.on_click = lambda _: page.run_task(_clear_studio_logs)

    clear_all_btn = ft.OutlinedButton()
    clear_all_btn.content = "清除所有日志"
    clear_all_btn.icon = Icons.CLEAR_ALL
    clear_all_btn.tooltip = "清除所有日志"
    clear_all_btn.on_click = lambda _: page.run_task(_clear_all_logs)

    # 初始化 AgentScope 选择框
    init_agentscope_checkbox = ft.Checkbox(
        label="启动 HTTP 时初始化 AgentScope",
        value=True,
        tooltip="勾选后，启动 HTTP 服务时会自动启动 AgentScope Studio（如未启动）并初始化 AgentScope",
    )
    
    def on_checkbox_change(e):
        _init_agentscope_flag[0] = init_agentscope_checkbox.value or False
        page.update()
    
    init_agentscope_checkbox.on_change = on_checkbox_change

    _btn_holder[0] = toggle_btn
    _studio_btn_holder[0] = studio_btn
    _sync_ui()

    if page.window is not None:
        page.window.prevent_close = True
        page.window.on_event = _on_window_event
    page.on_disconnect = _on_disconnect

    page.add(
        ft.Text(value="本机 HTTP（uvicorn）", size=20, weight=ft.FontWeight.BOLD),
        ft.Text(
            value="仅管理由本窗口拉起的子进程；启动时会从 data/players.json 加载角色（由服务端 lifespan 执行）。",
            size=12,
            color=ft.Colors.GREY_700,
        ),
        hint,
        studio_hint,
        ft.Row(
            controls=[toggle_btn, studio_btn],
            spacing=12,
            wrap=True,
        ),
        init_agentscope_checkbox,
        ft.Row(
            controls=[clear_http_btn, clear_studio_btn, clear_all_btn],
            spacing=12,
            wrap=True,
        ),
        tip,
        ft.Row(
            expand=True,
            spacing=12,
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                value="服务端日志",
                                size=13,
                                weight=ft.FontWeight.W_600,
                            ),
                            http_log_field,
                        ],
                        expand=True,
                        spacing=6,
                    ),
                    expand=True,
                    border=ft.Border.all(1, ft.Colors.GREY_400),
                    border_radius=6,
                    padding=8,
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                value="AgentScope Studio 日志",
                                size=13,
                                weight=ft.FontWeight.W_600,
                            ),
                            studio_log_field,
                        ],
                        expand=True,
                        spacing=6,
                    ),
                    expand=True,
                    border=ft.Border.all(1, ft.Colors.GREY_400),
                    border_radius=6,
                    padding=8,
                ),
            ],
        ),
    )


if __name__ == "__main__":
    _view = os.getenv("FLET_ADMIN_VIEW", "flet").strip().lower()
    if _view in ("web", "browser", "web_browser"):
        _port = int(os.getenv("FLET_ADMIN_PORT", "8550"))
        ft.run(main, view=ft.AppView.WEB_BROWSER, port=_port)
    else:
        ft.run(main, view=ft.AppView.FLET_APP)
