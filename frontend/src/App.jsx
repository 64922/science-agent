import { useState, useEffect, useRef } from "react";

function App() {
  const [backendStatus, setBackendStatus] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => setBackendStatus(data))
      .catch(() => setBackendStatus({ status: "disconnected" }));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { id: Date.now(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "demo_user_a",
          message: text,
          scenario_id: "popular_science",
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `请求失败 (${res.status})`);
      }

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { id: Date.now(), role: "assistant", content: data.reply },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="app">
      <header className="chat-header">
        <h1>知己科教 Agent</h1>
        <div className="status-bar">
          <span className="status-dot" data-status={backendStatus?.status} />
          <span>
            {backendStatus
              ? backendStatus.status === "ok"
                ? "服务运行中"
                : "未连接"
              : "检测中..."}
          </span>
        </div>
      </header>

      <main className="chat-area">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <div className="message-role">
              {msg.role === "user" ? "你" : "知己"}
            </div>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-role">知己</div>
            <div className="message-content loading">思考中...</div>
          </div>
        )}

        {error && (
          <div className="error-banner">
            出错了：{error}
            <button onClick={() => setError(null)}>关闭</button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      <footer className="chat-input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入你的问题，按 Enter 发送..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          发送
        </button>
      </footer>
    </div>
  );
}

export default App;
