"""知识库存储层：文本清洗、切分、文件持久化。

MVP 阶段用 JSON 文件存储，无需外部数据库。
"""

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("knowledge_store")


class KnowledgeStore:
    """管理文档上传、切分、存储和查询。"""

    def __init__(self, storage_dir: Path | None = None):
        if storage_dir is None:
            storage_dir = Path(__file__).resolve().parent.parent / "data" / "knowledge"
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.storage_dir / "_index.json"
        self._ensure_index()

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def upload(self, filename: str, content: str) -> dict:
        """上传一份文档，完成清洗 → 切分 → 保存，返回文档摘要。"""
        doc_id = uuid.uuid4().hex[:12]
        source_type = self._guess_type(filename)
        title = Path(filename).stem

        cleaned = self._clean_text(content)
        chunks = self._chunk_text(cleaned)

        doc = {
            "id": doc_id,
            "title": title,
            "source_type": source_type,
            "original_filename": filename,
            "chunk_count": len(chunks),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._save_document(doc, chunks)
        self._add_to_index(doc)

        logger.info("文档已入库: %s (%d 个切片)", filename, len(chunks))
        return doc

    def list_documents(self) -> list[dict]:
        """返回已上传文档列表（不含切片内容）。"""
        index = self._read_index()
        return list(index.values())

    def get_document(self, doc_id: str) -> dict | None:
        """获取单个文档及其所有切片。"""
        index = self._read_index()
        if doc_id not in index:
            return None
        doc = dict(index[doc_id])
        chunks = self._load_chunks(doc_id)
        doc["chunks"] = chunks
        return doc

    # ------------------------------------------------------------------
    # 文本处理
    # ------------------------------------------------------------------

    @staticmethod
    def _guess_type(filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext in (".md", ".markdown"):
            return "md"
        return "txt"

    @staticmethod
    def _clean_text(raw: str) -> str:
        text = raw.replace("\r\n", "\n").replace("\r", "\n")
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _chunk_text(text: str, max_chunk_size: int = 2000) -> list[dict]:
        """按段落切分文本，确保每个切片不超过 max_chunk_size 字符。"""
        raw_paragraphs = text.split("\n\n")
        chunks = []
        index = 0

        for para in raw_paragraphs:
            para = para.strip()
            if not para:
                continue

            # 长段落按句子边界再切分
            if len(para) > max_chunk_size:
                sub_chunks = KnowledgeStore._split_long_paragraph(para, max_chunk_size)
                for sc in sub_chunks:
                    if sc.strip():
                        chunks.append({"chunk_index": index, "content": sc.strip()})
                        index += 1
            else:
                chunks.append({"chunk_index": index, "content": para})
                index += 1

        return chunks

    @staticmethod
    def _split_long_paragraph(text: str, max_size: int) -> list[str]:
        """将过长的段落按句子边界切分为多个片段。"""
        sentences = re.split(r"(?<=[。！？.!?])\s*", text)
        pieces = []
        current = ""

        for sent in sentences:
            if len(current) + len(sent) <= max_size:
                current += sent
            else:
                if current.strip():
                    pieces.append(current.strip())
                current = sent

        if current.strip():
            pieces.append(current.strip())

        # 如果仍有过长的句子（极端情况），按字符硬切
        final = []
        for piece in pieces:
            while len(piece) > max_size:
                final.append(piece[:max_size])
                piece = piece[max_size:]
            if piece.strip():
                final.append(piece.strip())

        return final

    # ------------------------------------------------------------------
    # 文件读写
    # ------------------------------------------------------------------

    def _ensure_index(self):
        if not self._index_path.exists():
            self._index_path.write_text("{}", encoding="utf-8")

    def _read_index(self) -> dict:
        try:
            return json.loads(self._index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_index(self, index: dict):
        self._index_path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _save_document(self, doc: dict, chunks: list[dict]):
        doc_path = self.storage_dir / f"{doc['id']}.json"
        payload = {"doc": doc, "chunks": chunks}
        doc_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _load_chunks(self, doc_id: str) -> list[dict]:
        doc_path = self.storage_dir / f"{doc_id}.json"
        if not doc_path.exists():
            return []
        payload = json.loads(doc_path.read_text(encoding="utf-8"))
        return payload.get("chunks", [])

    def _add_to_index(self, doc: dict):
        index = self._read_index()
        index[doc["id"]] = {
            "id": doc["id"],
            "title": doc["title"],
            "source_type": doc["source_type"],
            "original_filename": doc["original_filename"],
            "chunk_count": doc["chunk_count"],
            "created_at": doc["created_at"],
        }
        self._write_index(index)
