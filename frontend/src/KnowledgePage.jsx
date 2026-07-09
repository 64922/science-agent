import { useState, useEffect } from "react";
import "./KnowledgePage.css";

function KnowledgePage() {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const fetchDocuments = () => {
    fetch("/api/knowledge/documents")
      .then((res) => res.json())
      .then((data) => setDocuments(data.documents || []))
      .catch(() => {});
  };

  useEffect(() => {
    fetchDocuments();
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

  return (
    <div className="knowledge-page">
      <header className="kp-header">
        <h2>知识库管理</h2>
        <p>上传 .txt 或 .md 资料，系统将自动清洗并切分为可检索的知识切片。</p>
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
                <th>源文件</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td>{doc.title}</td>
                  <td>
                    <span className="kp-type-badge">{doc.source_type}</span>
                  </td>
                  <td>{doc.chunk_count}</td>
                  <td>{new Date(doc.created_at).toLocaleString("zh-CN")}</td>
                  <td className="kp-filename">{doc.original_filename}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

export default KnowledgePage;
