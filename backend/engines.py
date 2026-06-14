from abc import ABC, abstractmethod
import asyncio
from backend.tools import registry, PhotoshopContext

class PSEngineBase(ABC):
    """Photoshop 执行引擎基类"""
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, args: dict) -> dict:
        """异步执行指定的 Photoshop 工具操作"""
        pass


class COMEngine(PSEngineBase):
    """COM 接口执行引擎，使用 win32com 与本地 Photoshop 通信"""
    
    def __init__(self):
        self.ctx = PhotoshopContext()

    async def execute_tool(self, tool_name: str, args: dict) -> dict:
        # 兼容现有的同步 COM 工具调用，仍然在主线程同步执行（由于 win32com 的线程模型限制）
        # 返回结果格式应与 registry.execute_tool 保持一致
        return registry.execute_tool(tool_name, args, self.ctx)


class UXPEngine(PSEngineBase):
    """UXP 接口执行引擎，通过 Socket.IO 发送指令到 Photoshop 内部的 UXP 插件执行"""
    
    def __init__(self, sio, sid: str):
        self.sio = sio
        self.sid = sid

    async def execute_tool(self, tool_name: str, args: dict) -> dict:
        try:
            # 向对应的 UXP 客户端派发 execute_tool 事件，挂起并等待前端响应（ack）
            # 设置 60 秒超时，防止因 PS 界面卡死或弹窗导致无限期挂起
            result = await self.sio.call(
                'execute_tool',
                {
                    "name": tool_name,
                    "args": args
                },
                to=self.sid,
                timeout=60.0
            )
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"UXP 引擎执行出错或响应超时: {str(e)}"
            }
