import { useState, useEffect, useRef, useMemo } from "react";

function App() {
  const [backendStatus, setBackendStatus] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState("popular_science");
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
    fetch("/api/scenarios")
      .then((res) => res.json())
      .then((data) => setScenarios(data.scenarios || []))
      .catch(() => {});
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
          scenario_id: selectedScenario,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `请求失败 (${res.status})`);
      }

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          role: "assistant",
          content: data.reply,
          scenarioName: data.scenario_name,
        },
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

  const currentLabel = useMemo(
    () => scenarios.find((s) => s.id === selectedScenario)?.name || selectedScenario,
    [scenarios, selectedScenario]
  );

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

      <nav className="scenario-bar">
        {scenarios.map((s) => (
          <button
            key={s.id}
            className={`scenario-tab ${s.id === selectedScenario ? "active" : ""}`}
            onClick={() => setSelectedScenario(s.id)}
            disabled={loading}
          >
            {s.name}
          </button>
        ))}
      </nav>

      <main className="chat-area">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <div className="message-role">
              {msg.role === "user"
                ? "你"
                : msg.scenarioName
                  ? `知己 · ${msg.scenarioName}`
                  : "知己"}
            </div>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-role">知己 · {currentLabel}</div>
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
          placeholder={`在「${currentLabel}」场景下提问，按 Enter 发送...`}
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
