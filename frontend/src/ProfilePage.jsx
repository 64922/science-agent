import { useState, useEffect } from "react";
import "./ProfilePage.css";
import { CATEGORY_LABELS, CATEGORY_ORDER, AUTH_LABELS, DEMO_USERS } from "./constants";

const ACTION_LABELS = {
  revoke_single: "撤回单条",
  revoke_category: "撤回类别",
  pause_memory: "暂停记忆",
  resume_memory: "恢复记忆",
};

const ACTION_TARGET = {
  revoke_single: (t) => `画像 #${t}`,
  revoke_category: (t) => CATEGORY_LABELS[t] || t,
  pause_memory: () => "全部记忆",
  resume_memory: () => "全部记忆",
};

function ProfilePage() {
  const [userId, setUserId] = useState("demo_user_a");
  const [profiles, setProfiles] = useState([]);
  const [error, setError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [adding, setAdding] = useState(false);
  const [memoryPaused, setMemoryPaused] = useState(false);
  const [auditLog, setAuditLog] = useState([]);
  const [showAuditLog, setShowAuditLog] = useState(false);
  const [newForm, setNewForm] = useState({
    profile_key: "basic_info",
    profile_value: "",
    evidence: "",
    confidence: 0.8,
    authorization_status: "confirmed",
  });

  const fetchProfiles = (uid) => {
    fetch(`/api/profile/${uid}`)
      .then((res) => res.json())
      .then((data) => {
        setProfiles(data.profiles || []);
      })
      .catch(() => setError("获取画像失败"));
  };

  const refreshAuditLog = () => {
    fetch(`/api/profile/${userId}/audit-log`)
      .then((res) => res.json())
      .then((data) => setAuditLog(data.entries || []))
      .catch(() => {});
  };

  useEffect(() => {
    fetchProfiles(userId);
    fetch(`/api/profile/${userId}/memory-status`)
      .then((res) => res.json())
      .then((data) => setMemoryPaused(data.memory_state?.paused || false))
      .catch(() => {});
    refreshAuditLog();
  }, [userId]);

  const handleDelete = async (profileId) => {
    if (!window.confirm("确定要删除这条画像吗？")) return;
    try {
      const res = await fetch(`/api/profile/${userId}/${profileId}`, { method: "DELETE" });
      if (!res.ok) throw new Error("删除失败");
      fetchProfiles(userId);
    } catch (err) {
      setError(err.message);
    }
  };

  const startEdit = (p) => {
    setEditingId(p.id);
    setEditForm({
      profile_value: p.profile_value,
      profile_key: p.profile_key,
      evidence: p.evidence,
      confidence: p.confidence,
      authorization_status: p.authorization_status,
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({});
  };

  const submitEdit = async () => {
    try {
      const res = await fetch(`/api/profile/${userId}/${editingId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editForm),
      });
      if (!res.ok) throw new Error("更新失败");
      setEditingId(null);
      setEditForm({});
      fetchProfiles(userId);
    } catch (err) {
      setError(err.message);
    }
  };

  const submitAdd = async () => {
    if (!newForm.profile_value.trim()) {
      setError("画像内容不能为空");
      return;
    }
    try {
      const res = await fetch(`/api/profile/${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newForm),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "添加失败");
      }
      setAdding(false);
      setNewForm({
        profile_key: "basic_info",
        profile_value: "",
        evidence: "",
        confidence: 0.8,
        authorization_status: "confirmed",
      });
      fetchProfiles(userId);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRevoke = async (profileId) => {
    if (!window.confirm("确定要撤回这条画像的授权吗？")) return;
    try {
      const res = await fetch(`/api/profile/${userId}/revoke/${profileId}`, { method: "POST" });
      if (!res.ok) throw new Error("撤回失败");
      fetchProfiles(userId);
      refreshAuditLog();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRevokeCategory = async (categoryKey) => {
    if (!window.confirm(`确定要撤回「${CATEGORY_LABELS[categoryKey]}」类别的全部授权吗？`)) return;
    try {
      const res = await fetch(`/api/profile/${userId}/revoke-category/${categoryKey}`, { method: "POST" });
      if (!res.ok) throw new Error("批量撤回失败");
      fetchProfiles(userId);
      refreshAuditLog();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleToggleMemory = async () => {
    const endpoint = memoryPaused ? "memory-resume" : "memory-pause";
    const action = memoryPaused ? "恢复" : "暂停";
    if (!window.confirm(`确定要${action}全部记忆吗？`)) return;
    try {
      const res = await fetch(`/api/profile/${userId}/${endpoint}`, { method: "POST" });
      if (!res.ok) throw new Error(`${action}失败`);
      const data = await res.json();
      setMemoryPaused(data.memory_state?.paused || false);
      refreshAuditLog();
    } catch (err) {
      setError(err.message);
    }
  };

  const groupedProfiles = CATEGORY_ORDER.map((key) => ({
    key,
    label: CATEGORY_LABELS[key],
    items: profiles.filter((p) => p.profile_key === key),
  }));

  return (
    <div className="profile-page">
      <header className="pp-header">
        <h2>我的画像</h2>
        <p>管理系统对你的认知画像。你的画像会影响回答的风格、难度和举例方式。</p>
      </header>

      <section className="pp-user-select">
        <label>当前用户：</label>
        <select value={userId} onChange={(e) => setUserId(e.target.value)}>
          {DEMO_USERS.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name}
            </option>
          ))}
        </select>
        <button className="pp-add-btn" onClick={() => setAdding(true)} disabled={adding}>
          添加画像
        </button>
        <button
          className={`pp-memory-btn ${memoryPaused ? "pp-memory-paused" : ""}`}
          onClick={handleToggleMemory}
        >
          {memoryPaused ? "▶ 恢复记忆" : "⏸ 暂停记忆"}
        </button>
      </section>

      {error && (
        <div className="pp-error">
          出错了：{error}
          <button onClick={() => setError(null)}>关闭</button>
        </div>
      )}

      {adding && (
        <section className="pp-add-form">
          <h3>新增画像条目</h3>
          <div className="pp-form-row">
            <label>类别</label>
            <select
              value={newForm.profile_key}
              onChange={(e) => setNewForm({ ...newForm, profile_key: e.target.value })}
            >
              {CATEGORY_ORDER.map((k) => (
                <option key={k} value={k}>{CATEGORY_LABELS[k]}</option>
              ))}
            </select>
          </div>
          <div className="pp-form-row">
            <label>内容</label>
            <input
              type="text"
              value={newForm.profile_value}
              onChange={(e) => setNewForm({ ...newForm, profile_value: e.target.value })}
              placeholder="画像内容，例如：高中一年级"
            />
          </div>
          <div className="pp-form-row">
            <label>证据</label>
            <input
              type="text"
              value={newForm.evidence}
              onChange={(e) => setNewForm({ ...newForm, evidence: e.target.value })}
              placeholder="证据来源，例如：用户说'我是高一学生'"
            />
          </div>
          <div className="pp-form-row">
            <label>置信度（{newForm.confidence}）</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={newForm.confidence}
              onChange={(e) => setNewForm({ ...newForm, confidence: parseFloat(e.target.value) })}
            />
          </div>
          <div className="pp-form-row">
            <label>授权状态</label>
            <select
              value={newForm.authorization_status}
              onChange={(e) => setNewForm({ ...newForm, authorization_status: e.target.value })}
            >
              <option value="confirmed">已授权</option>
              <option value="session_only">仅本轮</option>
              <option value="denied">已拒绝</option>
              <option value="revoked">已撤回</option>
            </select>
          </div>
          <div className="pp-form-actions">
            <button className="pp-btn-save" onClick={submitAdd}>保存</button>
            <button className="pp-btn-cancel" onClick={() => setAdding(false)}>取消</button>
          </div>
        </section>
      )}

      <section className="pp-profile-list">
        {groupedProfiles.map((group) => (
          <div key={group.key} className="pp-category">
            <h3 className="pp-cat-title">
              {group.label}
              <span className="pp-cat-count">{group.items.length}</span>
              {group.items.length > 0 && (
                <button
                  className="pp-btn-revoke-cat"
                  onClick={() => handleRevokeCategory(group.key)}
                  title={`撤回「${group.label}」全部授权`}
                >
                  撤回全部
                </button>
              )}
            </h3>
            {group.items.length === 0 ? (
              <p className="pp-empty-cat">暂无此类别画像</p>
            ) : (
              <ul className="pp-items">
                {group.items.map((p) =>
                  editingId === p.id ? (
                    <li key={p.id} className="pp-item pp-item-editing">
                      <div className="pp-edit-form">
                        <div className="pp-ef-row">
                          <label>内容</label>
                          <input
                            type="text"
                            value={editForm.profile_value}
                            onChange={(e) => setEditForm({ ...editForm, profile_value: e.target.value })}
                          />
                        </div>
                        <div className="pp-ef-row">
                          <label>证据</label>
                          <input
                            type="text"
                            value={editForm.evidence}
                            onChange={(e) => setEditForm({ ...editForm, evidence: e.target.value })}
                          />
                        </div>
                        <div className="pp-ef-row">
                          <label>置信度（{editForm.confidence}）</label>
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.05"
                            value={editForm.confidence}
                            onChange={(e) => setEditForm({ ...editForm, confidence: parseFloat(e.target.value) })}
                          />
                        </div>
                        <div className="pp-ef-row">
                          <label>授权状态</label>
                          <select
                            value={editForm.authorization_status}
                            onChange={(e) => setEditForm({ ...editForm, authorization_status: e.target.value })}
                          >
                            <option value="confirmed">已授权</option>
                            <option value="session_only">仅本轮</option>
                            <option value="denied">已拒绝</option>
                            <option value="revoked">已撤回</option>
                          </select>
                        </div>
                        <div className="pp-ef-actions">
                          <button className="pp-btn-save" onClick={submitEdit}>保存</button>
                          <button className="pp-btn-cancel" onClick={cancelEdit}>取消</button>
                        </div>
                      </div>
                    </li>
                  ) : (
                    <li key={p.id} className="pp-item">
                      <div className="pp-item-main">
                        <span className="pp-value">{p.profile_value}</span>
                        <div className="pp-meta">
                          {p.evidence && (
                            <span className="pp-evidence" title={p.evidence}>
                              证据：{p.evidence.length > 40 ? p.evidence.slice(0, 40) + "…" : p.evidence}
                            </span>
                          )}
                          <span className={`pp-auth pp-auth-${p.authorization_status}`}>
                            {AUTH_LABELS[p.authorization_status] || p.authorization_status}
                          </span>
                          <span className="pp-confidence">
                            置信度 {Math.round(p.confidence * 100)}%
                          </span>
                        </div>
                        <div className="pp-time">
                          更新于 {new Date(p.updated_at).toLocaleString("zh-CN")}
                        </div>
                      </div>
                      <div className="pp-item-actions">
                        {p.authorization_status !== "revoked" && (
                          <button className="pp-btn-revoke" onClick={() => handleRevoke(p.id)}>撤回</button>
                        )}
                        <button className="pp-btn-edit" onClick={() => startEdit(p)}>修改</button>
                        <button className="pp-btn-delete" onClick={() => handleDelete(p.id)}>删除</button>
                      </div>
                    </li>
                  )
                )}
              </ul>
            )}
          </div>
        ))}
      </section>

      <section className="pp-audit-section">
        <button
          className="pp-audit-toggle"
          onClick={() => setShowAuditLog(!showAuditLog)}
        >
          授权变更记录
          <span className="pp-audit-count">{auditLog.length}</span>
          <span className="pp-audit-arrow">{showAuditLog ? "▲" : "▼"}</span>
        </button>
        {showAuditLog && (
          auditLog.length === 0 ? (
            <p className="pp-audit-empty">暂无操作记录</p>
          ) : (
            <ul className="pp-audit-list">
              {auditLog.map((entry) => (
                <li key={entry.id} className="pp-audit-item">
                  <span className={`pp-audit-badge pp-audit-${entry.action}`}>
                    {ACTION_LABELS[entry.action] || entry.action}
                  </span>
                  <span className="pp-audit-target">
                    {(ACTION_TARGET[entry.action] || (() => entry.target))(entry.target)}
                  </span>
                  <span className="pp-audit-state">
                    {entry.previous_state} → {entry.new_state}
                  </span>
                  <span className="pp-audit-time">
                    {new Date(entry.timestamp).toLocaleString("zh-CN")}
                  </span>
                </li>
              ))}
            </ul>
          )
        )}
      </section>
    </div>
  );
}

export default ProfilePage;
