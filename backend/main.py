import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# 加载项目根目录的 .env 文件
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

from llm_client import LLMClient, ConfigError, APIError  # noqa: E402
from scenario_router import ScenarioRouter  # noqa: E402
from knowledge_store import KnowledgeStore  # noqa: E402
from skill_generator import SkillGenerator  # noqa: E402
from knowledge_retriever import KnowledgeRetriever  # noqa: E402
from fact_lock import FactLockBuilder  # noqa: E402
from risk_detector import RiskDetector  # noqa: E402
from profile_store import ProfileStore  # noqa: E402
from profile_extractor import ProfileExtractor  # noqa: E402
from profile_retriever import ProfileRetriever  # noqa: E402
from humanization_pipeline import HumanizationPipeline  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("main")


class ChatRequest(BaseModel):
    user_id: str
    message: str
    scenario_id: str = "popular_science"


MAX_EVIDENCE_CHARS = 3000
MAX_CHUNK_CHARS = 800

EMPTY_FACT_LOCK = {"facts": {"confirmed": [], "uncertain": [], "forbidden": []}}


def _inject_evidence(system_prompt: str, sources: list[dict]) -> str:
    """将检索到的知识切片注入系统提示词作为参考证据。

    总证据量不超过 MAX_EVIDENCE_CHARS，单切片不超过 MAX_CHUNK_CHARS，
    防止溢出模型上下文窗口。
    """
    lines = ["\n\n【知识库参考证据】\n以下是从知识库中检索到的相关资料，请在回答中参考这些事实，并引用来源：\n"]
    total = 0
    for i, s in enumerate(sources, 1):
        content = s["content"]
        if len(content) > MAX_CHUNK_CHARS:
            content = content[:MAX_CHUNK_CHARS] + "…"
        line = f"[{i}]（来源：《{s['doc_title']}》，切片 #{s['chunk_index']}）\n{content}\n"
        if total + len(line) > MAX_EVIDENCE_CHARS:
            break
        lines.append(line)
        total += len(line)
    return system_prompt + "\n".join(lines)


app = FastAPI(title="知己科教 Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 LLMClient；缺少 API Key 时记录警告但不崩溃
llm_client = None
llm_init_error: str | None = None
try:
    llm_client = LLMClient()
    logger.info("LLMClient 初始化成功，模型: %s", llm_client.model)
except ConfigError as exc:
    llm_init_error = str(exc)
    logger.warning("LLMClient 未就绪: %s", llm_init_error)

# 初始化 ScenarioRouter
scenario_router = ScenarioRouter()
logger.info("ScenarioRouter 初始化成功，已加载 %d 个场景", len(scenario_router.list_scenarios()))

# 初始化 KnowledgeStore
knowledge_store = KnowledgeStore()
logger.info("KnowledgeStore 初始化成功，存储目录: %s", knowledge_store.storage_dir)

# 初始化 SkillGenerator（依赖 LLMClient）
skill_generator = None
if llm_client is not None:
    skill_generator = SkillGenerator(llm_client)
    logger.info("SkillGenerator 初始化成功")

# 初始化 FactLockBuilder（依赖 LLMClient）
fact_lock_builder = None
if llm_client is not None:
    fact_lock_builder = FactLockBuilder(llm_client)
    logger.info("FactLockBuilder 初始化成功")

# 初始化 RiskDetector（纯规则引擎，不依赖 LLMClient）
risk_detector = RiskDetector()
logger.info("RiskDetector 初始化成功")

# 初始化 HumanizationPipeline（检测部分规则引擎，改写依赖 LLMClient）
humanization_pipeline = None
if llm_client is not None:
    humanization_pipeline = HumanizationPipeline(llm_client)
    logger.info("HumanizationPipeline 初始化成功")

# 初始化 ProfileStore
profile_store = ProfileStore()
logger.info("ProfileStore 初始化成功，存储目录: %s", profile_store.storage_dir)

# 初始化 ProfileExtractor（依赖 LLMClient）
profile_extractor = None
if llm_client is not None:
    profile_extractor = ProfileExtractor(llm_client)
    logger.info("ProfileExtractor 初始化成功")

# 初始化 ProfileRetriever（纯规则引擎，不依赖 LLMClient）
profile_retriever = ProfileRetriever()
logger.info("ProfileRetriever 初始化成功")

# 种子演示画像（从 demo-data.json 写入，仅在文件不存在时首次写入）
from pathlib import Path as _Path  # noqa: E402
import json as _json  # noqa: E402
_demo_data_path = _Path(__file__).resolve().parent.parent / "data" / "demo" / "demo-data.json"
if _demo_data_path.exists():
    _demo = _json.loads(_demo_data_path.read_text(encoding="utf-8"))
    for _du in _demo.get("demo_users", []):
        _uid = _du["id"]
        if not profile_store.get_profiles(_uid):
            _entries = [
                {"profile_key": "basic_info", "profile_value": _du["profile"]["education_level"]},
                {"profile_key": "knowledge_level", "profile_value": _du["profile"]["knowledge_base"]},
                {"profile_key": "interest_preference", "profile_value": _du["profile"]["interest_preference"]},
                {"profile_key": "expression_habit", "profile_value": _du["profile"]["expression_style"]},
                {"profile_key": "stage_goal", "profile_value": _du["profile"]["current_goal"]},
            ]
            profile_store.seed_demo_profiles(_uid, _entries)
            logger.info("种子画像已写入: user=%s count=%d", _uid, len(_entries))

# 初始化 KnowledgeRetriever（ChromaDB 向量检索）
knowledge_retriever = KnowledgeRetriever(knowledge_store=knowledge_store)
if knowledge_retriever.ready:
    knowledge_retriever.sync_from_store()
else:
    logger.warning("KnowledgeRetriever 未就绪，知识检索功能不可用")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "知己科教 Agent",
        "version": "0.1.0",
        "llm_ready": llm_client is not None,
    }


@app.get("/api/llm/status")
async def llm_status():
    """返回 LLMClient 状态和最近的调用日志。"""
    if llm_client is None:
        return {
            "ready": False,
            "error": llm_init_error or "LLMClient 未初始化",
            "model": os.environ.get("QWEN_MODEL", "qwen-plus"),
        }
    return llm_client.get_status()


@app.get("/api/scenarios")
async def list_scenarios():
    """返回所有可用场景配置。"""
    return {"scenarios": scenario_router.list_scenarios()}


@app.post("/api/knowledge/upload")
async def upload_knowledge(file: UploadFile = File(...)):
    """上传知识资料（.txt / .md），完成清洗和切分后保存。"""
    filename = file.filename or "untitled"
    ext = Path(filename).suffix.lower()
    if ext not in (".txt", ".md", ".markdown"):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型「{ext}」，仅支持 .txt 和 .md",
        )

    try:
        raw = await file.read()
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码不支持，请使用 UTF-8")

    if not content.strip():
        raise HTTPException(status_code=400, detail="文件内容为空")

    doc = knowledge_store.upload(filename, content)
    full_doc = knowledge_store.get_document(doc["id"])
    if full_doc:
        knowledge_retriever.add_document(doc["id"], doc["title"], full_doc.get("chunks", []))
    return {"status": "ok", "document": doc}


@app.get("/api/knowledge/documents")
async def list_knowledge_documents():
    """返回已上传的知识资料列表。"""
    return {"documents": knowledge_store.list_documents()}


@app.get("/api/knowledge/documents/{doc_id}")
async def get_knowledge_document(doc_id: str):
    """获取单个文档的详细信息和所有切片。"""
    doc = knowledge_store.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"document": doc}


@app.post("/api/knowledge/documents/{doc_id}/generate-skill")
async def generate_skill(doc_id: str):
    """为指定文档生成知识 Skill。"""
    if skill_generator is None:
        raise HTTPException(status_code=503, detail="LLM 服务未就绪，无法生成 Skill")
    doc = knowledge_store.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    try:
        result = skill_generator.generate(doc)
        return {"status": "ok", "skill": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Skill 生成失败: {exc}")


@app.get("/api/knowledge/documents/{doc_id}/skill")
async def get_skill(doc_id: str):
    """获取指定文档的已生成 Skill。"""
    if skill_generator is None:
        raise HTTPException(status_code=503, detail="LLM 服务未就绪")
    skill = skill_generator.get_skill(doc_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="该文档尚未生成 Skill")
    return {"skill": skill}


@app.get("/api/knowledge/skills")
async def list_skills():
    """列出所有已生成的 Skill 摘要。"""
    if skill_generator is None:
        return {"skills": []}
    return {"skills": skill_generator.list_skills()}


@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """获取指定用户的全部画像条目。"""
    return {
        "user_id": user_id,
        "profiles": profile_store.get_profiles(user_id),
    }


@app.post("/api/profile/{user_id}")
async def create_profile(user_id: str, entry: dict):
    """新增一条画像条目。"""
    try:
        profile = profile_store.create_profile(user_id, entry)
        return {"status": "ok", "profile": profile}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.put("/api/profile/{user_id}/{profile_id}")
async def update_profile(user_id: str, profile_id: str, updates: dict):
    """更新指定画像条目。"""
    profile = profile_store.update_profile(user_id, profile_id, updates)
    if profile is None:
        raise HTTPException(status_code=404, detail="画像条目不存在")
    return {"status": "ok", "profile": profile}


@app.delete("/api/profile/{user_id}/{profile_id}")
async def delete_profile(user_id: str, profile_id: str):
    """删除指定画像条目。"""
    if not profile_store.delete_profile(user_id, profile_id):
        raise HTTPException(status_code=404, detail="画像条目不存在")
    return {"status": "ok"}


@app.post("/api/profile/{user_id}/revoke/{profile_id}")
async def revoke_profile(user_id: str, profile_id: str):
    """撤回单条画像授权。"""
    profile = profile_store.revoke_profile(user_id, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="画像条目不存在")
    return {"status": "ok", "profile": profile}


@app.post("/api/profile/{user_id}/revoke-category/{category_key}")
async def revoke_category(user_id: str, category_key: str):
    """撤回某类画像的全部授权。"""
    try:
        count = profile_store.revoke_category(user_id, category_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok", "revoked_count": count}


@app.post("/api/profile/{user_id}/memory-pause")
async def pause_memory(user_id: str):
    """暂停全部记忆。"""
    state = profile_store.set_memory_pause(user_id, True)
    return {"status": "ok", "memory_state": state}


@app.post("/api/profile/{user_id}/memory-resume")
async def resume_memory(user_id: str):
    """恢复全部记忆。"""
    state = profile_store.set_memory_pause(user_id, False)
    return {"status": "ok", "memory_state": state}


@app.get("/api/profile/{user_id}/memory-status")
async def memory_status(user_id: str):
    """获取记忆暂停状态。"""
    return {"status": "ok", "memory_state": profile_store.get_memory_status(user_id)}


@app.get("/api/profile/{user_id}/audit-log")
async def audit_log(user_id: str):
    """获取授权变更操作记录。"""
    return {"status": "ok", "entries": profile_store.get_audit_log(user_id)}


class PreferenceFeedback(BaseModel):
    delta: float  # 负值降低权重，正值提升，范围 [-1, 1]


class ConfirmRequest(BaseModel):
    candidates: list[dict]
    action: str  # "remember" | "session_only" | "deny"


@app.post("/api/profile/{user_id}/confirm")
async def confirm_profile_candidates(user_id: str, req: ConfirmRequest):
    """确认画像候选：记住 / 仅本轮 / 拒绝。"""
    if req.action not in ("remember", "session_only", "deny"):
        raise HTTPException(status_code=400, detail=f"无效操作「{req.action}」，仅支持 remember/session_only/deny")

    existing = profile_store.get_profiles(user_id)

    results = []
    for candidate in req.candidates:
        if req.action == "deny":
            results.append({"candidate": candidate, "status": "denied"})
            continue

        # 去重：相同 key+value 已存在则跳过
        dupe = any(
            p["profile_key"] == candidate["profile_key"]
            and p["profile_value"] == candidate["profile_value"]
            for p in existing
        )
        if dupe:
            results.append({"candidate": candidate, "status": "skipped", "detail": "已存在相同画像"})
            continue

        try:
            entry = {
                "profile_key": candidate["profile_key"],
                "profile_value": candidate["profile_value"],
                "evidence": candidate.get("evidence", ""),
                "confidence": 1.0 if req.action == "remember" else candidate.get("confidence", 0.5),
                "authorization_status": "session_only" if req.action == "session_only" else "confirmed",
            }
            profile = profile_store.create_profile(user_id, entry)
            existing.append(profile)
            results.append({"candidate": candidate, "status": "written", "profile": profile})
        except ValueError as exc:
            results.append({"candidate": candidate, "status": "error", "detail": str(exc)})

    logger.info("画像确认: user=%s action=%s count=%d", user_id, req.action, len(req.candidates))
    return {"status": "ok", "results": results}


@app.get("/api/profile/categories")
async def get_profile_categories():
    """返回 8 类画像字段定义，供前端使用。"""
    return {"categories": profile_store.get_categories()}


@app.post("/api/profile/{user_id}/preference/{profile_id}")
async def adjust_preference(user_id: str, profile_id: str, req: PreferenceFeedback):
    """调整画像偏好权重（用户反馈"不喜欢这类例子"时降低权重）。"""
    profile = profile_store.adjust_preference_weight(user_id, profile_id, req.delta)
    if profile is None:
        raise HTTPException(status_code=404, detail="画像条目不存在")
    return {"status": "ok", "profile": profile}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """接收用户消息，调用 LLM 返回科学讲解。"""
    if llm_client is None:
        raise HTTPException(
            status_code=503,
            detail=llm_init_error or "LLM 服务未就绪，请检查 API Key 配置",
        )
    try:
        scenario = scenario_router.get_scenario_config(req.scenario_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        system_prompt = scenario_router.build_system_prompt(
            req.scenario_id, req.user_id
        )
        # 画像召回（Issue 13）
        authorized_profiles, profile_skipped = profile_store.get_authorized_profiles(req.user_id)
        profile_retrieval = profile_retriever.retrieve(
            req.user_id, req.scenario_id, authorized_profiles,
        )
        selected_profiles = profile_retrieval.get("selected_profiles", [])
        if selected_profiles:
            system_prompt = profile_retriever.build_profile_context(selected_profiles) + "\n" + system_prompt
        sources = knowledge_retriever.retrieve(req.message, top_k=5)
        fact_lock = EMPTY_FACT_LOCK
        if sources:
            system_prompt = _inject_evidence(system_prompt, sources)
            if fact_lock_builder is not None:
                fact_lock = fact_lock_builder.build(req.message, sources)
                system_prompt = fact_lock_builder.inject_constraint(system_prompt, fact_lock)
        reply = llm_client.chat(system_prompt, req.message)
        risk_report = risk_detector.analyze(reply)
        humanization_report = None
        scenario_name = scenario["name"]
        if humanization_pipeline is not None:
            humanization_report = humanization_pipeline.rewrite(
                reply, req.scenario_id, scenario_name, fact_lock
            )
            reply = humanization_report["rewritten_text"]
        profile_candidates = []
        if profile_extractor is not None:
            profile_candidates = profile_extractor.extract(req.message)
        profile_skip_log = []
        for s in profile_skipped:
            p = s["profile"]
            profile_skip_log.append({
                "profile_key": p["profile_key"],
                "profile_value": p["profile_value"],
                "reason": f"该画像因未授权未调用（{s['reason']}）",
            })
        logger.info(
            "对话完成 | user=%s scenario=%s sources=%d confirmed=%d uncertain=%d forbidden=%d risks=%d candidates=%d selected=%d skipped=%d reply_len=%d",
            req.user_id, req.scenario_id, len(sources),
            len(fact_lock.get("facts", {}).get("confirmed", [])),
            len(fact_lock.get("facts", {}).get("uncertain", [])),
            len(fact_lock.get("facts", {}).get("forbidden", [])),
            risk_report["risk_count"],
            len(profile_candidates),
            len(selected_profiles),
            len(profile_skip_log),
            len(reply),
        )
    except APIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {
        "reply": reply,
        "user_id": req.user_id,
        "scenario_id": req.scenario_id,
        "scenario_name": scenario_name,
        "sources": sources,
        "fact_lock": fact_lock,
        "risk_report": risk_report,
        "humanization_report": humanization_report,
        "profile_candidates": profile_candidates,
        "profile_skip_log": profile_skip_log,
        "selected_profiles": selected_profiles,
    }
