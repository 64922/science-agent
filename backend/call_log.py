"""模型调用日志记录."""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class CallType(str, Enum):
    CHAT = "chat"
    STRUCTURED_OUTPUT = "structured_output"


@dataclass
class CallLog:
    model_name: str
    call_type: CallType
    elapsed_seconds: float
    success: bool
    input_tokens: int = 0
    output_tokens: int = 0
    error_message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "call_type": self.call_type.value,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "success": self.success,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
        }
