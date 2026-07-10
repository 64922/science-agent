"""画像提取器 —— 从对话消息中提取用户画像候选，供用户确认后写入。"""

import logging
from llm_client import LLMClient

logger = logging.getLogger("profile_extractor")

PROFILE_EXTRACTION_PROMPT = """你是一个用户画像分析器。你的任务是：从用户的消息中识别出关于用户自身的信息，并提取为结构化的画像候选。

## 画像类别
1. basic_info（基本情况）：年级、专业、年龄段、学习背景
2. stage_goal（阶段目标）：备考、课堂展示、科研汇报、长期兴趣学习
3. knowledge_level（知识储备水平）：对某一主题的掌握程度
4. interest_preference（兴趣偏好）：喜欢的例子、类比、媒介形式
5. expression_habit（表达习惯）：喜欢简短、详细、图解、故事化、严谨表达
6. emotion_trait（情绪变化特征）：是否容易焦虑、是否需要鼓励
7. core_problem（核心待解决问题）：当前最困扰用户的学习卡点
8. authorization_boundary（信息授权边界）：哪些信息可记忆，哪些禁止使用

## 提取规则
- 只提取用户明确表达的信息，不要过度推断。
- 每条候选必须引用用户原话作为 evidence 字段。
- confidence 取值参考：
  - 0.7-1.0：用户明确自述（如"我是高一学生"）
  - 0.4-0.7：用户较明确表达但未直接声明（如"这个太难了"可推断为基础较弱）
  - 0.3 以下不提取。
- 如果用户没有透露任何新的画像信息，返回空数组。

## 输出格式
返回严格的 JSON 对象，结构如下：
{
  "candidates": [
    {
      "profile_key": "basic_info",
      "profile_value": "高中一年级学生",
      "evidence": "用户说：'我是高一学生'",
      "confidence": 0.95
    }
  ]
}

只输出 JSON，不要有其他文字。"""


class ProfileExtractor:
    """从用户消息中提取画像候选。

    每次 /api/chat 调用 extract() 分析用户消息，
    返回候选列表但不写入 ProfileStore。
    用户在前端确认后由 /api/profile/{user_id}/confirm 写入。
    """

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def extract(self, user_message: str) -> list[dict]:
        """从用户消息中提取画像候选。

        Returns:
            list[dict]: 候选列表，每个包含 profile_key/profile_value/evidence/confidence
        """
        try:
            result = self.llm_client.chat_structured(
                PROFILE_EXTRACTION_PROMPT,
                f"用户消息：{user_message}",
                temperature=0.1,
                max_tokens=1024,
            )
            candidates = result.get("candidates", [])
            valid = [c for c in candidates if self._is_valid(c)]
            if valid:
                logger.info(
                    "画像候选已提取: %d 条 | keys=%s",
                    len(valid),
                    [c["profile_key"] for c in valid],
                )
            return valid
        except Exception as exc:
            logger.error("画像提取失败: %s", exc)
            return []

    @staticmethod
    def _is_valid(candidate: dict) -> bool:
        valid_keys = {
            "basic_info", "stage_goal", "knowledge_level",
            "interest_preference", "expression_habit", "emotion_trait",
            "core_problem", "authorization_boundary",
        }
        return (
            candidate.get("profile_key") in valid_keys
            and isinstance(candidate.get("profile_value"), str)
            and candidate["profile_value"].strip()
            and isinstance(candidate.get("confidence"), (int, float))
            and candidate["confidence"] >= 0.3
        )
