from typing import Optional
from dataclasses import dataclass, asdict, field
import json
import time


class LogLevel:
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class LogType:
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ANALYTICS = "analytics"
    ERROR = "error"
    DEBUG = "debug"


@dataclass
class LogEntry:
    level: str
    type: str
    message: str
    service: str = "zenos-api"
    env: str = "production"
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    status: Optional[int] = None
    duration_ms: Optional[float] = None
    event_name: Optional[str] = None
    event_data: Optional[dict] = None
    error_type: Optional[str] = None
    error_msg: Optional[str] = None
    error_file: Optional[str] = None
    error_line: Optional[int] = None
    error_function: Optional[str] = None
    error_traceback: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        d = {k: v for k, v in asdict(self).items() if v is not None}
        d["timestamp"] = int(self.timestamp * 1000)
        return json.dumps(d)
