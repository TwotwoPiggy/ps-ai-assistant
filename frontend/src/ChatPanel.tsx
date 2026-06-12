import { useEffect, useRef, useState } from "react";
import { socket } from "./socket";
import "./styles.css";

interface Message {
    id: string;
    role: "user" | "assistant" | "system";
    text: string;
    status?: string;
    timestamp: number;
}

export function ChatPanel() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState("");
    const [apiKey, setApiKey] = useState("");
    const [model, setModel] = useState("gemini-2.5-flash");
    const [hasKey, setHasKey] = useState(false);
    const [isConfiguring, setIsConfiguring] = useState(false);
    const [statusText, setStatusText] = useState("");
    const [aiStatus, setAiStatus] = useState<"idle" | "thinking" | "executing">("idle");
    const chatEndRef = useRef<HTMLDivElement>(null);

    // Initial check for API key
    useEffect(() => {
        // Fetch config
        socket.emit("ai_config", { action: "get" }, (res: any) => {
            if (res) {
                setHasKey(res.has_key);
                if (res.gemini_api_key) {
                    setApiKey(res.gemini_api_key);
                }
                if (res.model) {
                    setModel(res.model);
                }
            }
        });

        // Listen for AI responses and statuses
        const handleResponse = (data: { response: string }) => {
            setMessages(prev => [
                ...prev,
                {
                    id: Math.random().toString(36).substring(7),
                    role: "assistant",
                    text: data.response,
                    timestamp: Date.now()
                }
            ]);
            setAiStatus("idle");
            setStatusText("");
        };

        const handleStatus = (data: { status: "thinking" | "executing" | "done"; message: string }) => {
            if (data.status === "done") {
                setAiStatus("idle");
                setStatusText("");
            } else {
                setAiStatus(data.status);
                setStatusText(data.message);
            }
        };

        socket.on("ai_chat_response", handleResponse);
        socket.on("ai_chat_status", handleStatus);

        return () => {
            socket.off("ai_chat_response", handleResponse);
            socket.off("ai_chat_status", handleStatus);
        };
    }, []);

    // Scroll to bottom when messages update
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, aiStatus, statusText]);

    const handleSend = () => {
        if (!inputValue.trim()) return;

        const userMsg = inputValue;
        setInputValue("");

        // Add user message to UI
        setMessages(prev => [
            ...prev,
            {
                id: Math.random().toString(36).substring(7),
                role: "user",
                text: userMsg,
                timestamp: Date.now()
            }
        ]);

        setAiStatus("thinking");
        setStatusText("AI 正在思考中...");

        // Send to backend
        socket.emit("ai_chat", { message: userMsg });
    };

    const handleClearHistory = () => {
        if (window.confirm("确定要清空当前的会话历史记录吗？")) {
            socket.emit("ai_clear_history", {}, () => {
                setMessages([]);
            });
            // 兜底清空
            setMessages([]);
        }
    };

    const handleSaveConfig = () => {
        socket.emit("ai_config", { action: "save", gemini_api_key: apiKey, model }, (res: any) => {
            if (res && res.success) {
                setHasKey(res.has_key);
                if (res.model) setModel(res.model);
                setIsConfiguring(false);
                // System notification message
                setMessages(prev => [
                    ...prev,
                    {
                        id: Math.random().toString(36).substring(7),
                        role: "system",
                        text: "Gemini API Key 配置保存成功，AI 操作助手功能已启用。",
                        timestamp: Date.now()
                    }
                ]);
            } else {
                alert("API Key 保存失败，请重试。");
            }
        });
    };

    return (
        <div className="sdppp-ai-chat-panel">
            {/* API Config Bar */}
            <div className="sdppp-ai-config-header">
                <div className="sdppp-ai-config-status">
                    <span className={`status-dot ${hasKey ? "active" : ""}`}></span>
                    <span>{hasKey ? "AI 助手已激活" : "AI 助手未配置"}</span>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button 
                        className="sdppp-ai-clear-btn"
                        onClick={handleClearHistory}
                        title="清空后端的会话记忆，避免历史数据过大导致报错"
                    >
                        清空历史
                    </button>
                    <button 
                        className="sdppp-ai-config-toggle"
                        onClick={() => setIsConfiguring(!isConfiguring)}
                    >
                        {isConfiguring ? "收起配置" : "配置 Key"}
                    </button>
                </div>
            </div>

            {isConfiguring && (
                <div className="sdppp-ai-config-body">
                    <label>请输入您的 Gemini API Key:</label>
                    <div className="sdppp-ai-config-input-row">
                        <input
                            type="password"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder="保留为空以使用现有 Key"
                            className="sdppp-ai-key-input"
                        />
                    </div>
                    <label>选择模型:</label>
                    <div className="sdppp-ai-config-input-row">
                        <select 
                            value={model} 
                            onChange={(e) => setModel(e.target.value)}
                            className="sdppp-ai-model-select"
                        >
                            <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                            <option value="gemini-3-flash">Gemini 3 Flash</option>
                            <option value="gemini-3.5-flash">Gemini 3.5 Flash</option>
                            <option value="gemini-3.1-flash-lite">Gemini 3.1 Flash Lite</option>
                            <option value="gemma-4-31b-it">Gemma-4-31b-it</option>
                            <option value="gemma-4-26b-a4b-it">Gemma-4-26b-a4b-it</option>
                        </select>
                        <button onClick={handleSaveConfig} className="sdppp-ai-save-btn">
                            保存
                        </button>
                    </div>
                    <span className="sdppp-ai-config-tip">
                        注意：您的 API Key 将被安全地保存在本地 Python 服务端配置文件中，不会上传到云端。
                    </span>
                </div>
            )}

            {/* Messages Area */}
            <div className="sdppp-ai-chat-messages">
                {messages.length === 0 && (
                    <div className="sdppp-ai-welcome-box">
                        <div className="sdppp-ai-logo-glow">✦</div>
                        <h3>欢迎使用 Photoshop AI 助手</h3>
                        <p>您可以使用自然语言直接控制 Photoshop 进行图层操作和画面修改。</p>
                        <div className="sdppp-ai-examples">
                            <h4>您可以尝试输入：</h4>
                            <ul>
                                <li>“帮我新建一个叫'高光图层'的图层，并不透明度设为80%”</li>
                                <li>“把所有隐藏的图层都显示出来”</li>
                                <li>“把画面整体调亮一点点”</li>
                                <li>“新建一个叫'背景模糊'的图层，然后把它移到最底层”</li>
                            </ul>
                        </div>
                    </div>
                )}

                {messages.map((msg) => (
                    <div key={msg.id} className={`sdppp-chat-msg-row ${msg.role}`}>
                        <div className="sdppp-chat-avatar">
                            {msg.role === "user" ? "👤" : msg.role === "system" ? "⚙️" : "✦"}
                        </div>
                        <div className="sdppp-chat-bubble">
                            {msg.text}
                        </div>
                    </div>
                ))}

                {aiStatus !== "idle" && (
                    <div className={`sdppp-chat-msg-row assistant loading`}>
                        <div className="sdppp-chat-avatar pulsating">✦</div>
                        <div className="sdppp-chat-bubble loading-bubble">
                            <div className="pulsating-ring"></div>
                            <span className="sdppp-status-msg">{statusText}</span>
                        </div>
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>

            {/* Input Area */}
            <div className="sdppp-ai-chat-input-bar">
                <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter") handleSend();
                    }}
                    placeholder={hasKey ? "请输入您对 Photoshop 的指令..." : "请先配置 API Key 以开始聊天"}
                    disabled={!hasKey || aiStatus !== "idle"}
                    className="sdppp-ai-main-input"
                />
                <button 
                    onClick={handleSend}
                    disabled={!hasKey || aiStatus !== "idle" || !inputValue.trim()}
                    className="sdppp-ai-send-btn"
                >
                    发送
                </button>
            </div>
        </div>
    );
}
