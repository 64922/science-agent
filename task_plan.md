# Task Plan: 知己科教 Agent MVP

## Goal
构建一个可演示的科教智能体 MVP，跑通"画像闭环 + 事实校验 + 人味化表达 + 多模态展示 + 评估看板"完整链路，主演示主题为"免疫系统如何识别病毒"。

## Current Phase
Phase 3

## Phases

### Phase 1: 基础骨架与模型接入 (Issues 01-04)
- [x] **Issue 01**: 初始化项目骨架与演示数据
  - 创建 frontend/backend/data/docs/finetune/screenshots 目录
  - .env.example 包含 DASHSCOPE_API_KEY、QWEN_MODEL、QWEN_BASE_URL
  - README 说明启动步骤
  - 前端首页显示"知己科教 Agent"
  - 后端 /api/health 返回服务状态
- [x] **Issue 02**: 封装 Qwen / 百炼模型调用客户端
  - 统一 LLMClient，支持普通对话、结构化输出、JSON 重试
  - 调用日志记录（模型名、调用类型、耗时、成功状态）
  - 缺少 API Key 时返回清晰错误
- [x] **Issue 03**: 实现基础对话工作台
  - 前端对话输入框、发送按钮、消息列表
  - /api/chat 接收 user_id、message、scenario_id
  - 加载中/失败状态提示
- [x] **Issue 04**: 场景选择与输出类型路由
  - 前端支持 4 个场景选择（科普传播、课堂教学、科研展示、长期学习陪伴）
  - ScenarioRouter 后端实现
  - 同一问题不同场景生成不同结构回答
  - 单元测试覆盖场景路由
- **Status:** complete

### Phase 2: 知识库与事实校验 (Issues 05-09) ← 当前阶段
- [x] **Issue 05**: 知识资料上传与文本切分
  - 知识库管理页
  - 支持 .txt / .md 上传
  - 文本清洗、切分、保存
- [x] **Issue 06**: 知识 Skill 生成与来源追踪
  - 调用 Qwen 抽取核心概念、定义、常见误解、适用受众
  - 每条知识点可追踪到原始切片
  - 前端查看 Skill 内容
- [x] **Issue 07**: 基础知识检索与引用回答
  - /api/chat 检索相关知识切片
  - 前端右侧显示"本轮引用证据"
  - 无相关资料时提示"当前知识库证据不足"
- [x] **Issue 08**: 事实清单与事实锁定流程
  - FactLockBuilder：可确认事实、不确定事实、禁止扩展事实
  - 回答前先生成事实清单，最终回答不加入清单外新结论
  - 前端侧栏显示"事实锁定结果"
- [x] **Issue 09**: 风险信号检测与幻觉抑制
  - 检测绝对化表达、数字、医学建议、因果外推
  - 无证据高风险句标记和修复
  - 前端显示风险检测结果
- **Status:** complete

### Phase 3: 用户画像系统 (Issues 10-13)
- [x] **Issue 10**: 用户画像 Schema 与画像管理页
  - 8 类画像字段（基本情况、阶段目标、知识水平、兴趣偏好、表达习惯、情绪特征、核心问题、授权边界）
  - 每条画像含证据、置信度、授权状态、更新时间
  - 前端"我的画像"页，支持修改和删除
- [ ] **Issue 11**: 对话中提取画像候选
  - ProfileExtractor 从对话中提取候选
  - 前端提供"记住 / 仅本次 / 不要记 / 修改后记住"确认卡片
- [ ] **Issue 12**: 画像授权、撤回与暂停记忆
  - 撤回单条/某类/全部记忆
  - 授权变更有操作记录
- [ ] **Issue 13**: 画像场景化召回并影响回答
  - ProfileRetriever：按场景和授权状态召回 Top 5 画像
  - 同一问题不同画像下回答不同
  - 前端显示"本轮调用画像"
- **Status:** pending

### Phase 4: 人味化与反馈闭环 (Issues 14-16)
- [ ] **Issue 14**: 人味化表达检测与改写
  - HumanizationPipeline：检测模板腔、过度排比、空泛总结、机翻感长句
  - 支持课堂老师、科普作者、科研汇报三种风格
  - 数字、术语、引用、事实结论锁定不可改
  - 前端显示改写报告
- [ ] **Issue 15**: 反馈按钮与回答迭代
  - 8 个反馈按钮（太难、太浅、不够自然、太像 AI、事实可疑、例子不喜欢、语气不合适、画像不对）
  - FeedbackRouter 根据不同反馈触发不同处理路径
- [ ] **Issue 16**: 迭代日志与版本对比展示
  - 回答版本历史 iteration_number
  - 前端对比第一版和最终版
- **Status:** pending

### Phase 5: 长期学习与多模态 (Issues 17-19)
- [ ] **Issue 17**: 长期学习记录与下一课建议
  - 学习记录包含掌握点、困惑点、下一步建议
  - 前端学习档案页
- [ ] **Issue 18**: 小测题与即时反馈 Skill
  - quiz-skill：基于事实清单生成小测题
  - 错题写入学习记录
- [ ] **Issue 19**: 多模态内容生成工坊
  - /api/artifact/generate：知识卡片、课堂讲稿、流程图(Mermaid)、漫画分镜
  - 结果基于事实清单，可复制或下载
- **Status:** pending

### Phase 6: 评估体系与微调预留 (Issues 20-22)
- [ ] **Issue 20**: 评估数据集与自动评估脚本
  - profile_cases.jsonl(30+)、fact_cases.jsonl(30+)、humanization_cases.jsonl(30+)
  - 脚本输出核心指标 JSON
- [ ] **Issue 21**: 评估看板与指标可视化
  - 画像准确率、授权违规率、无证据断言率、人味化自然度、场景适配分
  - 可导出评估报告 HTML
- [ ] **Issue 22**: 微调数据样本与微调预留文档
  - finetune/datasets 至少 200 条 JSONL
  - 覆盖科学问答、人味化改写、画像适配回答
- **Status:** pending

### Phase 7: 演示模式与赛事交付 (Issues 23-24)
- [ ] **Issue 23**: 演示模式页面
  - 按固定步骤展示完整闭环
  - 一键加载演示用户和演示资料
  - 可重置演示数据
  - docs/demo-script.md 与页面步骤一致
- [ ] **Issue 24**: 横向对比报告与评分映射文档
  - docs/open-source-comparison.md 对比 7 个参考项目
  - docs/scoring-map.md 覆盖科学价值、技术深度、应用潜力
- **Status:** pending

## Key Questions
1. ~~前端技术栈选型~~ → Vite + React 18
2. ~~后端技术栈选型~~ → Python FastAPI
3. ~~向量数据库选型（ChromaDB / Milvus / FAISS？）~~ → ChromaDB
4. 是否使用百炼平台的原生 API 还是 DashScope SDK？
5. ~~演示用户数据是纯前端 mock 还是后端种子数据？~~ → JSON 种子数据 (data/demo/demo-data.json)

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 主演示主题：免疫系统如何识别病毒 | 科学性强、适合分层讲解、方便做图解和漫画 |
| 基座模型：千问 Qwen 系列（百炼） | 赛事硬性约束 |
| MVP 优先跑通闭环，不全领域覆盖 | 演示价值 > 功能广度 |
| 前端：Vite + React 18 | 轻量、生态成熟、后续 Issue 无需重写 |
| 后端：Python FastAPI | 异步支持好、DashScope SDK 兼容、AI 项目标准选型 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       |         |            |

## Notes
- 24 个 Issue 分 7 批顺序执行，每批内可适当并行
- 随进度更新阶段状态: pending → in_progress → complete
- 重要决策前重新阅读此计划
- 永远不要重复失败的操作 — 改用不同方法
