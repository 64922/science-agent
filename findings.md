# Findings & Decisions

## Requirements
- 赛事项目，基座模型必须使用千问 Qwen 系列（百炼）
- 需要跑通"画像闭环 + 事实校验 + 人味化表达 + 多模态展示 + 评估看板"
- 主演示主题：免疫系统如何识别病毒
- 3 类演示用户：高一学生、大学低年级学生、科研新手
- 4 个标准场景：科普传播、课堂教学、科研展示、长期学习陪伴

## Research Findings
- 项目当前为空仓库，从零开始构建
- docs/product-plan.md 已包含完整的 14 模块产品设计和 24 个 Issue 定义
- 开发分 7 批顺序推进：基础骨架 → 知识库 → 画像 → 人味化 → 学习/多模态 → 评估 → 交付

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| 先做 MVP 可演示项目 | 核心是闭环完整，不是功能广度 |
| 主演示主题：免疫系统如何识别病毒 | 科学性强、适合分层讲解、方便图解 |
| 基座模型：千问 Qwen（百炼/DashScope） | 赛事硬性约束 |
| 开发顺序按 7 批推进 | 每批依赖上一批，降低集成风险 |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
|       |            |

## Resources
- docs/product-plan.md — 完整产品设计文档（14 模块 + 24 Issue）
- task_plan.md — 任务路线图

## Visual/Browser Findings
-
