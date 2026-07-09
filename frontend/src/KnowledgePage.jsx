import { useState, useEffect } from "react";
import "./KnowledgePage.css";

function KnowledgePage() {
  const [documents, setDocuments] = useState([]);
  const [skills, setSkills] = useState({});
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [generatingId, setGeneratingId] = useState(null);
  const [selectedSkill, setSelectedSkill] = useState(null);

  const fetchDocuments = () => {
    fetch("/api/knowledge/documents")
      .then((res) => res.json())
      .then((data) => setDocuments(data.documents || []))
      .catch(() => {});
  };

  const fetchSkills = () => {
    fetch("/api/knowledge/skills")
      .then((res) => res.json())
      .then((data) => {
        const map = {};
        (data.skills || []).forEach((s) => {
          map[s.doc_id] = s;
        });
        setSkills(map);
      })
      .catch(() => {});
  };

  useEffect(() => {
    fetchDocuments();
    fetchSkills();
  }, []);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    setSuccessMsg(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/knowledge/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `上传失败 (${res.status})`);
      }

      const data = await res.json();
      setSuccessMsg(`「${data.document.title}」上传成功，共 ${data.document.chunk_count} 个切片`);
      fetchDocuments();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleGenerateSkill = async (docId) => {
    setGeneratingId(docId);
    setError(null);
    try {
      const res = await fetch(`/api/knowledge/documents/${docId}/generate-skill`, {
        method: "POST",
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `生成失败 (${res.status})`);
      }
      const data = await res.json();
      setSkills((prev) => ({
        ...prev,
        [docId]: {
          doc_id: docId,
          status: data.skill.status,
          generated_at: data.skill.generated_at,
          has_error: false,
        },
      }));
      setSuccessMsg("知识 Skill 生成成功！");
    } catch (err) {
      setError(err.message);
    } finally {
      setGeneratingId(null);
    }
  };

  const handleViewSkill = async (docId) => {
    if (selectedSkill?.doc_id === docId) {
      setSelectedSkill(null);
      return;
    }
    try {
      const res = await fetch(`/api/knowledge/documents/${docId}/skill`);
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `获取失败 (${res.status})`);
      }
      const data = await res.json();
      setSelectedSkill({ doc_id: docId, ...data.skill });
    } catch (err) {
      setError(err.message);
    }
  };

  const skillStatus = (docId) => {
    const s = skills[docId];
    if (!s) return null;
    if (s.status === "generating") return "generating";
    if (s.status === "error" || s.has_error) return "error";
    if (s.status === "ready") return "ready";
    return null;
  };

  const statusLabel = (status) => {
    switch (status) {
      case "generating":
        return { text: "生成中...", className: "skill-badge generating" };
      case "error":
        return { text: "生成失败", className: "skill-badge error" };
      case "ready":
        return { text: "已就绪", className: "skill-badge ready" };
      default:
        return null;
    }
  };

  return (
    <div className="knowledge-page">
      <header className="kp-header">
        <h2>知识库管理</h2>
        <p>上传 .txt 或 .md 资料，系统将自动清洗并切分为可检索的知识切片，并可生成结构化教学 Skill。</p>
      </header>

      <section className="kp-upload">
        <label className="kp-upload-btn" tabIndex={0}>
          {uploading ? "处理中..." : "选择文件上传"}
          <input
            type="file"
            accept=".txt,.md,.markdown"
            onChange={handleUpload}
            disabled={uploading}
            hidden
          />
        </label>
        <span className="kp-hint">支持 .txt / .md 格式，UTF-8 编码</span>
      </section>

      {successMsg && (
        <div className="kp-success">
          {successMsg}
          <button onClick={() => setSuccessMsg(null)}>关闭</button>
        </div>
      )}

      {error && (
        <div className="kp-error">
          出错了：{error}
          <button onClick={() => setError(null)}>关闭</button>
        </div>
      )}

      <section className="kp-doc-list">
        <h3>已上传资料（{documents.length}）</h3>
        {documents.length === 0 ? (
          <p className="kp-empty">暂无资料，请上传 .txt 或 .md 文件</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>文档名称</th>
                <th>类型</th>
                <th>切片数</th>
                <th>上传时间</th>
                <th>Skill</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => {
                const st = skillStatus(doc.id);
                const lbl = statusLabel(st);
                const isGenerating = generatingId === doc.id;
                return (
                  <tr key={doc.id}>
                    <td>{doc.title}</td>
                    <td>
                      <span className="kp-type-badge">{doc.source_type}</span>
                    </td>
                    <td>{doc.chunk_count}</td>
                    <td>{new Date(doc.created_at).toLocaleString("zh-CN")}</td>
                    <td>
                      {lbl ? (
                        <span className={lbl.className}>{lbl.text}</span>
                      ) : (
                        <span className="skill-badge none">未生成</span>
                      )}
                    </td>
                    <td className="kp-actions">
                      {st === "ready" && (
                        <button
                          className="kp-btn kp-btn-view"
                          onClick={() => handleViewSkill(doc.id)}
                        >
                          {selectedSkill?.doc_id === doc.id ? "收起" : "查看"}
                        </button>
                      )}
                      <button
                        className="kp-btn kp-btn-gen"
                        onClick={() => handleGenerateSkill(doc.id)}
                        disabled={isGenerating}
                      >
                        {isGenerating
                          ? "生成中..."
                          : st === "ready" || st === "error"
                            ? "重新生成"
                            : "生成 Skill"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>

      {selectedSkill && selectedSkill.skill && (
        <section className="kp-skill-detail">
          <h3>知识 Skill 详情</h3>

          <div className="skill-section">
            <h4>核心概念（{selectedSkill.skill.core_concepts?.length || 0}）</h4>
            {selectedSkill.skill.core_concepts?.map((c, i) => (
              <div key={i} className="skill-item">
                <strong>{c.concept}</strong>
                <p>{c.description}</p>
                {c.source_chunks?.length > 0 && (
                  <span className="skill-sources">
                    来源切片：{c.source_chunks.map((ci) => `#${ci}`).join("、")}
                  </span>
                )}
              </div>
            ))}
          </div>

          <div className="skill-section">
            <h4>专业定义（{selectedSkill.skill.definitions?.length || 0}）</h4>
            {selectedSkill.skill.definitions?.map((d, i) => (
              <div key={i} className="skill-item">
                <strong>{d.term}</strong>
                <p>{d.definition}</p>
                {d.source_chunks?.length > 0 && (
                  <span className="skill-sources">
                    来源切片：{d.source_chunks.map((ci) => `#${ci}`).join("、")}
                  </span>
                )}
              </div>
            ))}
          </div>

          <div className="skill-section">
            <h4>常见误解（{selectedSkill.skill.misconceptions?.length || 0}）</h4>
            {selectedSkill.skill.misconceptions?.map((m, i) => (
              <div key={i} className="skill-item misconception">
                <strong>❌ {m.misconception}</strong>
                <p>✅ {m.correction}</p>
                {m.source_chunks?.length > 0 && (
                  <span className="skill-sources">
                    来源切片：{m.source_chunks.map((ci) => `#${ci}`).join("、")}
                  </span>
                )}
              </div>
            ))}
            {selectedSkill.skill.misconceptions?.length === 0 && (
              <p className="skill-none">文档未提及常见误解</p>
            )}
          </div>

          <div className="skill-section">
            <h4>适用受众</h4>
            {selectedSkill.skill.target_audience ? (
              <div className="skill-item audience">
                <p><strong>适合学段：</strong>{selectedSkill.skill.target_audience.level}</p>
                {selectedSkill.skill.target_audience.prerequisites?.length > 0 && (
                  <p><strong>前置知识：</strong>{selectedSkill.skill.target_audience.prerequisites.join("、")}</p>
                )}
                {selectedSkill.skill.target_audience.suggested_approach && (
                  <p><strong>教学建议：</strong>{selectedSkill.skill.target_audience.suggested_approach}</p>
                )}
              </div>
            ) : (
              <p className="skill-none">未指定</p>
            )}
          </div>

          <p className="skill-generated-at">
            生成时间：{new Date(selectedSkill.generated_at).toLocaleString("zh-CN")}
          </p>
        </section>
      )}
    </div>
  );
}

export default KnowledgePage;
