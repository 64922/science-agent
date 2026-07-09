import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# 加载项目根目录的 .env 文件
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

from llm_client import LLMClient, ConfigError, APIError  # noqa: E402
from scenario_router import ScenarioRouter  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("main")


class ChatRequest(BaseModel):
    user_id: str
    message: str
    scenario_id: str = "popular_science"


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
        reply = llm_client.chat(system_prompt, req.message)
    except APIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {
        "reply": reply,
        "user_id": req.user_id,
        "scenario_id": req.scenario_id,
        "scenario_name": scenario["name"],
    }
