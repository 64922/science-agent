"""人味化表达检测与改写 —— 检测AI痕迹并按场景风格改写科学回答。

流程：锁定不可改内容 -> 检测AI痕迹 -> LLM按风格改写 -> 回归校验。
检测部分为纯规则引擎（无额外LLM调用），改写部分调用LLM chat_structured。
"""

import re
import logging
from llm_client import LLMClient

logger = logging.getLogger("humanization")

# === AI 痕迹检测模式 ===

TEMPLATE_PATTERNS = [
    (re.compile(r"在当今[时代社会]"), "模板化开头"),
    (re.compile(r"总的?来说"), "模板化总结"),
    (re.compile(r"需要注意的[是]"), "模板化表达"),
    (re.compile(r"综上[所述]"), "模板化总结"),
    (re.compile(r"总的?而言"), "模板化总结"),
    (re.compile(r"众所[周知]"), "模板化开头"),
    (re.compile(r"不可否认[的]*，"), "模板化表达"),
]

PARALLELISM_PATTERNS = [
    (re.compile(r"不仅.{0,20}而且.{0,20}(?:同时|此外)"), "过度排比"),
    (re.compile(r"首先.{0,30}其次.{0,30}(?:再次|最后)"), "逻辑连接词堆叠"),
    (re.compile(r"一方面.{0,30}另一方面"), "过度排比"),
]

VAGUE_SUMMARY_PATTERNS = [
    (re.compile(r"具有重要[的]*(?:意义|价值|作用)"), "空泛总结"),
    (re.compile(r"值得深入[研究探讨]"), "空泛总结"),
    (re.compile(r"产生了深远[的]*影响"), "空泛总结"),
    (re.compile(r"为.{0,10}(?:做出|作出)了.{0,10}贡献"), "空泛总结"),
    (re.compile(r"在.{0,15}(?:领域|方面)(?:具有|发挥).{0,10}(?:作用|价值)"), "空泛总结"),
]

MACHINE_TRANSLATION_PATTERNS = [
    (re.compile(r"(?:被.{0,10}(?:所|给|用于))"), "机翻感被动句"),
    (re.compile(r"(?:[^。！？!?\n]{60,})"), "机翻感长句"),
    (re.compile(r"(?:(?:\S+的){3,})"), "机翻感定语堆叠"),
]

CONNECTOR_STACKING = re.compile(
    r"(?:首先|第一|其一)[^。！？\n]*?[。！？]?\s*"
    r"(?:其次|第二|其二)[^。！？\n]*?[。！？]?\s*"
    r"(?:再次|第三|其三)[^。！？\n]*?[。！？]?\s*"
    r"(?:最后|第四|其四)"
)

# === 不可修改内容锁定 ===

NUMBER_LOCK = re.compile(r"(?:\d{2,}\s*[万亿倍]|\d+(?:\.\d+)?%|\d{2,})")

TERM_LOCK = re.compile(
    r"(?:[A-Z]{2,}(?:\s*[细胞因子受体蛋白])?|"
    r"T细胞|B细胞|NK细胞|DNA|RNA|mRNA|PCR|CRISPR|"
    r"抗原|抗体|免疫|病毒|细菌|细胞|基因|蛋白|酶|受体|"
    r"免疫系统|免疫记忆|免疫反应|免疫细胞|"
    r"抗原呈递|抗原递呈|T淋巴细胞|B淋巴细胞)"
)

# === 风格定义 ===

STYLE_LABELS = {
    "teacher": "课堂老师",
    "science_writer": "科普作者",
    "research": "科研汇报",
}

STYLE_GUIDES = {
    "teacher": (
        "课堂老师风格：分步骤讲解，像在和学生对话。在关键处停顿提醒学生容易误解的地方。"
        "可以用「你注意到了吗？」「有没有想过为什么？」这类引导性问题。"
        "科学事实保持准确，但表达像真人老师讲课，有语气起伏和节奏感。"
    ),
    "science_writer": (
        "科普作者风格：自然流畅、有画面感、有阅读节奏，但不夸张不煽情。"
        "用生动的类比帮助理解，但类比不能替代科学准确性。"
        "像一篇好的科普文章，既专业又易懂，读起来像人在讲故事而非机器在列清单。"
    ),
    "research": (
        "科研汇报风格：克制、准确、有证据边界。使用专业术语但给出简短定义。"
        "明确区分「已知结论」和「推测」，留出讨论空间。"
        "适合组会汇报或学术交流，严谨但不晦涩，逻辑清晰。"
    ),
}

SCENARIO_TO_STYLE = {
    "popular_science": "science_writer",
    "classroom_teaching": "teacher",
    "research_presentation": "research",
    "long_term_companion": "teacher",
}

REWRITE_SYSTEM_PROMPT = """你是一个科教文本人味化改写专家。你的任务是将AI生成的回答改写得更自然、更像真人。

【核心约束——违反即为失败】
1. 以下受保护的术语和数字必须原样保留，一字不改：
{protected_terms}
2. 不得添加新的事实结论或科学断言
3. 不得改变原文的科学含义
4. 引用来源标注必须保留

【需要移除的AI痕迹】
{detected_patterns}

【目标风格要求】
{style_guide}

【输出格式】
返回严格的 JSON 对象：
{{
  "rewritten_text": "改写后的完整文本",
  "changes": [
    {{"type": "移除模板腔", "before": "原片段", "after": "改写后"}}
  ],
  "fact_changed": false
}}

只输出 JSON，不要有其他文字。"""


class HumanizationPipeline:
    """检测AI痕迹并按场景风格改写科学回答。

    检测部分为纯规则引擎（无额外LLM调用），
    改写部分调用LLM chat_structured 生成结构化结果。
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def detect(self, text: str) -> dict:
        """检测AI痕迹，返回问题标签列表和具体位置。"""
        findings = []

        for pattern, label in TEMPLATE_PATTERNS:
            for m in pattern.finditer(text):
                findings.append({
                    "pattern": label,
                    "text": m.group(),
                    "position": m.start(),
                })

        for pattern, label in PARALLELISM_PATTERNS:
            for m in pattern.finditer(text):
                findings.append({
                    "pattern": label,
                    "text": m.group()[:40],
                    "position": m.start(),
                })

        for pattern, label in VAGUE_SUMMARY_PATTERNS:
            for m in pattern.finditer(text):
                findings.append({
                    "pattern": label,
                    "text": m.group(),
                    "position": m.start(),
                })

        for pattern, label in MACHINE_TRANSLATION_PATTERNS:
            for m in pattern.finditer(text):
                snippet = m.group()
                if len(snippet) > 50:
                    snippet = snippet[:50] + "..."
                findings.append({
                    "pattern": label,
                    "text": snippet,
                    "position": m.start(),
                })

        if CONNECTOR_STACKING.search(text):
            findings.append({
                "pattern": "逻辑连接词堆叠",
                "text": "首先...其次...再次...最后",
                "position": 0,
            })

        unique_patterns = list(dict.fromkeys(f["pattern"] for f in findings))

        logger.info(
            "AI痕迹检测完成 | findings=%d patterns=%s",
            len(findings), unique_patterns,
        )

        return {
            "findings": findings,
            "detected_patterns": unique_patterns,
            "ai_trace_count": len(findings),
        }

    def _lock_protected(self, text: str, fact_lock: dict | None) -> list[str]:
        """提取需要保护的内容：数字、术语、事实结论。"""
        protected = []

        for m in NUMBER_LOCK.finditer(text):
            val = m.group()
            if val not in protected:
                protected.append(val)

        for m in TERM_LOCK.finditer(text):
            term = m.group().strip()
            if term and term not in protected:
                protected.append(term)

        if fact_lock:
            for fact in fact_lock.get("facts", {}).get("confirmed", []):
                fact_text = fact.get("fact", "")
                if fact_text and fact_text not in protected:
                    protected.append(fact_text)

        return protected

    def rewrite(
        self,
        original: str,
        scenario_id: str,
        scenario_name: str,
        fact_lock: dict | None,
    ) -> dict:
        """检测AI痕迹并按场景风格改写。"""
        detection = self.detect(original)
        protected_terms = self._lock_protected(original, fact_lock)
        style = SCENARIO_TO_STYLE.get(scenario_id, "science_writer")
        style_name = STYLE_LABELS.get(style, style)
        style_guide = STYLE_GUIDES.get(style, STYLE_GUIDES["science_writer"])

        protected_str = "\n".join(
            f"- {t}" for t in protected_terms[:20]
        ) or "（无特殊保护内容）"
        detected_str = "\n".join(
            f"- {p}" for p in detection["detected_patterns"]
        ) or "（未检测到明显AI痕迹）"

        system_prompt = REWRITE_SYSTEM_PROMPT.format(
            protected_terms=protected_str,
            detected_patterns=detected_str,
            style_guide=style_guide,
        )

        user_message = (
            f"当前场景：{scenario_name}\n"
            f"目标风格：{style_name}\n\n"
            f"【原始文本】\n{original}\n\n"
            "请改写上述文本，保留所有科学事实不变。"
        )

        try:
            result = self.llm.chat_structured(
                system_prompt, user_message, temperature=0.5, max_tokens=2048,
            )
        except Exception as exc:
            logger.warning("人味化改写LLM调用失败: %s，使用原文", exc)
            result = {
                "rewritten_text": original,
                "changes": [],
                "fact_changed": False,
            }

        rewritten = result.get("rewritten_text", original)
        llm_fact_changed = result.get("fact_changed", False)

        verified_ok = self._verify_protected(original, rewritten, protected_terms)
        fact_changed = llm_fact_changed or (not verified_ok)

        report = {
            "original_preview": original[:200] + ("..." if len(original) > 200 else ""),
            "rewritten_text": rewritten,
            "rewritten_preview": rewritten[:200] + ("..." if len(rewritten) > 200 else ""),
            "detected_patterns": detection["detected_patterns"],
            "ai_trace_count": detection["ai_trace_count"],
            "style_applied": style_name,
            "preserved_terms": protected_terms[:10],
            "changes": result.get("changes", []),
            "fact_changed": fact_changed,
        }

        logger.info(
            "人味化改写完成 | style=%s patterns=%d terms=%d fact_changed=%s",
            style, len(detection["detected_patterns"]), len(protected_terms), fact_changed,
        )

        return report

    def _verify_protected(self, original: str, rewritten: str, protected: list[str]) -> bool:
        """验证保护内容在改写后仍然存在（3字以上的术语检查）。"""
        for term in protected:
            if len(term) >= 3 and term in original and term not in rewritten:
                logger.warning("受保护术语在改写后丢失: %s", term)
                return False
        return True
