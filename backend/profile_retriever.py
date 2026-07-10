"""画像场景化召回器 —— 根据场景、问题和授权状态召回 Top 5 画像。"""

import logging
from datetime import datetime, timezone

from profile_store import PROFILE_CATEGORIES

logger = logging.getLogger("profile_retriever")

# 场景 → 画像类别相关性权重（0-1）
SCENARIO_CATEGORY_WEIGHTS = {
    "popular_science": {
        "interest_preference": 0.9,
        "expression_habit": 0.8,
        "knowledge_level": 0.7,
        "basic_info": 0.5,
        "stage_goal": 0.4,
    },
    "classroom_teaching": {
        "knowledge_level": 0.9,
        "stage_goal": 0.8,
        "core_problem": 0.7,
        "expression_habit": 0.6,
        "basic_info": 0.5,
    },
    "research_presentation": {
        "knowledge_level": 0.9,
        "expression_habit": 0.8,
        "stage_goal": 0.7,
        "core_problem": 0.5,
    },
    "long_term_learning": {
        "stage_goal": 0.9,
        "core_problem": 0.8,
        "emotion_trait": 0.7,
        "knowledge_level": 0.7,
        "interest_preference": 0.6,
        "expression_habit": 0.5,
    },
}

# 默认权重（场景未显式定义的类别）
DEFAULT_CATEGORY_WEIGHT = 0.3

# 召回理由模板
REASON_TEMPLATES = {
    "knowledge_level": "当前问题需要根据用户知识水平调整解释深度",
    "interest_preference": "可用于选择合适的类比和举例方式",
    "expression_habit": "影响回答的表达风格和详略程度",
    "basic_info": "帮助匹配适合用户背景的讲解方式",
    "stage_goal": "当前场景与用户学习目标高度相关",
    "core_problem": "可针对性解决用户的学习卡点",
    "emotion_trait": "帮助调整语气和鼓励方式",
    "authorization_boundary": "确认信息使用边界",
}

TOP_K = 5


class ProfileRetriever:
    """根据场景、授权状态和评分公式召回 Top K 画像。

    评分公式：
        score = 场景相关性 * 0.35 + 置信度 * 0.25 + 确认权重 * 0.20
              + 新鲜度 * 0.10 + 偏好权重 * 0.10
    """

    def retrieve(
        self,
        user_id: str,
        scenario_id: str,
        user_query: str,
        authorized_profiles: list[dict],
    ) -> dict:
        """从已授权画像中召回 Top K 条。

        Returns:
            {"selected_profiles": [...], "rejected_profiles": [...]}
        """
        if not authorized_profiles:
            return {"selected_profiles": [], "rejected_profiles": []}

        weights = SCENARIO_CATEGORY_WEIGHTS.get(scenario_id, {})

        scored = []
        for p in authorized_profiles:
            category_key = p.get("profile_key", "")
            scenario_rel = weights.get(category_key, DEFAULT_CATEGORY_WEIGHT)
            confidence = p.get("confidence", 0.5)

            auth_status = p.get("authorization_status", "confirmed")
            if auth_status == "confirmed":
                confirm_weight = 1.0
            elif auth_status == "session_only":
                confirm_weight = 0.5
            else:
                confirm_weight = 0.3

            freshness = self._calc_freshness(p.get("updated_at", ""))
            pref_weight = p.get("preference_weight", 0.5)

            score = (
                scenario_rel * 0.35
                + confidence * 0.25
                + confirm_weight * 0.20
                + freshness * 0.10
                + pref_weight * 0.10
            )

            scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)

        selected = []
        rejected = []
        for i, (score, p) in enumerate(scored):
            entry = {
                "profile_key": p["profile_key"],
                "profile_value": p["profile_value"],
                "score": round(score, 3),
                "reason": REASON_TEMPLATES.get(
                    p["profile_key"], "该画像与当前场景相关"
                ),
            }
            if i < TOP_K:
                selected.append(entry)
            else:
                rejected.append(entry)

        logger.info(
            "画像召回完成: user=%s scenario=%s authorized=%d selected=%d rejected=%d",
            user_id, scenario_id, len(authorized_profiles),
            len(selected), len(rejected),
        )
        return {"selected_profiles": selected, "rejected_profiles": rejected}

    @staticmethod
    def _calc_freshness(updated_at: str) -> float:
        """计算新鲜度（越近越高，0-1）。"""
        if not updated_at:
            return 0.5
        try:
            dt = datetime.fromisoformat(updated_at)
            now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            days = (now - dt).total_seconds() / 86400
            if days < 1:
                return 1.0
            if days < 7:
                return 0.8
            if days < 30:
                return 0.5
            if days < 90:
                return 0.3
            return 0.1
        except (ValueError, TypeError):
            return 0.5

    def build_profile_context(self, selected_profiles: list[dict]) -> str:
        """将召回画像转为可注入系统提示词的文本。"""
        if not selected_profiles:
            return ""

        lines = [
            "\n\n【用户画像】",
            "以下是根据用户学习背景和偏好匹配的画像信息，请在回答中参考这些信息，调整讲解深度、举例方式和表达风格：\n",
        ]
        for p in selected_profiles:
            label = PROFILE_CATEGORIES.get(p["profile_key"], p["profile_key"])
            lines.append(f"- {label}：{p['profile_value']}（{p['reason']}）")
        return "\n".join(lines)
