"""反馈路由 —— 根据用户反馈类型触发不同的回答迭代路径。

8 种反馈类型对应 4 条处理路径：
- 重写回答：too_hard / too_shallow / bad_examples / bad_tone
- 强人味化：not_natural / too_ai
- 事实复查：fact_suspect
- 画像修正：profile_wrong
"""

import hashlib
import logging

logger = logging.getLogger("feedback_router")

FEEDBACK_LABELS = {
    "too_hard": "太难了",
    "too_shallow": "太浅了",
    "not_natural": "不够自然",
    "too_ai": "太像 AI",
    "fact_suspect": "事实可疑",
    "bad_examples": "例子不喜欢",
    "bad_tone": "语气不合适",
    "profile_wrong": "画像不对",
}

FEEDBACK_INSTRUCTIONS = {
    "too_hard": (
        "用户反馈刚才的回答「太难了」。请用更简单、更基础的语言重新解释这个主题。"
        "减少专业术语，如果必须使用术语请用括号给出通俗解释。"
        "多用日常生活中的类比，假设听众完全没有专业背景。"
    ),
    "too_shallow": (
        "用户反馈刚才的回答「太浅了」。请深入讲解，增加专业深度和细节。"
        "可以引入更多机制层面的解释和前沿研究发现。"
        "假设听众有一定基础，想要真正理解原理。"
    ),
    "not_natural": (
        "用户反馈表达「不够自然」。请像真人老师一样自然地讲解。"
        "完全避免模板化的书面表达，像是在和学生聊天，不是在写论文或教科书。"
        "可以有语气起伏、口语化的过渡、自然的停顿。"
    ),
    "too_ai": (
        "用户反馈「太像AI写的」。请完全去除AI写作的痕迹。"
        "不要用「首先/其次/再次/最后」「总的来说」「综上所述」等模板结构。"
        "用口语化、有节奏感的语言，像朋友聊天一样自然。"
        "可以打破标准的三段式结构，让表达更有「人味」。"
    ),
    "fact_suspect": (
        "用户对刚才回答的事实准确性提出质疑。请重新严格核查你的回答。"
        "只使用有明确证据支持的结论，不确定的地方请明确标注「目前科学界对此尚有争议」或类似表述。"
        "如果之前的回答有事实性错误，请坦诚纠正。"
    ),
    "bad_examples": (
        "用户不喜欢之前回答中使用的例子。请用完全不同的例子、类比或比喻来重新解释。"
        "不要重复之前用过的任何例子，从另一个角度切入。"
    ),
    "bad_tone": (
        "用户反馈语气不合适。请调整你的语气和表达方式。"
        "考虑当前场景的受众特点，找到更合适的沟通语气和节奏。"
    ),
    "profile_wrong": (
        "用户反馈「画像不对」。系统对用户知识水平或偏好的判断可能有偏差。"
        "请在回答中更灵活地适应用户的实际水平，不要被之前的画像假设限制。"
        "同时在回答末尾附上一句简短说明，推测可能哪里判断有误。"
    ),
}

REWRITE_PATH = {"too_hard", "too_shallow", "bad_examples", "bad_tone"}
REHUMANIZE_PATH = {"not_natural", "too_ai"}
FACT_RECHECK_PATH = {"fact_suspect"}
PROFILE_PATH = {"profile_wrong"}


class FeedbackRouter:
    """根据反馈类型路由到不同的处理路径并生成新回答。"""

    def __init__(self, llm_client):
        self.llm = llm_client
        self.iteration_store: dict[str, list[dict]] = {}

    def route(
        self,
        feedback_type: str,
        message: str,
        current_reply: str,
        scenario_id: str,
        scenario_name: str,
        fact_lock: dict | None,
        sources: list[dict],
        system_prompt: str,
    ) -> dict:
        """根据反馈类型生成迭代后的新回答。"""
        label = FEEDBACK_LABELS.get(feedback_type, feedback_type)
        instruction = FEEDBACK_INSTRUCTIONS.get(
            feedback_type,
            "请根据用户反馈重新生成回答。",
        )

        turn_key = hashlib.md5(
            f"{message}_{scenario_id}".encode()
        ).hexdigest()[:16]
        iterations = self.iteration_store.get(turn_key, [])
        iteration_number = len(iterations) + 1

        # 注入事实锁定约束（所有路径均需遵守）
        if fact_lock and fact_lock != {"facts": {"confirmed": [], "uncertain": [], "forbidden": []}}:
            confirmed = fact_lock.get("facts", {}).get("confirmed", [])
            if confirmed:
                facts_text = "\n".join(f"- {f.get('fact', f)}" for f in confirmed[:10])
                system_prompt += (
                    "\n\n【事实锁定 —— 以下事实必须遵守，不得偏离】\n"
                    f"{facts_text}\n"
                    "回答中不得加入与此冲突的新结论。"
                )

        # 构建反馈增强的系统提示词
        end_constraint = "保持科学准确性，只输出回答文本。"
        if feedback_type == "profile_wrong":
            end_constraint = "保持科学准确性。可以在回答末尾简短推测画像可能的偏差。"

        feedback_prompt = (
            f"{system_prompt}\n\n"
            f"【用户反馈 —— {label}】\n"
            f"{instruction}\n\n"
            f"【上一版回答】\n{current_reply}\n\n"
            f"请根据以上反馈重新生成回答。{end_constraint}"
        )

        llm_error = False
        try:
            new_reply = self.llm.chat(feedback_prompt, message, temperature=0.7)
        except Exception as exc:
            logger.warning("反馈迭代 LLM 调用失败: %s", exc)
            new_reply = current_reply
            llm_error = True

        iteration_record = {
            "iteration_number": iteration_number,
            "feedback_type": feedback_type,
            "feedback_label": label,
            "previous_reply": current_reply,
            "new_reply": new_reply,
        }

        # 存储迭代记录
        if turn_key not in self.iteration_store:
            self.iteration_store[turn_key] = []
        self.iteration_store[turn_key].append(iteration_record)

        logger.info(
            "反馈迭代完成 | type=%s iteration=%d prev_len=%d new_len=%d llm_error=%s",
            feedback_type, iteration_number, len(current_reply), len(new_reply), llm_error,
        )

        return {
            "reply": new_reply,
            "feedback_type": feedback_type,
            "feedback_label": label,
            "iteration_number": iteration_number,
            "previous_reply": current_reply,
            "processing_path": self._get_path(feedback_type),
            "llm_error": llm_error,
        }

    def _get_path(self, feedback_type: str) -> str:
        if feedback_type in REWRITE_PATH:
            return "rewrite"
        if feedback_type in REHUMANIZE_PATH:
            return "rehumanize"
        if feedback_type in FACT_RECHECK_PATH:
            return "fact_recheck"
        return "profile_correction"
