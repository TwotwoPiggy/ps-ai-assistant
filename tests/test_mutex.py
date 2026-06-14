"""验证 Windows Mutex 单实例锁逻辑"""
import ctypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from launcher import acquire_single_instance, DEFAULT_HOST

print(">>> 测试 1: 首次获取应为唯一实例")
r1 = acquire_single_instance()
print(f"    acquire_single_instance() = {r1}")
assert r1 is True, "首次应该返回 True (唯一实例)"
print("    PASS")

print(">>> 测试 2: 同进程内再次调用应被拦截")
# 注意: 同进程内 CreateMutex 同名会返回 ERROR_ALREADY_EXISTS,
# 因为进程已持有该 mutex
r2 = acquire_single_instance()
print(f"    acquire_single_instance() = {r2}")
assert r2 is False, "同进程再次调用应返回 False (已存在)"
print("    PASS")

print()
print("=== Mutex 单实例逻辑验证通过 ===")
