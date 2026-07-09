"""事实锁定层 —— 从知识库资料中提取结构化事实清单，约束最终回答。"""

import logging
from llm_client import LLMClient

logger = logging.getLogger("fact_lock")

FACT_EXTRACTION_PROMPT = """你是一个科学事实审查员。你的任务是：根据提供的知识库资料，从用户问题中提取关键事实，并分类为三类。

## 分类标准

1. **已确认事实 (confirmed)**：知识库资料中明确陈述的事实。每条必须引用来源切片编号。
2. **不确定事实 (uncertain)**：与问题相关，但资料中没有明确说明的内容。需要标注"不确定"的原因。
3. **禁止扩展边界 (forbidden)**：资料完全不涉及的主题领域。回答时不得对这些领域做任何断言。

## 输出格式
返回严格的 JSON 对象，结构如下：
{
  "facts": {
    "confirmed": [
      {"fact": "完整的事实陈述句", "source_chunk": 编号}
    ],
    "uncertain": [
      {"fact": "完整的事实陈述句", "reason": "证据中未明确说明该机制"}
    ],
    "forbidden": [
      {"domain": "领域名称", "reason": "知识库无相关数据"}
    ]
  }
}

## 要求
- confirmed 和 uncertain 的 fact 字段必须是完整的、可独立理解的事实陈述句。
- 如果某类为空，返回空数组 []。
- 不要编造资料中没有的事实。
- 只输出 JSON，不要有其他文字。"""

FACT_LOCK_CONSTRAINT = """\n\n【事实锁定约束】
在生成回答时，你必须严格遵守以下约束：

核心规则：最终回答中的关键科学结论必须来自"已确认事实"列表。不得加入列表外的新关键结论。
- 已确认事实可以直接使用。
- 不确定的事实如需提及，必须标注"目前尚不完全清楚"或"可能"。
- 禁止扩展领域中的内容不得做任何断言，如被问及应明确说明"目前的知识库不包含这方面的信息"."""


class FactLockBuilder:
    """从知识库资料中提取结构化事实清单，生成回答约束。

    每次 /api/chat 先调用 build() 锁定事实边界，
    再将约束注入系统提示词，确保 LLM 不凭空编造科学结论。
    """

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def build(self, question: str, sources: list[dict]) -> dict:
        """从用户问题和知识库来源中提取事实清单。

        Returns:
            {"facts": {"confirmed": [...], "uncertain": [...], "forbidden": [...]}}
        """
        evidence = self._format_sources(sources)
        user_message = (
            f"用户问题：{question}\n\n"
            f"知识库参考资料：\n{evidence}"
        )
        try:
            result = self.llm_client.chat_structured(
                FACT_EXTRACTION_PROMPT, user_message, temperature=0.1, max_tokens=2048
            )
            facts = result.get("facts", {})
            logger.info(
                "事实清单已生成 | confirmed=%d uncertain=%d forbidden=%d",
                len(facts.get("confirmed", [])),
                len(facts.get("uncertain", [])),
                len(facts.get("forbidden", [])),
            )
            return result
        except Exception as exc:
            logger.error("事实清单生成失败: %s", exc)
            return {"facts": {"confirmed": [], "uncertain": [], "forbidden": []}}

    def inject_constraint(self, system_prompt: str, fact_list: dict) -> str:
        """将事实锁定约束注入系统提示词。"""
        facts = fact_list.get("facts", {})
        confirmed = facts.get("confirmed", [])
        uncertain = facts.get("uncertain", [])
        forbidden = facts.get("forbidden", [])

        lines = [FACT_LOCK_CONSTRAINT]

        if confirmed:
            lines.append("\n## 可使用的已确认事实")
            for i, f in enumerate(confirmed, 1):
                src = f.get("source_chunk", "?")
                lines.append(f"{i}. {f['fact']}（来源切片 #{src}）")

        if uncertain:
            lines.append("\n## 不确定的事实（如需提及请标注）")
            for i, f in enumerate(uncertain, 1):
                lines.append(f"{i}. {f['fact']}（{f.get('reason', '未知')}）")

        if forbidden:
            lines.append("\n## 禁止扩展的领域")
            for i, f in enumerate(forbidden, 1):
                lines.append(f"{i}. {f['domain']}（{f.get('reason', '未知')}）")

        return system_prompt + "\n".join(lines)

    @staticmethod
    def _format_sources(sources: list[dict]) -> str:
        lines = []
        for s in sources:
            content = s["content"]
            if len(content) > 800:
                content = content[:800] + "…"
            lines.append(
                f"[切片 #{s['chunk_index']}]（来源：《{s['doc_title']}》）\n{content}\n"
            )
        return "\n".join(lines) if lines else "（无参考资料）"
