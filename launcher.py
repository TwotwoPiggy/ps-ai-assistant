"""
PS AI Assistant — 服务启动器
================================
一键启动后端 (FastAPI + Socket.IO) 与前端 (Vite dev / 已构建 dist)，
并在 Windows 系统托盘显示一个带右键菜单的图标，支持快捷操作。

依赖:
    - 项目主依赖见 backend/requirements.txt
    - 托盘功能 (可选, 缺失时降级为纯命令行): pystray, Pillow

用法:
    start.bat              # 双击入口 (默认生产模式)
    python launcher.py     # 默认生产模式
    python launcher.py --dev   # 开发模式 (后端 + vite dev)
    python launcher.py --no-tray   # 禁用托盘, 仅命令行
    python launcher.py --no-browser   # 不自动打开浏览器
    python launcher.py --port 18919   # 指定后端端口
"""
from __future__ import annotations

import argparse
import ctypes
import logging
import os
import queue
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

# ==========================================
# 常量
# ==========================================
ROOT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"
LOGS_DIR = ROOT_DIR / "logs"
REQUIREMENTS_FILE = BACKEND_DIR / "requirements.txt"

DEFAULT_PORT = 18919
DEFAULT_HOST = "127.0.0.1"

# 日志器
logger = logging.getLogger("ps-launcher")


# ==========================================
# 日志配置
# ==========================================
def setup_logging():
    """同时输出日志到控制台与 logs/launcher.log"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "launcher.log"

    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # 文件 handler (覆盖旧文件, 避免无限增长)
    fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # 控制台 handler (UTF-8, 处理 Windows 控制台编码问题)
    try:
        if sys.platform == "win32":
            sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
            sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)


# ==========================================
# 依赖与环境预检查
# ==========================================
def check_python_version() -> bool:
    """检查 Python 版本 >= 3.10"""
    if sys.version_info < (3, 10):
        logger.error(f"Python 版本过低: {sys.version.split()[0]} (需要 >= 3.10)")
        return False
    logger.info(f"Python: {sys.version.split()[0]}  OK")
    return True


def check_node() -> bool:
    """检查 Node.js 是否可用 (仅开发模式或需构建时必须)"""
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            logger.info(f"Node.js: {r.stdout.strip()}  OK")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    logger.warning("未检测到 Node.js (开发模式或前端构建需要, 生产模式可忽略)")
    return False


def ensure_backend_deps() -> bool:
    """检查并尝试安装后端关键依赖 (fastapi, uvicorn, socketio)"""
    required = ["fastapi", "uvicorn", "socketio"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if not missing:
        logger.info("后端 Python 依赖: 完整  OK")
        return True

    logger.warning(f"缺少后端依赖: {', '.join(missing)}, 尝试自动安装...")
    if not REQUIREMENTS_FILE.exists():
        logger.error(f"未找到 requirements 文件: {REQUIREMENTS_FILE}")
        return False
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)]
        )
        # 二次验证
        for pkg in missing:
            __import__(pkg)
        logger.info("后端依赖安装完成  OK")
        return True
    except Exception as e:
        logger.error(f"自动安装后端依赖失败: {e}")
        logger.error(f"请手动运行: pip install -r {REQUIREMENTS_FILE}")
        return False


def ensure_tray_deps() -> bool:
    """检查托盘依赖 (pystray, Pillow); 缺失时返回 False 以触发降级"""
    try:
        import pystray  # noqa: F401
        from PIL import Image  # noqa: F401
        return True
    except ImportError:
        return False


def ensure_frontend_build() -> bool:
    """生产模式下检查 frontend/dist 是否已构建"""
    index_html = FRONTEND_DIST / "index.html"
    if index_html.exists():
        logger.info(f"前端构建产物: {FRONTEND_DIST}  OK")
        return True
    logger.warning(f"未找到前端构建产物: {index_html}")
    return False


def build_frontend() -> bool:
    """执行 npm run build 构建 frontend/dist"""
    if not FRONTEND_DIR.exists():
        logger.error(f"前端目录不存在: {FRONTEND_DIR}")
        return False
    if not (FRONTEND_DIR / "node_modules").exists():
        logger.info("首次构建, 安装前端依赖 (npm install)...")
        try:
            subprocess.check_call(["npm", "install"], cwd=str(FRONTEND_DIR))
        except Exception as e:
            logger.error(f"npm install 失败: {e}")
            return False
    logger.info("开始构建前端 (npm run build)...")
    try:
        subprocess.check_call(["npm", "run", "build"], cwd=str(FRONTEND_DIR))
        logger.info("前端构建完成  OK")
        return True
    except Exception as e:
        logger.error(f"前端构建失败: {e}")
        return False


# ==========================================
# 端口检测
# ==========================================
def is_port_in_use(port: int, host: str = DEFAULT_HOST) -> bool:
    """检测端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def is_server_running(port: int, host: str = DEFAULT_HOST) -> bool:
    """检测后端服务是否已经可以接收连接"""
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def find_available_port(start: int, host: str = DEFAULT_HOST, max_tries: int = 20) -> int:
    """从 start 开始递增查找可用端口"""
    for p in range(start, start + max_tries):
        if not is_port_in_use(p, host):
            return p
    return -1


# ==========================================
# 单实例锁 (防止双击/重复启动产生多个托盘)
# ==========================================
# 使用 Windows 命名 Mutex: 进程退出或崩溃时 OS 自动释放, 不会死锁.
_single_instance_mutex = None

def acquire_single_instance() -> bool:
    """尝试获取单实例锁. 返回 True 表示当前是唯一实例.

    若已有实例在运行则返回 False, 调用方应直接退出.
    非 Windows 平台跳过检查 (始终返回 True).
    """
    global _single_instance_mutex
    if os.name != "nt":
        return True
    try:
        # CreateMutex: 返回句柄; 若 mutex 已存在, GetLastError 返回 ERROR_ALREADY_EXISTS (183)
        GENERIC_ACCESS = 0x1F0001  # SYNCHRONIZE | STANDARD_RIGHTS_REQUIRED
        mutex_name = "Global\\PSAI-Launcher-SingleInstance"
        handle = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
        last_error = ctypes.windll.kernel32.GetLastError()
        if last_error == 183:  # ERROR_ALREADY_EXISTS
            # 已有实例, 关闭本进程持有的多余句柄并返回 False
            ctypes.windll.kernel32.CloseHandle(handle)
            return False
        # 持有句柄保活, 进程退出时 OS 自动回收
        _single_instance_mutex = handle
        return True
    except Exception as e:
        # 互斥机制失败时不应阻断启动, 仅记录告警
        logger.warning(f"单实例锁获取异常 (忽略): {e}")
        return True


# ==========================================
# 进程管理器
# ==========================================
class ProcessManager:
    """统一管理后端 / 前端子进程, 保证退出时全部清理"""

    def __init__(self):
        self._procs: list[subprocess.Popen] = []
        self._lock = threading.Lock()
        self._stopped = False

    def spawn(self, name: str, cmd: list[str], cwd: Path | None = None,
              env: dict | None = None) -> subprocess.Popen | None:
        """启动子进程并接管 stdout/stderr 流式转发到日志"""
        creationflags = 0
        if os.name == "nt":
            # CREATE_NEW_PROCESS_GROUP: 允许独立发送 CTRL_BREAK 信号
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd) if cwd else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
                creationflags=creationflags,
            )
        except FileNotFoundError as e:
            logger.error(f"无法启动 {name}: {e} (命令不存在: {cmd[0]})")
            return None
        except Exception as e:
            logger.error(f"无法启动 {name}: {e}")
            return None

        with self._lock:
            self._procs.append(proc)

        # 启动流式输出转发线程
        t = threading.Thread(
            target=self._stream_output,
            args=(proc, name),
            daemon=True,
        )
        t.start()
        logger.info(f"[{name}] 已启动 (PID {proc.pid})")
        return proc

    def _stream_output(self, proc: subprocess.Popen, name: str):
        """将子进程输出逐行写入 logger"""
        try:
            for line in iter(proc.stdout.readline, ""):
                line = line.rstrip()
                if line:
                    logger.info(f"[{name}] {line}")
        except Exception:
            pass

    def wait_ready(self, port: int, host: str = DEFAULT_HOST, timeout: int = 25) -> bool:
        """轮询等待后端端口可连接"""
        logger.info(f"等待后端就绪 ({host}:{port})...")
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._stopped:
                return False
            try:
                with socket.create_connection((host, port), timeout=1):
                    logger.info("后端已就绪  OK")
                    return True
            except OSError:
                time.sleep(0.5)
        logger.error(f"后端在 {timeout}s 内未就绪")
        return False

    def is_running(self) -> bool:
        """是否有任一子进程仍在运行"""
        if self._stopped:
            return False
        with self._lock:
            for proc in self._procs:
                if proc.poll() is None:
                    return True
        return False

    def stop_all(self):
        """优雅停止所有子进程"""
        if self._stopped:
            return
        self._stopped = True
        logger.info("正在停止所有子进程...")
        with self._lock:
            procs = list(reversed(self._procs))  # 先停前端

        for proc in procs:
            if proc.poll() is not None:
                continue
            try:
                if os.name == "nt":
                    # Windows: 用 taskkill 杀整个进程树 (子进程也包含)
                    subprocess.run(
                        ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                        capture_output=True,
                    )
                else:
                    proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            except Exception as e:
                logger.warning(f"停止 PID {proc.pid} 时出错: {e}")
        logger.info("所有子进程已停止")


# ==========================================
# 启动器主类
# ==========================================
class Launcher:
    def __init__(self, args):
        self.args = args
        self.mode = "dev" if args.dev else "prod"
        self.port = args.port
        self.host = DEFAULT_HOST
        self.pm = ProcessManager()
        self.use_tray = (not args.no_tray) and ensure_tray_deps()
        self._tray_queue: "queue.Queue[str]" = queue.Queue()
        self._exit_event = threading.Event()

    # ---------------- 主流程 ----------------
    def run(self) -> int:
        logger.info("=" * 50)
        logger.info(f"PS AI Assistant 启动器 — 模式: {self.mode.upper()}")
        logger.info("=" * 50)

        # 1. 环境预检
        if not check_python_version():
            return 1
        ensure_backend_deps()  # 关键依赖必须装上; 安装失败仍尝试启动, 由用户决定

        if self.mode == "dev":
            check_node()
        else:
            if not ensure_frontend_build():
                # 生产模式自动尝试构建
                ans = self._ask("前端 dist 缺失, 是否立即构建? (Y/n)")
                if ans in ("", "y", "Y"):
                    if not build_frontend():
                        return 1
                else:
                    logger.warning("无前端 dist, 后端仍会启动但页面不可访问")

        # 2. 端口检测
        if not self._resolve_port():
            return 1

        # 3. 启动服务
        self._start_services()

        # 4. 等待后端就绪并打开浏览器
        ready = self.pm.wait_ready(self.port, self.host)
        if ready and not self.args.no_browser:
            url = f"http://{self.host}:{self.port}"
            logger.info(f"正在打开浏览器: {url}")
            try:
                webbrowser.open(url)
            except Exception as e:
                logger.warning(f"打开浏览器失败: {e}")

        # 5. 进入托盘或命令行模式
        if self.use_tray:
            self._run_tray()
        else:
            if not ensure_tray_deps():
                logger.info("提示: 安装 pystray + Pillow 可启用托盘图标")
                logger.info("      pip install pystray Pillow")
            self._run_cli()

        return 0

    # ---------------- 端口策略 ----------------
    def _resolve_port(self) -> bool:
        """
        生产模式: 前端硬编码 18919, 换端口会导致前端连不上, 因此
                  被占用时报错并提示, 不自动换。
        开发模式: vite proxy 可动态适配, 自动查找可用端口。
        """
        if not is_port_in_use(self.port, self.host):
            logger.info(f"端口 {self.port} 可用  OK")
            return True

        logger.warning(f"端口 {self.port} 已被占用")
        if self.mode == "prod":
            logger.error("生产模式下端口固定为 18919 (前端硬编码), 无法自动切换。")
            logger.error(f"请关闭占用 {self.port} 的程序, 或使用 --port 指定其他端口")
            logger.error("(注意: 切换端口会导致前端连不上后端)")
            return False
        else:
            new_port = find_available_port(self.port + 1, self.host)
            if new_port == -1:
                logger.error("未找到可用端口")
                return False
            logger.info(f"开发模式: 自动切换到端口 {new_port}")
            self.port = new_port
            return True

    # ---------------- 启动服务 ----------------
    def _start_services(self):
        # 后端: 通过 python -m backend.server, 通过 PORT 环境变量传端口
        env = os.environ.copy()
        env["PORT"] = str(self.port)
        self.pm.spawn(
            "backend",
            [sys.executable, "-m", "backend.server"],
            cwd=ROOT_DIR,
            env=env,
        )

        if self.mode == "dev":
            # 前端 dev server; 端口固定让 vite 自选 (默认 5173), 开发者自行访问
            self.pm.spawn(
                "frontend",
                ["npm", "run", "dev"],
                cwd=FRONTEND_DIR,
            )

    # ---------------- 托盘模式 ----------------
    def _run_tray(self):
        logger.info("系统托盘已启用 (右键查看菜单, 关闭将通过菜单退出)")
        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError:
            logger.warning("托盘依赖加载失败, 降级为命令行模式")
            return self._run_cli()

        # 服务运行状态: 'running' | 'stopped'
        # pystray 菜单项的文本/启用状态可用可调用对象实现动态刷新
        self.service_state = "running"

        def on_open(icon, item):
            if self.service_state == "running":
                webbrowser.open(f"http://{self.host}:{self.port}")

        def on_restart(icon, item):
            def _task():
                logger.info("[托盘] 请求重启服务...")
                self.pm.stop_all()
                self.pm = ProcessManager()
                time.sleep(1)
                self._start_services()
                ready = self.pm.wait_ready(self.port, self.host)
                self.service_state = "running" if ready else "stopped"
                self._update_tray_tooltip(icon)
                icon.update_menu()
            threading.Thread(target=_task, daemon=True).start()

        def on_stop(icon, item):
            def _task():
                logger.info("[托盘] 请求停止服务...")
                self.pm.stop_all()
                self.pm = ProcessManager()
                self.service_state = "stopped"
                self._update_tray_tooltip(icon)
                icon.update_menu()
            threading.Thread(target=_task, daemon=True).start()

        def on_start(icon, item):
            def _task():
                logger.info("[托盘] 请求启动服务...")
                self._start_services()
                ready = self.pm.wait_ready(self.port, self.host)
                self.service_state = "running" if ready else "stopped"
                self._update_tray_tooltip(icon)
                if ready and not self.args.no_browser:
                    webbrowser.open(f"http://{self.host}:{self.port}")
                icon.update_menu()
            threading.Thread(target=_task, daemon=True).start()

        def on_quit(icon, item):
            logger.info("[托盘] 用户请求退出")
            icon.stop()
            self._exit_event.set()

        menu = pystray.Menu(
            pystray.MenuItem(
                lambda item: f"PS AI Assistant ({self.mode.upper()} :{self.port})",
                None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("打开浏览器", on_open, default=True),
            pystray.MenuItem("启动服务", on_start, enabled=lambda item: self.service_state == "stopped"),
            pystray.MenuItem("停止服务", on_stop, enabled=lambda item: self.service_state == "running"),
            pystray.MenuItem("重启服务", on_restart, enabled=lambda item: self.service_state == "running"),
            pystray.MenuItem("查看日志", lambda *_: self._open_log()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", on_quit),
        )

        icon = pystray.Icon("ps-ai-assistant", self._make_tray_image(),
                            self._tray_tooltip(), menu)

        # 若托盘因主线程退出而结束, 也确保子进程被清理
        try:
            icon.run()
        finally:
            self.pm.stop_all()

    def _tray_tooltip(self) -> str:
        """根据服务状态生成托盘提示文本"""
        if getattr(self, "service_state", "running") == "running":
            return f"PS AI Assistant (运行中 :{self.port})"
        return f"PS AI Assistant (已停止 :{self.port})"

    def _update_tray_tooltip(self, icon):
        """更新托盘 hover 提示文本"""
        try:
            icon.title = self._tray_tooltip()
        except Exception:
            pass

    def _make_tray_image(self):
        """生成一个简洁的 'PS' 图标 (64x64)"""
        from PIL import Image, ImageDraw
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # 圆角背景: 深蓝紫
        d.ellipse([2, 2, size - 2, size - 2], fill=(56, 96, 255, 255))
        # 文字 (粗略居中)
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("arial.ttf", 28)
        except Exception:
            font = ImageFont.load_default()
        text = "PS"
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]),
               text, fill=(255, 255, 255, 255), font=font)
        return img

    def _open_log(self):
        log_file = LOGS_DIR / "launcher.log"
        if log_file.exists():
            os.startfile(str(log_file))

    # ---------------- 命令行模式 ----------------
    def _run_cli(self):
        logger.info("命令行模式 (Ctrl+C 退出)")
        try:
            while not self._exit_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到 Ctrl+C, 正在退出...")
        finally:
            self.pm.stop_all()

    # ---------------- 小工具 ----------------
    def _ask(self, prompt: str) -> str:
        try:
            return input(f"{prompt} ").strip()
        except (EOFError, KeyboardInterrupt):
            return "n"


# ==========================================
# 入口
# ==========================================
def main() -> int:
    # Windows: 让控制台支持 ANSI + UTF-8 输出
    if os.name == "nt":
        try:
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="PS AI Assistant 服务启动器"
    )
    parser.add_argument("--dev", action="store_true", help="开发模式 (后端 + vite dev)")
    parser.add_argument("--no-tray", action="store_true", help="禁用系统托盘, 仅命令行")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"后端端口 (默认 {DEFAULT_PORT}, 生产模式建议保持)")
    args = parser.parse_args()

    setup_logging()

    # 单实例检查: 防止双击/重复启动产生多个托盘图标
    if not acquire_single_instance():
        msg = "PS AI Assistant 已在运行中 (托盘已有图标)"
        logger.warning(msg)
        
        # 仅当后端服务已经可以接收连接时，才为其打开浏览器。
        # 避免用户短时间内多次双击启动脚本，导致前一个实例还在启动中（未打开浏览器）
        # 而后一个实例立刻打开了浏览器，最终出现两个前端页面的问题。
        if is_server_running(args.port, DEFAULT_HOST):
            # 给用户友好反馈: 打开浏览器到现有实例, 而非静默退出
            try:
                url = f"http://{DEFAULT_HOST}:{args.port}"
                webbrowser.open(url)
            except Exception:
                pass
            # 静默模式下弹窗提示 (VBS 启动无控制台可见)
            if os.environ.get("PSAI_SILENT") == "1":
                try:
                    ctypes.windll.user32.MessageBoxW(
                        0, msg + "\n\n已为你打开浏览器。", "PS AI Assistant", 0x40)
                except Exception:
                    pass
        else:
            logger.info("检测到主实例正在启动中，当前实例将静默退出。主实例稍后会自动打开浏览器。")
            
        return 0

    launcher = Launcher(args)
    try:
        return launcher.run()
    except Exception as e:
        logger.exception(f"启动器异常: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
