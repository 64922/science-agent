# Progress Log

## Session: 2026-07-08

### 初始化
- **Status:** complete
- **Started:** 2026-07-08
- Actions taken:
  - 初始化 planning-with-files 规划文件结构
  - 创建 task_plan.md / findings.md / progress.md
- Files created/modified:
  - task_plan.md (created)
  - findings.md (created)
  - progress.md (created)

## Session: 2026-07-09

### 填充任务规划
- **Status:** complete
- **Started:** 2026-07-09
- Actions taken:
  - 根据 docs/product-plan.md 的 24 个 Issue 填充 task_plan.md
  - 更新 findings.md 记录需求和决策
  - 项目进入 Phase 1: 基础骨架与模型接入
- Files created/modified:
  - task_plan.md (rewritten — 7 phases, 24 issues)
  - findings.md (rewritten — populated with requirements and decisions)
  - progress.md (this update)

### Phase 1: 基础骨架与模型接入
- **Status:** complete
- **Issues:** ~~01~~, ~~02~~, ~~03~~, ~~04~~
- Actions taken:
  - **Issue 01 完成**: 创建完整项目骨架
- Files created/modified:
  - backend/main.py (created — FastAPI + /api/health)
  - backend/requirements.txt (created)
  - frontend/package.json (created — Vite + React 18)
  - frontend/vite.config.js (created — proxy /api → :8000)
  - frontend/index.html (created)
  - frontend/src/main.jsx (created)
  - frontend/src/App.jsx (created — 首页展示项目名 + 演示主题 + 3 个演示用户)
  - frontend/src/App.css (created)
  - .env.example (created)
  - README.md (created)
  - data/demo/demo-data.json (created — 演示主题 + 4 场景 + 3 用户)
- Verification:
  - `curl /api/health` → `{"status":"ok","service":"知己科教 Agent","version":"0.1.0"}`
  - `vite build` → 构建成功 (27 modules, 423ms)

### Issue 02: 封装 Qwen / 百炼模型调用客户端
- **Status:** complete
  - llm_client.py: LLMClient 统一封装（chat, chat_structured）
  - call_log.py: CallLog 数据模型
  - main.py: 集成 LLMClient + /api/llm/status 端点
  - 支持 JSON 解析失败自动重试（最多 3 次）
  - 缺少 API Key 时 raise ConfigError，不导致服务崩溃
- Files created/modified:
  - backend/llm_client.py (created)
  - backend/call_log.py (created)
  - backend/main.py (updated — LLMClient 集成)
  - backend/requirements.txt (updated — openai, python-dotenv)
  - README.md (updated — 百炼 API Key 配置说明 + 截图提醒)
- Verification:
  - `curl /api/health` → `{"llm_ready":true}`
  - `curl /api/llm/status` → 返回模型名、调用次数、最近日志
  - chat() 调用成功，日志包含 model_name, call_type, elapsed, success, tokens
  - chat_structured() JSON 输出成功，失败重试机制正常
  - 未配置 API Key 时: ConfigError + 清晰错误信息
  - `vite build` → 构建成功 (27 modules, 373ms)

### Issue 03: 实现基础对话工作台
- **Status:** complete
  - main.py: 新增 `/api/chat` POST 端点（ChatRequest 模型，`user_id`/`message`/`scenario_id`）
  - main.py: `_build_system_prompt()` 通用科教提示词（不含画像，画像归 Phase 3）
  - App.jsx: 对话工作台（消息列表 + 输入框 + 发送按钮 + 加载/错误状态）
  - App.css: 聊天界面样式
  - Enter 发送，自动滚到底部
  - Code review 后裁剪：移除用户/场景选择器（属 Issue 04/10-13）、空状态建议问题
- Files created/modified:
  - backend/main.py (updated — ChatRequest + `/api/chat` + `_build_system_prompt`)
  - frontend/src/App.jsx (rewritten — 对话工作台)
  - frontend/src/App.css (rewritten — 聊天界面样式)
  - README.md (updated — API 表新增 `/api/chat`)
  - findings.md (updated — Issue 03 完成)
- Verification:
  - `POST /api/chat` → 请求解析、LLMClient 调用、错误处理全链路打通
  - `vite build` → 构建成功 (27 modules, 395ms)
  - `/api/health` → `{"llm_ready":true}`
  - 503 (LLM 未就绪) / 502 (API 错误) 错误响应正确

### Issue 04: 场景选择与输出类型路由
- **Status:** complete
- Actions taken:
  - scenario_router.py: ScenarioRouter 加载 demo-data.json 场景配置
  - 4 套场景专属系统提示词（科普/课堂/科研/陪伴），同一问题不同场景生成不同结构回答
  - main.py: 集成 ScenarioRouter，`_build_system_prompt()` 替换为 router 版本
  - main.py: 新增 `GET /api/scenarios` 返回可用场景列表
  - main.py: `/api/chat` 响应新增 `scenario_name` 字段 + 无效 scenario_id 返回 400
  - App.jsx: 场景选择器（4 按钮标签栏）+ 消息角色显示当前场景名称
  - App.css: 场景栏样式
  - test_scenario_router.py: 10 个单元测试（场景加载/配置获取/提示词生成/列表格式）
- Files created/modified:
  - backend/scenario_router.py (created)
  - backend/test_scenario_router.py (created)
  - backend/main.py (updated — ScenarioRouter 集成 + `/api/scenarios` + chat 响应扩展)
  - backend/requirements.txt (updated — pytest)
  - frontend/src/App.jsx (updated — 场景选择器 + 场景名称显示)
  - frontend/src/App.css (updated — 场景栏样式)
- Verification:
  - `pytest test_scenario_router.py -v` → 10 passed
  - `vite build` → 构建成功 (27 modules, 388ms)
  - 4 场景系统提示词均有区分度（科普→生动类比、课堂→提纲+思考题、科研→摘要+证据边界、陪伴→小节+学习建议）

## Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
|      |       |          |        |        |

## Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
|           |       | 1       |            |

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | Phase 4 进行中，Issue 14 完成，Issues 15-16 待做 |
| Where am I going? | Issue 15: 反馈按钮→Issue 16: 迭代日志 |
| What's the goal? | 构建知己科教 Agent MVP，完整跑通画像-事实-人味化-多模态-评估闭环 |
| What have I learned? | HumanizationPipeline 检测部分纯规则引擎（0 额外 LLM 调用），改写部分通过 chat_structured 锁定保护内容后调用 LLM，回归校验确保事实一致性 |
| What have I done? | Issue 14 完成：4 类 AI 痕迹检测 × 3 种风格改写 × 保护内容锁定+校验 × 前端 HumanizationPanel |

### Issue 05: 知识资料上传与文本切分
- **Status:** complete
- **Started:** 2026-07-09
- Actions taken:
  - 创建 `backend/knowledge_store.py`：KnowledgeStore 类，文本清洗 + 段落切分 + JSON 文件持久化
  - 后端新增 3 个端点：`POST /api/knowledge/upload`、`GET /api/knowledge/documents`、`GET /api/knowledge/documents/{id}`
  - 创建 `frontend/src/KnowledgePage.jsx`：知识库管理页（上传按钮 + 文档列表表格）
  - App.jsx 新增"对话 / 知识库"主 Tab 导航
  - requirements.txt 新增 python-multipart 依赖
  - Code review 修复：移除未使用的 hashlib import、移除 source_type 参数、移除 search_chunks（属 Issue 07）
- Files created/modified:
  - backend/knowledge_store.py (created — 186 lines)
  - backend/main.py (updated — 3 new endpoints)
  - backend/requirements.txt (updated — python-multipart)
  - frontend/src/KnowledgePage.jsx (created)
  - frontend/src/KnowledgePage.css (created)
  - frontend/src/App.jsx (updated — tab navigation)
  - frontend/src/App.css (updated — tab styles)
  - README.md (updated — API table)
  - findings.md (updated)
- Verification:
  - POST upload → 200 + document metadata with chunk_count
  - GET documents → 200 + list
  - GET documents/{id} → 200 + chunks with chunk_index + content
  - 400 on invalid extension / empty content
  - 404 on missing document
  - `vite build` → 29 modules, 458ms

### Issue 06: 知识 Skill 生成与来源追踪
- **Status:** complete
- **Started:** 2026-07-09
- Actions taken:
  - 创建 `backend/skill_generator.py`：SkillGenerator 类，调用 Qwen chat_structured 从切片中抽取核心概念/定义/误解/受众
  - 每个知识条目带 `source_chunks` 数组回溯到原始切片，`_validate_and_clean()` 做范围校验
  - 后端新增 3 个端点：`POST generate-skill`、`GET skill`、`GET skills`
  - 前端 KnowledgePage 新增 Skill 状态列（未生成/生成中/已就绪/失败）、生成/查看/重新生成按钮
  - 前端 Skill 详情面板展示 4 类知识点 + 来源切片引用
- Files created/modified:
  - backend/skill_generator.py (created — 175 lines)
  - backend/main.py (updated — 3 new endpoints + SkillGenerator init)
  - frontend/src/KnowledgePage.jsx (rewritten — Skill generation + viewing)
  - frontend/src/KnowledgePage.css (updated — Skill UI styles)
  - README.md (updated — API table)
  - task_plan.md (updated — Issue 06 marked complete)
  - findings.md (updated)
- Verification:
  - SkillGenerator import OK
  - main.py import OK (all 4 modules initialized)
  - `vite build` → 29 modules, 439ms
  - 5/5 Acceptance Criteria met

### Issue 07: 基础知识检索与引用回答
- **Status:** complete
- **Started:** 2026-07-09
- Actions taken:
  - 创建 `backend/knowledge_retriever.py`：KnowledgeRetriever 类，基于 ChromaDB 向量检索
  - 上传文档时自动索引切片到 ChromaDB（upload 端点联动）
  - `/api/chat` 检索 Top 5 相关切片，注入系统提示词作为参考证据
  - 响应新增 `sources` 字段（doc_id, doc_title, chunk_index, content, relevance）
  - `best_distance > 1.85` 阈值判断无证据 → 返回空 sources
  - 前端 App.jsx 新增 `sources` 状态和右侧"本轮引用证据"面板
  - 前端 App.css 两列布局（chat-main + citation-panel），280px 侧栏
  - sources 为空时显示"当前知识库证据不足"
- Files created/modified:
  - backend/knowledge_retriever.py (created — 109 lines)
  - backend/main.py (updated — import + init + _inject_evidence + upload 联动 + chat 检索)
  - backend/requirements.txt (updated — chromadb>=0.5.0)
  - .gitignore (updated — data/chromadb/)
  - frontend/src/App.jsx (updated — sources state + citation panel + 两列布局)
  - frontend/src/App.css (updated — chat-container/chat-main/citation-panel 样式)
  - task_plan.md (updated — Issue 07 marked complete)
  - findings.md (updated)
- Verification:
  - KnowledgeRetriever 初始化成功（import chromadb OK）
  - `main.py` import OK（所有 5 个模块初始化正常）
  - 相关查询 ("T cells immune") → 返回 2 sources
  - 无关查询 ("quantum physics") → 返回 0 sources（证据不足）
  - `vite build` → 构建成功（421ms）
  - 5/5 Acceptance Criteria met

### Code Review: Issue 07 修复 (2026-07-09)
- **Status:** complete
- Actions taken:
  - Standards: 魔术数字 `1.85`/`0.25` → 命名常量 `EVIDENCE_CUTOFF`/`SIBLING_TOLERANCE` + 注释
  - Standards: Primitive Obsession → `ChunkDict`/`SourceDict` TypedDict 定义在 `knowledge_store.py`，`knowledge_retriever.py` 引用
  - Spec: 无关键词回退 → `_keyword_search()` 方法（bigram 分词 + 完整查询加权），`retrieve()` 向量无结果时自动回退
  - Spec: `_inject_evidence` 无 token 预算 → `MAX_EVIDENCE_CHARS=3000` / `MAX_CHUNK_CHARS=800` 截断控制
  - Spec: 初始加载时显示"证据不足" → 增加 `messages.length === 0` 判断，无消息时显示"发送问题后显示引用证据"
  - 移除 SIBLING_TOLERANCE 兄弟过滤（配合关键词回退后不再需要）
- Files modified:
  - backend/knowledge_store.py (+5 lines — ChunkDict TypedDict)
  - backend/knowledge_retriever.py (rewritten — +keyword fallback, +SourceDict, -sibling filter)
  - backend/main.py (+5 lines — MAX_EVIDENCE_CHARS / MAX_CHUNK_CHARS)
  - frontend/src/App.jsx (+2 lines — messages.length check)
  - findings.md (updated)
- Verification:
  - `pytest test_scenario_router.py -v` → 10 passed
  - Keyword search "免疫系统" → 3 results (top relevance=1.0)
  - `vite build` → 构建成功 (412ms)
  - 4/4 code review findings resolved

### Issue 08: 事实清单与事实锁定流程
- **Status:** complete
- **Started:** 2026-07-09
- Actions taken:
  - 创建 `backend/fact_lock.py`：FactLockBuilder 类，调用 Qwen chat_structured 从问题 + 知识库证据中提取结构化事实清单
  - 三类事实分类：confirmed（可确认，引用来源切片）、uncertain（不确定，标注原因）、forbidden（禁止扩展边界）
  - `inject_constraint()` 将事实锁定约束注入系统提示词，核心规则"关键结论必须来自已确认事实列表"
  - main.py: 初始化 FactLockBuilder，改造 `/api/chat` 流程为 先检索→再锁事实→最后生成回答（增加 1 次额外 LLM 调用）
  - `/api/chat` 响应新增 `fact_lock` 字段，日志中自动记录事实清单
  - App.jsx: 新增 `FactLockPanel` 组件 + `factLock` 状态
  - App.css: 三类事实颜色编码（绿=已确认、黄=不确定、红=禁止扩展）
- Files created/modified:
  - backend/fact_lock.py (created — 113 lines)
  - backend/main.py (updated — import + init + chat flow + response)
  - frontend/src/App.jsx (updated — FactLockPanel component + factLock state)
  - frontend/src/App.css (updated — fact lock panel styles)
  - task_plan.md (updated — Issue 08 marked complete)
  - findings.md (updated)
- Verification:
  - FactLockBuilder import OK
  - main.py import OK（所有 6 个模块初始化正常）
  - `pytest test_scenario_router.py -v` → 10 passed（无回归）
  - `vite build` → 构建成功（29 modules, 415ms）
  - 5/5 Acceptance Criteria met

### Issue 09: 风险信号检测与幻觉抑制
- **Status:** complete
- **Started:** 2026-07-09
- Actions taken:
  - 创建 `backend/risk_detector.py`：RiskDetector 类，纯规则引擎（无额外 LLM 调用）
  - 5 类风险检测：绝对化表达（11 个正则模式）、数字/百分比、医学建议、实验安全、因果外推
  - `_repair()` 降级映射：10 组替换规则（"所有"→"大多数"、"一定"→"很可能"等）
  - main.py: 集成 RiskDetector，`/api/chat` 在 LLM 生成回答后执行 `risk_detector.analyze()`
  - `/api/chat` 响应新增 `risk_report` 字段，日志中自动记录风险数量
  - App.jsx: 新增 `RiskPanel` 组件 + `riskReport` 状态
  - App.css: 风险检测结果样式（黄色警告底色、颜色标签区分风险类型、建议修改文本绿色背景）
- Files created/modified:
  - backend/risk_detector.py (created — 123 lines)
  - backend/main.py (updated — import + init + chat flow + response + logging)
  - frontend/src/App.jsx (updated — RiskPanel component + riskReport state)
  - frontend/src/App.css (updated — risk panel styles, ~70 lines)
  - task_plan.md (updated — Issue 09 marked complete, Phase 2 status → complete)
  - findings.md (updated)
- Verification:
  - RiskDetector import OK（所有 7 个模块初始化正常）
  - `pytest test_scenario_router.py -v` → 10 passed（无回归）
  - `vite build` → 构建成功（444ms）
  - 5/5 Acceptance Criteria met
  - Smoke test: 绝对化检测（2/2）、数字检测（2/2）、医学检测（2/2）、干净文本（0）、降级修复（正确替换）
- **Phase 2 全部完成（Issues 05-09）**

### Code Review: Issue 09 修复 (2026-07-09)
- **Status:** complete
- Actions taken:
  - Standards S1: `_detect_signals` 重复循环体 → 提取 `_match_patterns()` 静态方法，消除 4 次重复
  - Standards S2: `.risk-tag-医学` / `.risk-tag-安全` 完全相同的 CSS → 合并选择器
  - Standards S3: `_repair` 用 `str.replace` 误改"不一定" → `_downgrade` 增加 `DOWNGRADE_NEGATION` 否定上下文保护
  - Standards S4: `_repair` 命名不明确 → 重命名为 `_downgrade`
  - Standards S5: `DOWNGRADE_MAP` 为 `list[tuple]` → 改为 `dict` 语义类型
  - Spec P2: 实验安全仅 1 个模式 → 扩展至 4 个模式（护目镜/手套、避免接触、通风橱等）
  - Spec P3: 数字检测过宽（"2024年""25度"误报）→ 收窄为仅检测含约/大约/超过/万/亿/倍的上下文
  - Spec P5: 医学模式把"抗生素用于治疗"事实陈述误标 → 收窄为仅匹配建议性表达（应该/建议/请/遵循医嘱）
  - Spec P1/P4: "无证据"判定和因果外推误匹配 → 纯规则引擎固有局限，非本 Issue 范围，记录不修复
- Files modified:
  - backend/risk_detector.py (rewritten — ~165 lines, all fixes applied)
  - frontend/src/App.css (updated — combined duplicate selectors)
- Verification:
  - "不一定是正确的" 不触发降级（否定保护生效）
  - 实验安全从 1 模式扩展至 4 模式（4/4 检测）
  - 数字检测："约95%"和"超过300万"标记，"2024年""25度"不再误报
  - 医学检测："抗生素用于治疗"不再误报，"你应该服用""遵循医嘱"正确标记
  - AC1 回归：3/3 绝对化表达正常检测
  - `pytest` → 10 passed | `vite build` → 421ms
  - 8/9 findings resolved（1 项设计限制不修复）

### Issue 10: 用户画像 Schema 与画像管理页
- **Status:** complete
- **Started:** 2026-07-10
- Actions taken:
  - 创建 `backend/profile_store.py`：ProfileStore 类，8 类画像字段 CRUD + JSON 文件持久化
  - 后端新增 5 个端点：`GET /api/profile/{user_id}`、`POST`、`PUT`、`DELETE`、`GET /api/profile/{user_id}/categories`
  - 启动时自动从 demo-data.json 种子 3 个演示用户的画像（各 5 条）
  - 创建 `frontend/src/ProfilePage.jsx`：用户选择器 + 按 8 类分组的画像列表 + 添加/编辑/删除
  - App.jsx 新增"我的画像"主 Tab 导航
- Files created/modified:
  - backend/profile_store.py (created — 131 lines)
  - backend/main.py (updated — import + init + seed + 5 endpoints)
  - frontend/src/ProfilePage.jsx (created — 270 lines)
  - frontend/src/ProfilePage.css (created — ~290 lines)
  - frontend/src/App.jsx (updated — import + tab)
  - task_plan.md (updated — Issue 10 marked complete)
  - findings.md (updated)
- Verification:
  - ProfileStore import/init OK（8 类画像字段）
  - main.py import OK（所有 8 个模块初始化正常）
  - `pytest test_scenario_router.py -v` → 10 passed（无回归）
  - `vite build` → 构建成功（31 modules, 416ms）
  - Profile CRUD 冒烟测试：增/查/改/删 全部通过
  - 3 个演示用户各 5 条种子画像正确写入
  - 5/5 Acceptance Criteria met

### Issue 11: 对话中提取画像候选
- **Status:** complete
- **Started:** 2026-07-10
- Actions taken:
  - 创建 `backend/profile_extractor.py`：ProfileExtractor 类，调用 Qwen chat_structured 从用户消息中提取画像候选
  - 8 类画像字段的提取提示词，confidence 阈值 0.3 以下不提取
  - `/api/chat` 每次调用 extract() 返回候选列表（不写入 ProfileStore）
  - 新增 `POST /api/profile/{user_id}/confirm` 端点（remember / session_only / deny 批量处理）
  - App.jsx: 新增 `ProfileCandidateCard` 组件，支持记住/仅本次/不要记/修改后记住 4 种操作
  - App.css: `.profile-candidate-card` / `.pcc-*` 样式（蓝色卡片 + 内联编辑）
- Files created/modified:
  - backend/profile_extractor.py (created — 96 lines)
  - backend/main.py (updated — ProfileExtractor init + chat flow + ConfirmRequest + confirm endpoint)
  - frontend/src/App.jsx (updated — ProfileCandidateCard + profileCandidates state + handleConfirmCandidates)
  - frontend/src/App.css (updated — profile candidate card styles, ~120 lines)
  - frontend/src/constants.js (created — CATEGORY_LABELS, AUTH_LABELS, DEMO_USERS)
- Verification:
  - ProfileExtractor import OK
  - `pytest test_scenario_router.py -v` → 10 passed（无回归）
  - `vite build` → 构建成功
  - 5/5 Acceptance Criteria met
- **Commit:** `bfd5565`

### Issue 12: 画像授权、撤回与暂停记忆
- **Status:** complete
- **Started:** 2026-07-10
- Actions taken:
  - ProfileStore 新增授权管理方法：revoke_profile / revoke_category / set_memory_pause / get_memory_status / get_audit_log / get_authorized_profiles
  - JSONL 审计日志（_{user_id}_audit.jsonl，追加模式）+ 记忆暂停状态文件（_{user_id}_memory.json）
  - `get_authorized_profiles()` 返回 (authorized, skipped) 双列表，过滤逻辑：paused → 全部跳过；revoked/denied → 跳过
  - 后端新增 6 个端点：revoke / revoke-category / memory-pause / memory-resume / memory-status / audit-log
  - `/api/chat` 记录画像跳过日志（profile_skip_log）
  - ProfilePage.jsx: 撤回按钮 + 暂停记忆按钮 + 可折叠审计日志面板
  - 审计日志使用 ACTION_LABELS / ACTION_TARGET 查找表（code review 修复 Repeated Switches）
  - ProfilePage.css: 撤回/暂停/审计日志样式（+178 lines）
- Files created/modified:
  - backend/profile_store.py (updated — +126 lines, 7 new methods + 2 file helpers)
  - backend/main.py (updated — +53 lines, 6 new endpoints + chat skip log)
  - frontend/src/ProfilePage.jsx (updated — +118 lines, revoke/pause/audit UI)
  - frontend/src/ProfilePage.css (updated — +178 lines, new component styles)
  - frontend/src/App.jsx (updated — +17 lines, profileSkipLog state + display)
  - frontend/src/App.css (updated — +22 lines, skip-log styles)
- Verification:
  - `pytest test_scenario_router.py -v` → 10 passed（无回归）
  - `vite build` → 构建成功（32 modules, 433ms）
  - ProfileStore smoke test: 授权/撤回/暂停/审计全部通过
  - Code review: 7 findings → 6 fixed, 1 deferred (authorized for Issue 13)
  - 5/5 Acceptance Criteria met
- **Commit:** `a93f322`

### Issue 13: 画像场景化召回并影响回答
- **Status:** complete
- **Started:** 2026-07-10
- Actions taken:
  - 创建 `backend/profile_retriever.py`：ProfileRetriever 类，场景-类别相关性映射（4 场景 × 8 类别权重矩阵）
  - 5 因素评分公式：场景相关性(0.35) + 置信度(0.25) + 确认权重(0.20) + 新鲜度(0.10) + 偏好权重(0.10)
  - `build_profile_context()` 将召回画像转为可注入系统提示词的文本
  - ProfileStore 新增 `preference_weight` 字段（默认 0.5）+ `adjust_preference_weight()` 方法
  - `/api/chat` 改造：先召回画像 → 注入 system prompt → 生成回答 → 返回 selected_profiles
  - 新增 `POST /api/profile/{user_id}/preference/{profile_id}` 端点（AC5 反馈权重调整）
  - App.jsx: 新增 `selectedProfiles` 状态，"本轮调用画像"面板展示画像 + 调用理由
  - App.css: `.profile-recall-list` / `.profile-recall-item` / `.pr-category` / `.pr-value` / `.pr-reason` 样式
- Files created/modified:
  - backend/profile_retriever.py (created — 140 lines)
  - backend/profile_store.py (updated — preference_weight in create/seed/update + adjust_preference_weight)
  - backend/main.py (updated — ProfileRetriever import/init/chat flow/response + PreferenceFeedback endpoint)
  - frontend/src/App.jsx (updated — selectedProfiles state + capture + recall panel)
  - frontend/src/App.css (updated — profile recall panel styles, ~35 lines)
  - task_plan.md (updated — Issues 11/12/13 marked complete, Phase 3 status → complete)
  - findings.md (updated — Issue 13 completion added, Issues 09-12 context restored)
- Verification:
  - ProfileRetriever import OK
  - main.py import OK（所有 10 个模块初始化正常）
  - `pytest test_scenario_router.py -v` → 10 passed（无回归）
  - `vite build` → 构建成功（32 modules, 456ms）
  - Smoke test: 同一问题不同用户 → 不同画像值召回（demo_user_a 兴趣=航天类比 vs demo_user_b 兴趣=机制图因果链）
  - Smoke test: 不同场景 → 不同排序（popular_science: interest_preference 第一, classroom_teaching: knowledge_level 第一）
  - Smoke test: 偏好权重调整生效（-0.3 → score 从 0.89 降至 0.86）
  - 5/5 Acceptance Criteria met
  - **Phase 3 全部完成（Issues 10-13）**

### Issue 14: 人味化表达检测与改写
- **Status:** complete
- **Started:** 2026-07-10
- Actions taken:
  - 创建 `backend/humanization_pipeline.py`：HumanizationPipeline 类，检测部分纯规则引擎，改写部分 LLM chat_structured
  - 4 类 AI 痕迹检测：模板化开头/总结（7 模式）、过度排比/连接词堆叠（3 模式）、空泛总结（5 模式）、机翻感（3 模式）
  - 保护内容锁定：数字/百分比（含单位）、科学术语（T细胞/B细胞/抗体等）、事实结论（from fact_lock）
  - 3 种风格提示词：课堂老师（分步+引导问题）、科普作者（生动+类比）、科研汇报（克制+证据边界）
  - 场景→风格映射：popular_science→科普作者、classroom_teaching→课堂老师、research_presentation→科研汇报、long_term_companion→课堂老师
  - `_verify_protected()` 回归校验：改写后检查 3 字以上受保护术语是否仍存在
  - LLM 调用失败时降级使用原文，不阻塞对话
  - main.py: HumanizationPipeline 初始化 + `/api/chat` 调用（风险检测后，改写结果覆盖 reply）
  - 响应新增 `humanization_report` 字段
  - App.jsx: HumanizationPanel 组件——场景风格标签/事实一致性/检测到的AI痕迹标签/修改详情列表/受保护内容标签/改写前后对比
  - App.css: 人味化面板完整样式（~200 lines），包含 hz-summary/badge/section/pattern-tags/term-tags/change-list/compare 子组件
- Files created/modified:
  - backend/humanization_pipeline.py (created — 297 lines)
  - backend/main.py (updated — import + init + /api/chat flow + response)
  - frontend/src/App.jsx (updated — HumanizationPanel component + humanizationReport state)
  - frontend/src/App.css (updated — humanization panel styles, ~200 lines)
- Verification:
  - HumanizationPipeline import OK
  - main.py import OK（所有 11 个模块初始化正常）
  - `pytest test_scenario_router.py -v` → 10 passed（无回归）
  - `vite build` → 构建成功（32 modules, 422ms）
  - 规则检测冒烟测试：模板腔 4/4、连接词堆叠 1/1、干净文本 0/0、数字+术语锁定正确
  - 5/5 Acceptance Criteria met
