"""统一模型调用客户端 —— 封装 Qwen / 百炼 API 调用."""

import os
import time
import json
import logging
from openai import OpenAI

from call_log import CallLog, CallType

logger = logging.getLogger("llm_client")


class LLMClientError(Exception):
    pass


class ConfigError(LLMClientError):
    """缺少 API Key 等配置错误。"""


class APIError(LLMClientError):
    """模型 API 调用错误。"""


class LLMClient:
    """统一模型调用封装。

    业务代码通过此类调用模型，不直接接触 API。支持普通对话、
    结构化输出（JSON 模式）、JSON 解析失败自动重试、调用日志记录。
    """

    def __init__(self) -> None:
        self.api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        self.model = os.environ.get("QWEN_MODEL", "qwen-plus")
        self.base_url = os.environ.get(
            "QWEN_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        if not self.api_key:
            raise ConfigError(
                "未配置 DASHSCOPE_API_KEY。请在项目根目录的 .env 文件中设置 "
                "DASHSCOPE_API_KEY=你的百炼APIKey，或设置同名环境变量。"
                "详见 README.md。"
            )

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.call_history: list[CallLog] = []

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        call_type = CallType.CHAT
        start = time.perf_counter()
        success = False
        input_tokens = 0
        output_tokens = 0
        error_message = ""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            success = True
            if response.usage:
                input_tokens = response.usage.prompt_tokens or 0
                output_tokens = response.usage.completion_tokens or 0
            content = response.choices[0].message.content or ""
            return content
        except Exception as exc:
            error_message = str(exc)
            raise APIError(f"模型调用失败: {error_message}") from exc
        finally:
            elapsed = time.perf_counter() - start
            self._log(
                call_type=call_type,
                model=self.model,
                success=success,
                elapsed=elapsed,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                error_message=error_message,
            )

    def chat_structured(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        max_retries: int = 3,
    ) -> dict:
        """结构化输出：要求模型返回 JSON，解析失败时自动重试。"""
        call_type = CallType.STRUCTURED_OUTPUT
        start = time.perf_counter()
        input_tokens = 0
        output_tokens = 0

        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    response_format={"type": "json_object"},
                )
                if response.usage:
                    input_tokens += response.usage.prompt_tokens or 0
                    output_tokens += response.usage.completion_tokens or 0

                raw = response.choices[0].message.content or ""
                result = json.loads(raw)
                if not isinstance(result, dict):
                    raise ValueError("模型输出不是 JSON 对象")

                elapsed = time.perf_counter() - start
                self._log(
                    call_type=call_type,
                    model=self.model,
                    success=True,
                    elapsed=elapsed,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                return result

            except (json.JSONDecodeError, ValueError) as parse_err:
                error_message = str(parse_err)
                self._log(
                    call_type=call_type,
                    model=self.model,
                    success=False,
                    elapsed=time.perf_counter() - start,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    error_message=f"第 {attempt}/{max_retries} 次: {error_message}",
                )
                if attempt < max_retries:
                    logger.warning(
                        "JSON 解析失败（第 %d/%d 次），重试中: %s",
                        attempt,
                        max_retries,
                        error_message,
                    )
                else:
                    raise APIError(
                        f"结构化输出 JSON 解析失败，已重试 {max_retries} 次: {error_message}"
                    ) from parse_err

            except Exception as exc:
                error_message = str(exc)
                elapsed = time.perf_counter() - start
                self._log(
                    call_type=call_type,
                    model=self.model,
                    success=False,
                    elapsed=elapsed,
                    error_message=error_message,
                )
                raise APIError(f"模型调用失败: {error_message}") from exc

    def get_status(self) -> dict:
        return {
            "ready": True,
            "model": self.model,
            "base_url": self.base_url,
            "total_calls": len(self.call_history),
            "recent_calls": [log.to_dict() for log in self.call_history[-20:]],
        }

    def _log(
        self,
        *,
        call_type: CallType,
        model: str,
        success: bool,
        elapsed: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error_message: str = "",
    ) -> None:
        entry = CallLog(
            model_name=model,
            call_type=call_type,
            elapsed_seconds=elapsed,
            success=success,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            error_message=error_message,
        )
        self.call_history.append(entry)
        logger.info(
            "LLM call | type=%s model=%s success=%s elapsed=%.3fs "
            "in=%d out=%d%s",
            call_type.value,
            model,
            success,
            elapsed,
            input_tokens,
            output_tokens,
            f" error={error_message}" if error_message else "",
        )
