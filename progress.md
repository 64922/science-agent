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
| Where am I? | Phase 1 完成，准备 Phase 2（知识库与事实校验，Issues 05-09） |
| Where am I going? | Phase 2: 知识上传→Skill 生成→检索→事实锁定→幻觉抑制 |
| What's the goal? | 构建知己科教 Agent MVP，完整跑通画像-事实-人味化-多模态-评估闭环 |
| What have I learned? | ScenarioRouter 模式正确——4 套场景提示词产生明显不同的回答结构 |
| What have I done? | Phase 1 全部完成（Issues 01-04）：骨架→LLM→对话→场景路由 |

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

---
*每个阶段完成后或遇到错误时更新*
