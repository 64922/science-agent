export const CATEGORY_LABELS = {
  basic_info: "基本情况",
  stage_goal: "阶段目标",
  knowledge_level: "知识储备水平",
  interest_preference: "兴趣偏好",
  expression_habit: "表达习惯",
  emotion_trait: "情绪变化特征",
  core_problem: "核心待解决问题",
  authorization_boundary: "信息授权边界",
};

export const CATEGORY_ORDER = Object.keys(CATEGORY_LABELS);

export const AUTH_LABELS = {
  confirmed: "已授权",
  session_only: "仅本轮",
  denied: "已拒绝",
};

export const DEMO_USERS = [
  { id: "demo_user_a", name: "用户 A：高一学生" },
  { id: "demo_user_b", name: "用户 B：大学低年级学生" },
  { id: "demo_user_c", name: "用户 C：科研新手" },
];
