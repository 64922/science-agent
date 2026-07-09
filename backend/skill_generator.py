"""知识 Skill 生成器：调用 Qwen 从文档切片中抽取结构化知识点。"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from llm_client import LLMClient

logger = logging.getLogger("skill_generator")

SKILL_SYSTEM_PROMPT = """你是一位科教知识整理专家。你的任务是从给定的文档切片中提取结构化的教学知识(Skill)。

## 输出要求

返回一个 JSON 对象，格式如下：

```json
{
  "core_concepts": [
    {
      "concept": "核心概念名称",
      "description": "用一两句话解释这个概念",
      "source_chunks": [0, 2]
    }
  ],
  "definitions": [
    {
      "term": "专业术语",
      "definition": "准确的定义",
      "source_chunks": [1]
    }
  ],
  "misconceptions": [
    {
      "misconception": "常见的错误理解",
      "correction": "正确的理解是什么",
      "source_chunks": [3]
    }
  ],
  "target_audience": {
    "level": "适合的学段（如：初中/高中/大学低年级/研究生）",
    "prerequisites": ["需要的前置知识"],
    "suggested_approach": "建议的教学方式或讲解策略（1-2句话）"
  }
}
```

## 抽取规则

1. **core_concepts**：提取文档中讨论的核心科学概念（3-8 个）。每个概念给出准确但不过于学术化的描述。
2. **definitions**：提取需要精确定义的专业术语（2-6 个）。定义必须忠实于原文，不可发挥。
3. **misconceptions**：如果文档明确提及或暗示了常见误解，列出来（0-4 个）。没有的话返回空数组。
4. **target_audience**：根据文档的深度和语言风格，判断适合的受众和前置知识。
5. **source_chunks**：每个条目必须标注来源切片编号（chunk_index），这是从哪些切片中提取的。确保可追溯。
6. 只提取文档中实际存在的信息，不要凭空编造。"""


class SkillGenerator:
    """从知识库文档生成结构化教学 Skill。"""

    def __init__(self, llm_client: LLMClient, storage_dir: Path | None = None):
        self.llm = llm_client
        if storage_dir is None:
            storage_dir = Path(__file__).resolve().parent.parent / "data" / "knowledge"
        self.storage_dir = storage_dir

    def generate(self, doc: dict) -> dict:
        """为一份文档生成知识 Skill，结果持久化到磁盘。"""
        doc_id = doc["id"]
        chunks = doc.get("chunks", [])
        if not chunks:
            raise ValueError("文档没有切片内容，无法生成 Skill")

        skill_path = self._skill_path(doc_id)

        # 标记生成中
        self._save_skill(doc_id, {"status": "generating", "generated_at": None, "skill": None, "error_message": None})

        try:
            user_message = self._build_user_message(chunks)
            raw = self.llm.chat_structured(SKILL_SYSTEM_PROMPT, user_message, temperature=0.3, max_tokens=4096)

            skill = self._validate_and_clean(raw, len(chunks))

            result = {
                "status": "ready",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "skill": skill,
                "error_message": None,
            }
            self._save_skill(doc_id, result)
            logger.info("Skill 生成成功: %s (%s)", doc.get("title", doc_id), doc_id)
            return result

        except Exception as exc:
            error_result = {
                "status": "error",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "skill": None,
                "error_message": str(exc),
            }
            self._save_skill(doc_id, error_result)
            logger.error("Skill 生成失败: %s — %s", doc_id, exc)
            raise

    def get_skill(self, doc_id: str) -> dict | None:
        """读取已生成的 Skill。"""
        skill_path = self._skill_path(doc_id)
        if not skill_path.exists():
            return None
        return json.loads(skill_path.read_text(encoding="utf-8"))

    def list_skills(self) -> list[dict]:
        """列出所有已生成的 Skill 摘要。"""
        skills = []
        for f in sorted(self.storage_dir.glob("*_skill.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                doc_id = f.stem.replace("_skill", "")
                skills.append({
                    "doc_id": doc_id,
                    "status": data.get("status"),
                    "generated_at": data.get("generated_at"),
                    "has_error": data.get("error_message") is not None,
                })
            except json.JSONDecodeError:
                continue
        return skills

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _skill_path(self, doc_id: str) -> Path:
        return self.storage_dir / f"{doc_id}_skill.json"

    @staticmethod
    def _build_user_message(chunks: list[dict]) -> str:
        lines = ["请从以下文档切片中提取结构化教学知识：\n"]
        for ch in chunks:
            lines.append(f"--- 切片 {ch['chunk_index']} ---")
            lines.append(ch["content"])
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _validate_and_clean(raw: dict, chunk_count: int) -> dict:
        """确保 LLM 输出结构完整、source_chunks 范围有效。"""
        valid_range = range(chunk_count)

        def clamp(chunk_list):
            return [i for i in (chunk_list or []) if isinstance(i, int) and i in valid_range]

        core = raw.get("core_concepts") or []
        concepts = []
        for c in core:
            if not c.get("concept"):
                continue
            concepts.append({
                "concept": str(c["concept"]),
                "description": str(c.get("description", "")),
                "source_chunks": clamp(c.get("source_chunks", [])),
            })

        defs_raw = raw.get("definitions") or []
        definitions = []
        for d in defs_raw:
            if not d.get("term"):
                continue
            definitions.append({
                "term": str(d["term"]),
                "definition": str(d.get("definition", "")),
                "source_chunks": clamp(d.get("source_chunks", [])),
            })

        misc_raw = raw.get("misconceptions") or []
        misconceptions = []
        for m in misc_raw:
            if not m.get("misconception"):
                continue
            misconceptions.append({
                "misconception": str(m["misconception"]),
                "correction": str(m.get("correction", "")),
                "source_chunks": clamp(m.get("source_chunks", [])),
            })

        audience = raw.get("target_audience") or {}
        target_audience = {
            "level": str(audience.get("level", "未指定")),
            "prerequisites": [str(p) for p in (audience.get("prerequisites") or [])],
            "suggested_approach": str(audience.get("suggested_approach", "")),
        }

        return {
            "core_concepts": concepts,
            "definitions": definitions,
            "misconceptions": misconceptions,
            "target_audience": target_audience,
        }

    def _save_skill(self, doc_id: str, data: dict):
        self._skill_path(doc_id).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
