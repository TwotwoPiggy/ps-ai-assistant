"""验证托盘停止/启动逻辑的状态切换正确性"""
import sys, time, socket, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.argv = ['launcher.py', '--no-tray', '--no-browser', '--port', '18950']
from launcher import Launcher, setup_logging
setup_logging()


def port_up(p):
    try:
        with socket.create_connection(('127.0.0.1', p), timeout=1):
            return True
    except OSError:
        return False


class FakeIcon:
    def __init__(self):
        self.menu_updated = 0
        self.title = ""

    def update_menu(self):
        self.menu_updated += 1


args = argparse.Namespace(dev=False, no_tray=True, no_browser=True, port=18950)
L = Launcher(args)
L.use_tray = False


def step(msg):
    print(f"\n>>> {msg}", flush=True)


step("1. 初始启动服务")
L._start_services()
ready1 = L.pm.wait_ready(18950, timeout=20)
L.service_state = "running" if ready1 else "stopped"
print(f"   状态={L.service_state} 端口监听={port_up(18950)}", flush=True)
assert L.service_state == "running" and port_up(18950), "启动失败"

step("2. 模拟点击[停止服务]")
icon = FakeIcon()
L.pm.stop_all()
L.pm = type(L.pm)()
L.service_state = "stopped"
icon.update_menu()
L._update_tray_tooltip(icon)
time.sleep(1)
print(f"   状态={L.service_state} 端口监听={port_up(18950)} tooltip={icon.title!r}", flush=True)
assert L.service_state == "stopped", "停止后状态错误"
assert not port_up(18950), "停止后端口仍监听!"

step("3. 模拟点击[启动服务]")
L._start_services()
ready3 = L.pm.wait_ready(18950, timeout=20)
L.service_state = "running" if ready3 else "stopped"
icon.update_menu()
L._update_tray_tooltip(icon)
print(f"   状态={L.service_state} 端口监听={port_up(18950)} tooltip={icon.title!r}", flush=True)
assert L.service_state == "running" and port_up(18950), "重新启动失败"

print("\n=== 全部断言通过: 停止/启动状态切换正确 ===", flush=True)
L.pm.stop_all()
