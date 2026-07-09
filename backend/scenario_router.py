"""场景路由器 —— 根据 scenario_id 返回不同风格的提示词和输出结构."""

import json
from pathlib import Path
from typing import Optional

SCENARIO_PROMPTS = {
    "popular_science": (
        "你正在以科普传播的方式讲解科学知识。你的听众是普通大众。\n"
        "请用以下方式组织你的回答：\n"
        "1. 用生动易懂的语言解释核心概念\n"
        "2. 使用生活中的类比帮助理解\n"
        "3. 保持短段落，适合移动端阅读\n"
        "4. 语气亲切自然，像在和朋友聊天\n"
        "5. 适当加入“你可以这样理解...”的引导语"
    ),
    "classroom_teaching": (
        "你正在以课堂教学的方式讲解科学知识。你的听众是学生。\n"
        "请用以下方式组织你的回答：\n"
        "1. 先列出本课的知识点提纲\n"
        "2. 分步骤讲解，每步标注关键概念\n"
        "3. 在容易误解的地方给出「易错提醒」\n"
        "4. 结尾提出 2-3 个思考题供学生巩固\n"
        "5. 语气像一位有经验的老师，耐心但专业"
    ),
    "research_presentation": (
        "你正在以科研展示的方式讲解科学知识。你的听众是科研同行或评委。\n"
        "请用以下方式组织你的回答：\n"
        "1. 先给出核心结论的摘要（3-5 句话）\n"
        "2. 使用专业术语，保持严谨\n"
        "3. 标注证据来源和研究边界\n"
        "4. 区分“已确认”与“仍在研究”的内容\n"
        "5. 语气克制、准确，适合用于组会或学术汇报"
    ),
    "long_term_learning": (
        "你正在以长期学习陪伴的方式讲解科学知识。你的目标是帮助学习者逐步构建知识体系。\n"
        "请用以下方式组织你的回答：\n"
        "1. 先回顾与本话题相关的基础知识（如果适用）\n"
        "2. 将新知识拆分为可消化的小节\n"
        "3. 在关键点询问用户是否理解，鼓励提问\n"
        "4. 根据用户的掌握程度建议下一步学习方向\n"
        "5. 语气温暖有分寸，像一位陪伴学习成长的导师"
    ),
}


class ScenarioRouter:
    """根据场景 ID 返回场景配置和对应的系统提示词。"""

    def __init__(self, data_path: Optional[Path] = None) -> None:
        self.scenarios = self._load_scenarios(data_path)

    def _load_scenarios(self, data_path: Optional[Path] = None) -> list[dict]:
        if data_path is None:
            data_path = (
                Path(__file__).resolve().parent.parent
                / "data" / "demo" / "demo-data.json"
            )
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("scenarios", [])

    def get_scenario_config(self, scenario_id: str) -> dict:
        for s in self.scenarios:
            if s["id"] == scenario_id:
                return s
        known = [s["id"] for s in self.scenarios]
        raise ValueError(
            f"未知场景: {scenario_id}，可用场景: {', '.join(known)}"
        )

    def build_system_prompt(self, scenario_id: str, user_id: str) -> str:
        scenario = self.get_scenario_config(scenario_id)
        scenario_prompt = SCENARIO_PROMPTS.get(scenario_id, "")

        return (
            '你是"知己"，一个专业的科教智能体。'
            '你的任务是围绕"免疫系统如何识别病毒"这一主题，'
            "用科学、准确的方式回答用户的问题。\n\n"
            f"当前场景：{scenario['name']}\n"
            f"{scenario_prompt}\n\n"
            "请用流畅自然的中文回答，根据问题的难度调整讲解深度。"
        )

    def list_scenarios(self) -> list[dict]:
        return [
            {"id": s["id"], "name": s["name"], "style": s.get("style", "")}
            for s in self.scenarios
        ]
