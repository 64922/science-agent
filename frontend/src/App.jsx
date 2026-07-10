import { useState, useEffect, useRef, useMemo } from "react";
import KnowledgePage from "./KnowledgePage";
import ProfilePage from "./ProfilePage";
import { CATEGORY_LABELS, DEMO_USERS } from "./constants";

function getRiskShortLabel(signal) {
  if (signal.startsWith("绝对化")) return "绝对化";
  if (signal.startsWith("具体数字") || signal.startsWith("具体百分比")) return "数字";
  if (signal.startsWith("医学")) return "医学";
  if (signal.startsWith("实验安全")) return "安全";
  if (signal.startsWith("因果外推")) return "外推";
  return "其他";
}

function RiskPanel({ riskReport }) {
  if (!riskReport) {
    return (
      <>
        <h3>风险检测结果</h3>
        <p className="citation-empty">暂无风险检测数据</p>
      </>
    );
  }

  const risks = riskReport.risks || [];

  return (
    <>
      <h3>风险检测结果</h3>
      {risks.length === 0 ? (
        <p className="citation-empty">未检测到高风险表述</p>
      ) : (
        <>
          <div className="risk-summary">
            <span className="risk-badge risk-badge-count">
              发现 {risks.length} 处风险
            </span>
          </div>
          <ul className="risk-list">
            {risks.map((r, i) => (
              <li key={i} className="risk-item">
                <div className="risk-sentence">"{r.sentence}"</div>
                <div className="risk-signals">
                  {r.signals.map((sig) => {
                    const short = getRiskShortLabel(sig);
                    return (
                      <span key={sig} className={`risk-signal-tag risk-tag-${short}`}>
                        {sig}
                      </span>
                    );
                  })}
                </div>
                {r.repaired && (
                  <div className="risk-repaired">
                    <span className="risk-repaired-label">建议修改：</span>
                    "{r.repaired}"
                  </div>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  );
}

function FactLockPanel({ factLock }) {
  if (!factLock) {
    return (
      <>
        <h3>事实锁定结果</h3>
        <p className="citation-empty">知识库无匹配资料，未执行事实锁定</p>
      </>
    );
  }

  const facts = factLock.facts || {};
  const confirmed = facts.confirmed || [];
  const uncertain = facts.uncertain || [];
  const forbidden = facts.forbidden || [];

  const isEmpty = confirmed.length === 0 && uncertain.length === 0 && forbidden.length === 0;

  return (
    <>
      <h3>事实锁定结果</h3>
      {isEmpty ? (
        <p className="citation-empty">本轮未抽取出结构化事实</p>
      ) : (
        <>
          <div className="fact-lock-summary">
            {confirmed.length > 0 && (
              <span className="fl-badge fl-confirmed">已确认 {confirmed.length}</span>
            )}
            {uncertain.length > 0 && (
              <span className="fl-badge fl-uncertain">不确定 {uncertain.length}</span>
            )}
            {forbidden.length > 0 && (
              <span className="fl-badge fl-forbidden">禁止 {forbidden.length}</span>
            )}
          </div>
          <ul className="fact-lock-list">
            {confirmed.map((f, i) => (
              <li key={`cf-${i}`} className="fl-item fl-item-confirmed">
                <span className="fl-tag">已确认</span>
                {f.fact}
              </li>
            ))}
            {uncertain.map((f, i) => (
              <li key={`uc-${i}`} className="fl-item fl-item-uncertain">
                <span className="fl-tag">不确定</span>
                {f.fact}
                <span className="fl-reason">{f.reason}</span>
              </li>
            ))}
            {forbidden.map((f, i) => (
              <li key={`fb-${i}`} className="fl-item fl-item-forbidden">
                <span className="fl-tag">禁止扩展</span>
                {f.domain}
                <span className="fl-reason">{f.reason}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  );
}

function ProfileCandidateCard({ candidates: initialCandidates, onConfirm, onDismiss }) {
  const [candidates, setCandidates] = useState(initialCandidates);
  const [editingIdx, setEditingIdx] = useState(-1);
  const [editValue, setEditValue] = useState("");

  const startEdit = (idx) => {
    setEditingIdx(idx);
    setEditValue(candidates[idx].profile_value);
  };

  const confirmEdit = () => {
    if (!editValue.trim()) return;
    const updated = [...candidates];
    updated[editingIdx] = { ...updated[editingIdx], profile_value: editValue.trim() };
    setCandidates(updated);
    setEditingIdx(-1);
    setEditValue("");
    onConfirm(updated, "remember");
  };

  const handleAction = (action) => {
    onConfirm(candidates, action);
  };

  if (candidates.length === 0) return null;

  return (
    <div className="profile-candidate-card">
      <div className="pcc-header">
        <span className="pcc-icon">📋</span>
        系统识别到以下画像候选，是否记住？
      </div>
      <ul className="pcc-list">
        {candidates.map((c, i) => (
          <li key={i} className="pcc-item">
            <div className="pcc-category">{CATEGORY_LABELS[c.profile_key] || c.profile_key}</div>
            {editingIdx === i ? (
              <div className="pcc-edit-row">
                <input
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") confirmEdit(); }}
                  autoFocus
                />
                <button className="pcc-btn-confirm-edit" onClick={confirmEdit}>确认修改</button>
                <button className="pcc-btn-cancel-edit" onClick={() => setEditingIdx(-1)}>取消</button>
              </div>
            ) : (
              <div className="pcc-value-row">
                <div className="pcc-value">{c.profile_value}</div>
                <button className="pcc-btn-edit-inline" onClick={() => startEdit(i)} title="修改后记住">
                  ✎
                </button>
              </div>
            )}
            {c.evidence && (
              <div className="pcc-evidence">证据：{c.evidence}</div>
            )}
            <div className="pcc-confidence">
              置信度 {Math.round((c.confidence || 0) * 100)}%
            </div>
          </li>
        ))}
      </ul>
      <div className="pcc-actions">
        <button className="pcc-btn-remember" onClick={() => handleAction("remember")}>
          记住
        </button>
        <button className="pcc-btn-session" onClick={() => handleAction("session_only")}>
          仅本次
        </button>
        <button className="pcc-btn-deny" onClick={() => handleAction("deny")}>
          不要记
        </button>
        <button className="pcc-btn-dismiss" onClick={onDismiss}>
          忽略
        </button>
      </div>
    </div>
  );
}

function App() {
  const [activeTab, setActiveTab] = useState("chat");
  const [userId, setUserId] = useState("demo_user_a");
  const [backendStatus, setBackendStatus] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState("popular_science");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sources, setSources] = useState([]);
  const [factLock, setFactLock] = useState(null);
  const [riskReport, setRiskReport] = useState(null);
  const [profileCandidates, setProfileCandidates] = useState(null);
  const [profileSkipLog, setProfileSkipLog] = useState([]);
  const [selectedProfiles, setSelectedProfiles] = useState([]);
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
          user_id: userId,
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
      setSources(data.sources || []);
      setFactLock(data.fact_lock || null);
      setRiskReport(data.risk_report || null);
      setProfileCandidates(
        data.profile_candidates && data.profile_candidates.length > 0
          ? data.profile_candidates
          : null
      );
      setProfileSkipLog(data.profile_skip_log || []);
      setSelectedProfiles(data.selected_profiles || []);
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

  const handleConfirmCandidates = async (candidates, action) => {
    try {
      const res = await fetch(`/api/profile/${userId}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidates, action }),
      });
      if (!res.ok) throw new Error("确认失败");
      setProfileCandidates(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDismissCandidates = () => {
    setProfileCandidates(null);
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

      <nav className="main-tabs">
        <button
          className={`main-tab ${activeTab === "chat" ? "active" : ""}`}
          onClick={() => setActiveTab("chat")}
        >
          对话
        </button>
        <button
          className={`main-tab ${activeTab === "knowledge" ? "active" : ""}`}
          onClick={() => setActiveTab("knowledge")}
        >
          知识库
        </button>
        <button
          className={`main-tab ${activeTab === "profile" ? "active" : ""}`}
          onClick={() => setActiveTab("profile")}
        >
          我的画像
        </button>
      </nav>

      {activeTab === "chat" && (
        <>
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
            <div className="user-select-inline">
              <label>用户：</label>
              <select value={userId} onChange={(e) => setUserId(e.target.value)}>
                {DEMO_USERS.map((u) => (
                  <option key={u.id} value={u.id}>{u.name}</option>
                ))}
              </select>
            </div>
          </nav>

          <div className="chat-container">
            <div className="chat-main">
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

                {profileCandidates && (
                  <ProfileCandidateCard
                    candidates={profileCandidates}
                    onConfirm={handleConfirmCandidates}
                    onDismiss={handleDismissCandidates}
                  />
                )}

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

            <aside className="citation-panel">
              <h3>本轮引用证据</h3>
              {messages.length === 0 ? (
                <p className="citation-empty">发送问题后显示引用证据</p>
              ) : sources.length === 0 ? (
                <p className="citation-empty">当前知识库证据不足</p>
              ) : (
                <ul className="citation-list">
                  {sources.map((s, i) => (
                    <li key={i} className="citation-item">
                      <div className="citation-header">
                        <span className="citation-index">#{i + 1}</span>
                        <span className="citation-source">
                          《{s.doc_title}》· 切片 #{s.chunk_index}
                        </span>
                      </div>
                      <p className="citation-content">{s.content}</p>
                    </li>
                  ))}
                </ul>
              )}

              {messages.length > 0 && (
                <FactLockPanel factLock={factLock} />
              )}

              {selectedProfiles.length > 0 && (
                <>
                  <h3>本轮调用画像</h3>
                  <ul className="profile-recall-list">
                    {selectedProfiles.map((p, i) => (
                      <li key={i} className="profile-recall-item">
                        <span className="pr-category">
                          {CATEGORY_LABELS[p.profile_key] || p.profile_key}
                        </span>
                        <span className="pr-value">{p.profile_value}</span>
                        <span className="pr-reason">{p.reason}</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}

              {profileSkipLog.length > 0 && (
                <>
                  <h3>画像调用跳过记录</h3>
                  <ul className="skip-log-list">
                    {profileSkipLog.map((s, i) => (
                      <li key={i} className="skip-log-item">
                        <span className="fl-tag">未调用</span>
                        {s.profile_value}
                        <span className="fl-reason">{s.reason}</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}

              {messages.length > 0 && (
                <RiskPanel riskReport={riskReport} />
              )}
            </aside>
          </div>
        </>
      )}

      {activeTab === "knowledge" && <KnowledgePage />}

      {activeTab === "profile" && <ProfilePage />}
    </div>
  );
}

export default App;
