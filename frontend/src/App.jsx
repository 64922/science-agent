import { useState, useEffect } from "react";

function App() {
  const [backendStatus, setBackendStatus] = useState(null);

  useEffect(() => {
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => setBackendStatus(data))
      .catch(() => setBackendStatus({ status: "disconnected" }));
  }, []);

  return (
    <div className="app">
      <header className="hero">
        <h1>知己科教 Agent</h1>
        <p className="subtitle">
          一个能记住你、锁定事实、像真人老师一样讲科学的智能体
        </p>
      </header>

      <section className="status-bar">
        <span className="status-dot" data-status={backendStatus?.status} />
        <span>
          后端服务：
          {backendStatus
            ? backendStatus.status === "ok"
              ? "运行中"
              : "未连接"
            : "检测中..."}
        </span>
      </section>

      <main className="demo-section">
        <h2>演示主题</h2>
        <div className="demo-card">
          <h3>免疫系统如何识别病毒</h3>
          <p>从抗原呈递到免疫记忆，一步步理解身体的防御机制。</p>
        </div>

        <h2>演示用户</h2>
        <div className="user-cards">
          <div className="user-card">
            <h4>用户 A：高一学生</h4>
            <p>基础较弱，喜欢航天类比，一步步讲</p>
          </div>
          <div className="user-card">
            <h4>用户 B：大学低年级学生</h4>
            <p>知道术语但不稳，喜欢机制图和因果链</p>
          </div>
          <div className="user-card">
            <h4>用户 C：科研新手</h4>
            <p>关注证据来源，偏好严谨克制表达</p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
