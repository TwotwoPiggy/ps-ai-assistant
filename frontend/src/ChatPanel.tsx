import { useEffect, useRef, useState } from "react";
import { socket } from "./socket";
import "./styles.css";

interface Message {
    id: string;
    role: "user" | "assistant" | "system";
    text: string;
    status?: string;
    timestamp: number;
    thinkingText?: string;
}

interface ProviderConfig {
    api_key: string;
    base_url: string;
    model: string;
}

interface ThinkingBoxProps {
    text: string;
}

function ThinkingBox({ text }: ThinkingBoxProps) {
    const [isOpen, setIsOpen] = useState(true);
    if (!text) return null;
    return (
        <div className="sdppp-ai-thinking-box">
            <div className="sdppp-ai-thinking-header" onClick={() => setIsOpen(!isOpen)}>
                <div className="sdppp-ai-thinking-title">
                    <span className="thinking-icon">💭</span>
                    <span>思考过程</span>
                </div>
                <div className={`sdppp-ai-thinking-arrow ${isOpen ? "open" : ""}`}>
                    ▾
                </div>
            </div>
            {isOpen && (
                <div className="sdppp-ai-thinking-content">
                    {text}
                </div>
            )}
        </div>
    );
}

export function ChatPanel() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState("");
    const [currentProvider, setCurrentProvider] = useState("gemini");
    const [providers, setProviders] = useState<Record<string, ProviderConfig>>({
        gemini: { api_key: "", base_url: "", model: "gemini-2.5-flash" },
        deepseek: { api_key: "", base_url: "", model: "deepseek-chat" },
        qwen: { api_key: "", base_url: "", model: "qwen-plus" },
        mimo: { api_key: "", base_url: "", model: "mimo-v1" },
        custom: { api_key: "", base_url: "", model: "" }
    });
    const thinkingRef = useRef("");
    const [currentThinking, setCurrentThinking] = useState("");
    const [hasKey, setHasKey] = useState(false);
    const [isConfiguring, setIsConfiguring] = useState(false);
    const [statusText, setStatusText] = useState("");
    const [aiStatus, setAiStatus] = useState<"idle" | "thinking" | "executing">("idle");
    const chatEndRef = useRef<HTMLDivElement>(null);

    // Initial check for API key
    useEffect(() => {
        // Fetch config
        socket.emit("ai_config", { action: "get" }, (res: any) => {
            if (res && res.success) {
                setHasKey(res.has_key);
                if (res.current_provider) {
                    setCurrentProvider(res.current_provider);
                }
                if (res.providers) {
                    setProviders(res.providers);
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
                    thinkingText: thinkingRef.current,
                    timestamp: Date.now()
                }
            ]);
            setAiStatus("idle");
            setStatusText("");
            thinkingRef.current = "";
            setCurrentThinking("");
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

        const handleThinking = (data: { word: string }) => {
            thinkingRef.current += data.word;
            setCurrentThinking(thinkingRef.current);
        };

        socket.on("ai_chat_response", handleResponse);
        socket.on("ai_chat_status", handleStatus);
        socket.on("ai_chat_thinking", handleThinking);

        return () => {
            socket.off("ai_chat_response", handleResponse);
            socket.off("ai_chat_status", handleStatus);
            socket.off("ai_chat_thinking", handleThinking);
        };
    }, []);

    // Scroll to bottom when messages update
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, aiStatus, statusText, currentThinking]);

    const handleSend = () => {
        if (!inputValue.trim()) return;

        const userMsg = inputValue;
        setInputValue("");
        
        // 重置思维链缓存
        thinkingRef.current = "";
        setCurrentThinking("");

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

    const updateProviderField = (provider: string, field: keyof ProviderConfig, value: string) => {
        setProviders(prev => ({
            ...prev,
            [provider]: {
                ...prev[provider],
                [field]: value
            }
        }));
    };

    const handleKeyFocus = (provider: string, currentVal: string) => {
        if (currentVal && currentVal.includes("****")) {
            updateProviderField(provider, "api_key", "");
        }
    };

    const handleSaveConfig = () => {
        socket.emit("ai_config", {
            action: "save",
            current_provider: currentProvider,
            providers: providers
        }, (res: any) => {
            if (res && res.success) {
                setHasKey(res.has_key);
                setIsConfiguring(false);
                // System notification message
                setMessages(prev => [
                    ...prev,
                    {
                        id: Math.random().toString(36).substring(7),
                        role: "system",
                        text: `AI 配置保存成功，当前 Provider 已切换为 ${currentProvider}。`,
                        timestamp: Date.now()
                    }
                ]);
            } else {
                alert("配置保存失败，请检查参数后重试。");
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
                    <label>选择 AI 提供商 (Provider):</label>
                    <div className="sdppp-ai-config-input-row">
                        <select 
                            value={currentProvider} 
                            onChange={(e) => setCurrentProvider(e.target.value)}
                            className="sdppp-ai-provider-select"
                        >
                            <option value="gemini">Gemini (Google)</option>
                            <option value="deepseek">DeepSeek</option>
                            <option value="qwen">通义千问 (Qwen)</option>
                            <option value="mimo">MiMo (小米)</option>
                            <option value="custom">自定义 OpenAI 兼容</option>
                        </select>
                    </div>

                    <label>API Key:</label>
                    <div className="sdppp-ai-config-input-row">
                        <input
                            type="password"
                            value={providers[currentProvider]?.api_key || ""}
                            onChange={(e) => updateProviderField(currentProvider, "api_key", e.target.value)}
                            onFocus={() => handleKeyFocus(currentProvider, providers[currentProvider]?.api_key || "")}
                            placeholder="保留为空以使用现有 Key"
                            className="sdppp-ai-key-input"
                        />
                    </div>

                    {(currentProvider === "custom" || currentProvider === "mimo") && (
                        <>
                            <label>接口地址 (Base URL):</label>
                            <div className="sdppp-ai-config-input-row">
                                <input
                                    type="text"
                                    value={providers[currentProvider]?.base_url || ""}
                                    onChange={(e) => updateProviderField(currentProvider, "base_url", e.target.value)}
                                    placeholder={currentProvider === "mimo" ? "http://10.0.0.x:8000/v1" : "https://api.yourprovider.com/v1"}
                                    className="sdppp-ai-base-url-input"
                                />
                            </div>
                        </>
                    )}

                    <label>选择/输入模型 (Model):</label>
                    <div className="sdppp-ai-config-input-row">
                        {currentProvider === "custom" ? (
                            <input
                                type="text"
                                value={providers[currentProvider]?.model || ""}
                                onChange={(e) => updateProviderField(currentProvider, "model", e.target.value)}
                                placeholder="例如: gpt-4o"
                                className="sdppp-ai-model-input"
                            />
                        ) : (
                            <select 
                                value={providers[currentProvider]?.model || ""} 
                                onChange={(e) => updateProviderField(currentProvider, "model", e.target.value)}
                                className="sdppp-ai-model-select"
                            >
                                {currentProvider === "gemini" && (
                                    <>
                                        <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                                        <option value="gemini-3-flash">Gemini 3 Flash</option>
                                        <option value="gemini-3.5-flash">Gemini 3.5 Flash</option>
                                        <option value="gemini-3.1-flash-lite">Gemini 3.1 Flash Lite</option>
                                        <option value="gemma-4-31b-it">Gemma-4-31b-it</option>
                                        <option value="gemma-4-26b-a4b-it">Gemma-4-26b-a4b-it</option>
                                    </>
                                )}
                                {currentProvider === "deepseek" && (
                                    <>
                                        <option value="deepseek-chat">deepseek-chat (V3)</option>
                                        <option value="deepseek-reasoner">deepseek-reasoner (R1)</option>
                                    </>
                                )}
                                {currentProvider === "qwen" && (
                                    <>
                                        <option value="qwen-plus">qwen-plus</option>
                                        <option value="qwen-max">qwen-max</option>
                                        <option value="qwen-vl-plus">qwen-vl-plus</option>
                                    </>
                                )}
                                {currentProvider === "mimo" && (
                                    <>
                                        <option value="mimo-v1">mimo-v1</option>
                                    </>
                                )}
                            </select>
                        )}
                        <button onClick={handleSaveConfig} className="sdppp-ai-save-btn">
                            保存配置
                        </button>
                    </div>
                    <span className="sdppp-ai-config-tip">
                        注意：您的配置及 API Key 将安全地保存在本地服务端，不会上传到公共云端。
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
                        <div className="sdppp-chat-bubble-wrapper">
                            {msg.role === "assistant" && msg.thinkingText && (
                                <ThinkingBox text={msg.thinkingText} />
                            )}
                            <div className="sdppp-chat-bubble">
                                {msg.text}
                            </div>
                        </div>
                    </div>
                ))}

                {aiStatus !== "idle" && (
                    <div className={`sdppp-chat-msg-row assistant loading`}>
                        <div className="sdppp-chat-avatar pulsating">✦</div>
                        <div className="sdppp-chat-bubble-wrapper">
                            {currentThinking && (
                                <ThinkingBox text={currentThinking} />
                            )}
                            <div className="sdppp-chat-bubble loading-bubble">
                                <div className="pulsating-ring"></div>
                                <span className="sdppp-status-msg">{statusText}</span>
                            </div>
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
