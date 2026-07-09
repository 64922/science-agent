"""风险信号检测与幻觉抑制 —— 对 LLM 回答做规则化后处理，识别高风险表述并降级。"""

import re
import logging

logger = logging.getLogger("risk_detector")

# 绝对化表达模式
ABSOLUTE_PATTERNS = [
    (re.compile(r"所有"), "绝对化 — '所有'"),
    (re.compile(r"一定"), "绝对化 — '一定'"),
    (re.compile(r"完全"), "绝对化 — '完全'"),
    (re.compile(r"必然"), "绝对化 — '必然'"),
    (re.compile(r"绝对(?!值)"), "绝对化 — '绝对'"),
    (re.compile(r"肯定"), "绝对化 — '肯定'"),
    (re.compile(r"毫无疑问"), "绝对化 — '毫无疑问'"),
    (re.compile(r"毋庸置疑"), "绝对化 — '毋庸置疑'"),
    (re.compile(r"总是"), "绝对化 — '总是'"),
    (re.compile(r"从不"), "绝对化 — '从不'"),
    (re.compile(r"永远"), "绝对化 — '永远'"),
]

# 数字/统计相关模式 —— 仅检测有主张性质的数字，排除年份等背景数字
NUMBER_PATTERNS = [
    (re.compile(r"(?:约|大约|近|超过|高达|低至)?\d{1,3}(?:\.\d+)?%"), "具体百分比"),
    (re.compile(r"(?:(?:约|大约|近|超过|高达|低至)\s*)?\d{2,}(?:\s*万|\s*亿|\s*倍)"), "具体数字"),
]

# 医学建议模式 —— 仅匹配建议性表述，不匹配事实陈述
MEDICAL_PATTERNS = [
    (re.compile(r"(?:应该|建议|需要|可以|请)(?:服用|用药|吃药|服药|使用|使用该药)"), "医学建议"),
    (re.compile(r"(?:请遵|谨遵|遵循)医嘱"), "医学建议"),
]

# 实验安全模式
SAFETY_PATTERNS = [
    (re.compile(r"(?:实验|操作)(?:时|中|过程中).{0,15}(?:注意|安全|危险|小心|谨慎)"), "实验安全"),
    (re.compile(r"请(?:佩戴|穿戴|使用)(?:护目镜|手套|防护|口罩|实验服)"), "实验安全"),
    (re.compile(r"(?:避免|防止|禁止)(?:接触|吸入|吞食|直接)"), "实验安全"),
    (re.compile(r"在(?:通风橱|通风处|安全柜)"), "实验安全"),
]

# 因果外推模式（因果词 + 绝对化词组合）
CAUSAL_EXTRAPOLATION = re.compile(
    r"(?:因此|所以|由此可见|这说明|这意味着).{0,30}(?:一定|必然|肯定|所有|完全)"
)

# 降级映射表
DOWNGRADE_MAP = {
    "毫无疑问": "一般认为",
    "毋庸置疑": "目前认为",
    "所有": "大多数",
    "一定": "很可能",
    "完全": "在很大程度上",
    "必然": "通常",
    "绝对": "非常",
    "总是": "通常",
    "从不": "很少",
    "永远": "长期",
}

SENTENCE_SPLIT = re.compile(r"(?<=[。！？!?])(?![」』）\)])")

# 排除降级的否定上下文 —— 否定词后的词不降级
DOWNGRADE_NEGATION = re.compile(r"(?<=不)[一定断然]|(?<=没)[有]")


class RiskDetector:
    """对 LLM 回答做规则化风险检测和过度表达降级。

    检测维度：
    - 绝对化表达（所有、一定、必然...）
    - 具体数字/百分比
    - 医学建议
    - 实验安全表述
    - 因果外推
    """

    def analyze(self, reply: str) -> dict:
        """分析回答文本，返回风险报告。

        Returns:
            {"risks": [...], "repaired_text": str, "risk_count": int}
        """
        sentences = self._split_sentences(reply)
        risks = []
        repaired_sentences = []

        for sent in sentences:
            stripped = sent.strip()
            if not stripped:
                repaired_sentences.append(sent)
                continue

            signals = self._detect_signals(stripped)
            if signals:
                repaired = self._downgrade(stripped)
                risks.append({
                    "sentence": stripped,
                    "signals": signals,
                    "repaired": repaired if repaired != stripped else None,
                })
                repaired_sentences.append(repaired)
            else:
                repaired_sentences.append(sent)

        repaired_text = "".join(repaired_sentences)

        logger.info(
            "风险检测完成 | sentences=%d risks=%d repaired=%d",
            len(sentences), len(risks),
            sum(1 for r in risks if r["repaired"] is not None),
        )

        return {
            "risks": risks,
            "repaired_text": repaired_text if risks else reply,
            "risk_count": len(risks),
        }

    def _split_sentences(self, text: str) -> list[str]:
        """按中文标点拆分句子，保留标点在各自句尾。"""
        parts = SENTENCE_SPLIT.split(text)
        return parts if parts else [text]

    def _detect_signals(self, sentence: str) -> list[str]:
        """检测单句中的风险信号，返回信号标签列表。"""
        signals = []
        for pattern_list in (ABSOLUTE_PATTERNS, NUMBER_PATTERNS, MEDICAL_PATTERNS, SAFETY_PATTERNS):
            self._match_patterns(sentence, pattern_list, signals)
        if CAUSAL_EXTRAPOLATION.search(sentence):
            signals.append("因果外推")
        return signals

    @staticmethod
    def _match_patterns(sentence: str, patterns: list, signals: list) -> None:
        """对一组模式匹配句子，将匹配到的标签去重追加到 signals。"""
        for pattern, label in patterns:
            if pattern.search(sentence) and label not in signals:
                signals.append(label)

    def _downgrade(self, sentence: str) -> str:
        """将过度表述降级为保守表达，跳过否定上下文中的词。"""
        # 先标记否定上下文中不应替换的区间
        protected_ranges = []
        for m in DOWNGRADE_NEGATION.finditer(sentence):
            protected_ranges.append((m.start(), m.end()))

        def _is_protected(pos: int) -> bool:
            return any(start <= pos < end for start, end in protected_ranges)

        result = sentence
        for original, replacement in DOWNGRADE_MAP.items():
            idx = 0
            while True:
                idx = result.find(original, idx)
                if idx == -1:
                    break
                if not _is_protected(idx):
                    result = result[:idx] + replacement + result[idx + len(original):]
                    idx += len(replacement)
                else:
                    idx += len(original)
        return result
