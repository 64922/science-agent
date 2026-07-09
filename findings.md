# Findings & Decisions

## Requirements
- 赛事项目，基座模型必须使用千问 Qwen 系列（百炼）
- 需要跑通"画像闭环 + 事实校验 + 人味化表达 + 多模态展示 + 评估看板"
- 主演示主题：免疫系统如何识别病毒
- 3 类演示用户：高一学生、大学低年级学生、科研新手
- 4 个标准场景：科普传播、课堂教学、科研展示、长期学习陪伴

## Research Findings
- 项目于 2026-07-08 从空仓库初始化，当前 Phase 1（Issues 01-04）
- Issue 01 完成：项目骨架、FastAPI + React、演示数据就绪
- Issue 02 完成：LLMClient 统一封装，通过 OpenAI SDK 调用百炼 Qwen
- Issue 03 完成：基础对话工作台（/api/chat + 前端聊天界面），系统提示词不含画像注入，画像和场景选择器归后续 Issue
- Issue 04 完成：ScenarioRouter 加载 demo-data.json 4 个场景配置，每个场景有独立系统提示词（科普→生动类比、课堂→提纲+思考题、科研→摘要+证据边界、陪伴→小节+学习建议），前端场景选择器标签栏 + 消息显示场景名称，10 个单元测试全部通过
- Phase 1（Issues 01-04）全部完成，项目进入 Phase 2：知识库与事实校验
- docs/product-plan.md 已包含完整的 14 模块产品设计和 24 个 Issue 定义
- 开发分 7 批顺序推进：基础骨架 → 知识库 → 画像 → 人味化 → 学习/多模态 → 评估 → 交付

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| 先做 MVP 可演示项目 | 核心是闭环完整，不是功能广度 |
| 主演示主题：免疫系统如何识别病毒 | 科学性强、适合分层讲解、方便图解 |
| 基座模型：千问 Qwen（百炼/DashScope） | 赛事硬性约束 |
| LLM 调用使用 OpenAI SDK + DashScope 兼容 API | 百炼提供 `/compatible-mode/v1` 端点，OpenAI SDK 生态成熟 |
| JSON 结构化输出失败自动重试（最多 3 次） | Qwen 偶发非 JSON 输出，重试可显著提高可靠性 |
| 调用日志内存存储（CallLog dataclass） | MVP 阶段无数据库依赖，后续可迁入持久化存储 |
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
