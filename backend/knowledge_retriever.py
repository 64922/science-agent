"""知识检索层：基于 ChromaDB 的向量检索 + 关键词回退。"""

import logging
import re
from pathlib import Path
from typing import TypedDict

from knowledge_store import ChunkDict

logger = logging.getLogger("knowledge_retriever")


class SourceDict(TypedDict):
    doc_id: str
    doc_title: str
    chunk_index: int
    content: str
    relevance: float


class KnowledgeRetriever:
    """封装 ChromaDB 向量检索，支持添加文档和语义查询。

    向量检索无结果时自动回退到关键词匹配，确保小知识库也能
    返回至少 1 条来源（AC4）。
    """

    def __init__(self, persist_dir: Path | None = None, knowledge_store=None):
        self.knowledge_store = knowledge_store
        self._ready = False
        self._collection = None

        try:
            import chromadb

            if persist_dir is None:
                persist_dir = Path(__file__).resolve().parent.parent / "data" / "chromadb"
            persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(persist_dir))
            self._collection = self._client.get_or_create_collection(name="knowledge_chunks")
            self._ready = True
            logger.info("KnowledgeRetriever 初始化成功，持久化目录: %s", persist_dir)
        except ImportError:
            logger.warning("chromadb 未安装，知识检索不可用")
        except Exception as exc:
            logger.warning("KnowledgeRetriever 初始化失败: %s", exc)

    @property
    def ready(self) -> bool:
        return self._ready

    def add_document(self, doc_id: str, doc_title: str, chunks: list[ChunkDict]):
        """将文档切片添加到向量索引。"""
        if not self._ready or not chunks:
            return

        ids = [f"{doc_id}_{c['chunk_index']}" for c in chunks]
        documents = [c["content"] for c in chunks]
        metadatas = [
            {"doc_id": doc_id, "doc_title": doc_title, "chunk_index": c["chunk_index"]}
            for c in chunks
        ]

        try:
            self._collection.add(ids=ids, documents=documents, metadatas=metadatas)
            logger.info("已索引文档 %s (%d 个切片)", doc_id, len(chunks))
        except Exception as exc:
            logger.error("索引文档 %s 失败: %s", doc_id, exc)

    def retrieve(self, query: str, top_k: int = 5) -> list[SourceDict]:
        """检索与查询最相关的知识切片。

        优先使用 ChromaDB 向量检索；向量检索无结果时回退到关键词匹配。
        """
        sources = self._vector_search(query, top_k)
        if not sources:
            sources = self._keyword_search(query, top_k)
        return sources

    # ------------------------------------------------------------------
    # 向量检索
    # ------------------------------------------------------------------

    def _vector_search(self, query: str, top_k: int) -> list[SourceDict]:
        if not self._ready:
            return []

        count = self._collection.count()
        if count == 0:
            return []

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(top_k, count),
            )
        except Exception as exc:
            logger.error("检索失败: %s", exc)
            return []

        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        ids_list = results["ids"][0]
        docs_list = results.get("documents", [[""]])[0]
        metas_list = results.get("metadatas", [[{}]])[0]
        distances = results.get("distances", [[0.0] * len(ids_list)])[0]

        # ChromaDB 默认 all-MiniLM-L6-v2（余弦距离，范围 0-2）。
        # 中文内容距离天然偏高，EVIDENCE_CUTOFF 设为 1.85 以过滤明显无关的结果。
        EVIDENCE_CUTOFF = 1.85

        best_distance = distances[0] if distances else 2.0
        if best_distance > EVIDENCE_CUTOFF:
            return []

        sources: list[SourceDict] = []
        for i, chunk_id in enumerate(ids_list):
            distance = distances[i] if i < len(distances) else 2.0
            relevance = round(max(0.0, 1.0 - distance), 4)
            meta = metas_list[i] if i < len(metas_list) else {}
            sources.append({
                "doc_id": meta.get("doc_id", ""),
                "doc_title": meta.get("doc_title", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "content": docs_list[i] if i < len(docs_list) else "",
                "relevance": relevance,
            })

        return sources

    # ------------------------------------------------------------------
    # 关键词回退检索
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize_for_keyword(text: str) -> list[str]:
        """中文关键词分词：字符级 bigram + 原词。"""
        cleaned = re.sub(r"[^一-鿿\w]", "", text.lower())
        tokens = [cleaned]  # 完整查询作为最高权重 token
        for i in range(len(cleaned) - 1):
            tokens.append(cleaned[i:i + 2])
        return tokens

    def _keyword_search(self, query: str, top_k: int) -> list[SourceDict]:
        """关键词匹配回退：遍历所有文档切片，按命中数排序。"""
        if self.knowledge_store is None:
            return []

        query_tokens = self._tokenize_for_keyword(query)
        if not query_tokens:
            return []

        scored: list[tuple[float, dict]] = []
        for doc_summary in self.knowledge_store.list_documents():
            full_doc = self.knowledge_store.get_document(doc_summary["id"])
            if not full_doc or not full_doc.get("chunks"):
                continue
            for chunk in full_doc["chunks"]:
                content_lower = chunk["content"].lower()
                hits = sum(1 for t in query_tokens if t in content_lower)
                if hits == 0:
                    continue
                # 基础分 = 命中率；完整查询命中额外加权
                score = hits / len(query_tokens)
                if query_tokens[0] in content_lower:
                    score += 0.5
                scored.append((score, {
                    "doc_id": full_doc["id"],
                    "doc_title": full_doc["title"],
                    "chunk_index": chunk["chunk_index"],
                    "content": chunk["content"],
                    "relevance": round(min(1.0, score), 4),
                }))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    # ------------------------------------------------------------------
    # 索引同步
    # ------------------------------------------------------------------

    def sync_from_store(self):
        """将 KnowledgeStore 中已有的文档同步到 ChromaDB。"""
        if not self._ready or self.knowledge_store is None:
            return

        existing = self._collection.get()
        indexed_ids = set()
        if existing and existing.get("metadatas"):
            for meta in existing["metadatas"]:
                if meta and "doc_id" in meta:
                    indexed_ids.add(meta["doc_id"])

        documents = self.knowledge_store.list_documents()
        for doc in documents:
            if doc["id"] in indexed_ids:
                continue
            full_doc = self.knowledge_store.get_document(doc["id"])
            if full_doc and full_doc.get("chunks"):
                self.add_document(doc["id"], doc["title"], full_doc["chunks"])
