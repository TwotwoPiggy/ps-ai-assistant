import { io } from "socket.io-client";
import { modalQueue } from "./modalQueue";
import { executeUXPTool } from "./uxpTools";

// Connect to the Python backend server
const SOCKET_URL = "http://127.0.0.1:18919";

// 检测是否为 UXP 环境
let isUXP = false;
try {
  // @ts-ignore
  isUXP = !!require('uxp');
} catch (e) {
  // 浏览器环境
}

export const socket = io(SOCKET_URL, {
    transports: isUXP ? ["websocket"] : ["websocket", "polling"],
    auth: {
        client_type: isUXP ? "uxp" : "web"
    }
});

socket.on("connect", () => {
    console.log(`Connected to PS AI Assistant server (${isUXP ? 'UXP Plugin' : 'Web Browser'})`);
});

socket.on("disconnect", () => {
    console.log("Disconnected from server");
});

// 在 UXP 插件内，挂载全局 Socket 事件监听，将工具调用派发至 ModalQueue
if (isUXP) {
  socket.on("execute_tool", async (data, callback) => {
    const { name, args } = data;
    console.log(`[PS-AI UXP] 接收到工具执行请求: ${name}`, args);
    
    try {
      // 所有的 PS 修改/修改操作都必须放入 ModalQueue 排队并在 executeAsModal 中安全运行
      const result = await modalQueue.enqueue(async () => {
        return await executeUXPTool(name, args);
      }, `AI: ${name}`);
      
      console.log(`[PS-AI UXP] 工具 ${name} 执行成功:`, result);
      if (typeof callback === 'function') {
        callback(result);
      }
    } catch (error: any) {
      console.error(`[PS-AI UXP] 工具 ${name} 执行发生错误:`, error);
      if (typeof callback === 'function') {
        callback({
          success: false,
          error: error.message || error.toString()
        });
      }
    }
  });
}

