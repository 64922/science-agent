# Findings & Decisions

## Requirements
- 赛事项目，基座模型必须使用千问 Qwen 系列（百炼）
- 需要跑通"画像闭环 + 事实校验 + 人味化表达 + 多模态展示 + 评估看板"
- 主演示主题：免疫系统如何识别病毒
- 3 类演示用户：高一学生、大学低年级学生、科研新手
- 4 个标准场景：科普传播、课堂教学、科研展示、长期学习陪伴

## Research Findings
- 项目于 2026-07-08 从空仓库初始化，当前 Phase 4（Issues 14-16）
- Issue 01 完成：项目骨架、FastAPI + React、演示数据就绪
- Issue 02 完成：LLMClient 统一封装，通过 OpenAI SDK 调用百炼 Qwen
- Issue 03 完成：基础对话工作台（/api/chat + 前端聊天界面），系统提示词不含画像注入，画像和场景选择器归后续 Issue
- Issue 04 完成：ScenarioRouter 加载 demo-data.json 4 个场景配置，每个场景有独立系统提示词（科普→生动类比、课堂→提纲+思考题、科研→摘要+证据边界、陪伴→小节+学习建议），前端场景选择器标签栏 + 消息显示场景名称，10 个单元测试全部通过
- Phase 1（Issues 01-04）全部完成，项目进入 Phase 2：知识库与事实校验
- Issue 05 完成：KnowledgeStore 按段落切分（`\n\n`）+ 长段落按句子边界二次切分（max 2000 字符），JSON 文件持久化到 `data/knowledge/`，前端通过主 Tab "知识库" 进入管理页
- Issue 06 完成：SkillGenerator 调用 Qwen chat_structured 从切片中抽取核心概念/定义/误解/受众，每条知识点带 source_chunks 回溯，结果持久化为 `{doc_id}_skill.json`，前端 Skill 详情面板支持查看和重新生成
- Issue 07 完成：KnowledgeRetriever 基于 ChromaDB 实现向量检索 + 关键词回退（bigram 分词 + 完整查询命中加权），上传文档自动索引，/api/chat 注入检索证据到系统提示词（MAX_EVIDENCE_CHARS=3000 / MAX_CHUNK_CHARS=800 预算控制），前端右侧新增"本轮引用证据"面板。ChromaDB 默认 all-MiniLM-L6-v2 嵌入模型对中文内容距离偏大，采用 EVIDENCE_CUTOFF=1.85 阈值判断无证据。ChunkDict / SourceDict TypedDict 消除 Primitive Obsession。code review 4 项全部修复：魔术数字命名化、关键词回退、TypedDict、token 预算
- Issue 08 完成：FactLockBuilder 调用 Qwen chat_structured 从知识库资料中提取结构化事实清单（confirmed / uncertain / forbidden 三类），约束注入系统提示词确保最终回答不超出锁定边界。每次 /api/chat 先锁事实再生成回答，增加一次额外 LLM 调用。前端侧栏"事实锁定结果"以颜色标签区分三类事实。
- Issue 09 完成：RiskDetector 纯规则引擎，无需额外 LLM 调用。覆盖 5 类风险：绝对化表达（11 个正则模式）、具体数字/百分比、医学建议、实验安全、因果外推。检测到高风险句后通过 DOWNGRADE_MAP 自动降级。前端侧栏"风险检测结果"以颜色标签区分风险类型，并展示建议修改文本。Phase 2 全部完成。
- Issue 10 完成：ProfileStore 实现 8 类画像字段的完整 CRUD，JSON 文件按用户 ID 分文件存储。启动时自动从 demo-data.json 为 3 个演示用户各写入 5 条种子画像。前端"我的画像"页支持用户切换、按类别分组查看、添加/修改/删除操作。
- Issue 11 完成：ProfileExtractor 调用 Qwen chat_structured 从用户消息中提取画像候选，前端弹出确认卡片（记住/仅本次/不要记/修改后记住）。`/api/profile/{user_id}/confirm` 批量处理确认操作。
- Issue 12 完成：ProfileStore 授权管理层（revoke_profile / revoke_category / set_memory_pause / get_authorized_profiles），6 个新 API 端点，JSONL 审计日志，前端撤回按钮 + 暂停记忆 + 授权变更记录面板。`get_authorized_profiles()` 返回 (authorized, skipped) 双列表供 Issue 13 使用。
- Issue 13 完成：ProfileRetriever 按场景-类别相关性映射 + 5 因素评分公式召回 Top 5 已授权画像，注入系统提示词影响回答。新增 `preference_weight` 字段和 `adjust_preference_weight()` 方法支持反馈闭环（AC5）。前端"本轮调用画像"面板展示召回画像和调用理由。
- docs/product-plan.md 已包含完整的 14 模块产品设计和 24 个 Issue 定义
- 开发分 7 批顺序推进：基础骨架 → 知识库 → 画像 → 人味化 → 学习/多模态 → 评估 → 交付

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| 先做 MVP 可演示项目 | 核心是闭环完整，不是功能广度 |
| 主演示主题：免疫系统如何识别病毒 | 科学性强、适合分层讲解、方便图解 |
| 基座模型：千问 Qwen（百炼/DashScope） | 赛事硬性约束 |
| 向量数据库选型 ChromaDB | 轻量嵌入、元数据过滤友好、Python 原生，适合 MVP 阶段的知识检索 + Phase 3 画像召回 |
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
