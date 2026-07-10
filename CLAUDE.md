# CLAUDE.md — 知己科教 Agent

## 项目定位

赛事项目：构建一个能记住用户认知特点、严格锁定科学事实、把专业知识讲得像真人老师一样的科教智能体。

## 技术栈

- **后端**：Python FastAPI（端口 8000）
- **前端**：Vite + React 18（端口 5173，`/api` 代理到后端）
- **基座模型**：千问 Qwen 系列，通过百炼 / DashScope 调用（赛事硬性约束）
- **包管理**：pip（后端）、npm（前端）

## 硬约束（不可违反）

1. 基座模型必须使用千问 Qwen，不得替换为其他模型。
2. 所有模型调用必须通过统一 `LLMClient` 封装（Issue 02 实现），业务代码不得直接调用模型 API。
3. 科学回答必须先锁定事实再生成表达，不得凭空生成科学结论。

## 目录结构

```
frontend/          # Vite + React 18（源码在 src/）
backend/           # FastAPI（main.py 入口）
data/
  demo/            # 演示种子数据
  knowledge/       # 知识库文件
  eval/            # 评估数据集
docs/              # 对外文档（产品方案、评分映射、演示脚本）
finetune/          # 微调数据集、脚本、报告
screenshots/       # 百炼控制台截图
```

## 开发流程

- 使用 planning-with-files 管理任务：`task_plan.md`（路线图）、`findings.md`（发现）、`progress.md`（日志）
- 24 个 Issue 分 7 批顺序执行，当前 Phase 5（Issues 17-19）
- 每个 Issue 完成后必须同步更新规划文件，按以下顺序执行：
  1. `task_plan.md`：勾选 Issue 复选框，Phase 完成时更新 `Current Phase` 和 `Status`
  2. `progress.md`：添加独立的 Issue 条目（Status / Actions / Files / Verification / Commit）
  3. `findings.md`：记录关键技术决策或踩坑经验
- **绝对不要将多个 Issue 合并为一个条目写入 progress.md**，每个 Issue 必须有独立记录。
- 遇见前端UI界面构建的步骤，采取UI UX Pro Max技能构建界面

## 命令速查

```bash
# 后端
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000

# 前端
cd frontend && npm install && npm run dev

# 健康检查
curl http://localhost:8000/api/health
```

## 深入文档

| 文档 | 内容 |
|------|------|
| `docs/product-plan.md` | 完整产品设计（14 模块 + 24 Issue 定义） |
| `task_plan.md` | 任务路线图（7 阶段，当前进度） |
| `data/demo/demo-data.json` | 演示主题 + 4 场景 + 3 用户种子数据 |
