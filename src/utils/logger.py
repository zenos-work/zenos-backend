import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from utils.forwarder import make_forwarder


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
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        d = {k: v for k, v in asdict(self).items() if v is not None}
        d["timestamp"] = int(self.timestamp * 1000)
        return json.dumps(d)


class Logger:
    def __init__(self, env, trace_id=None, user_id=None, user_role=None):
        self._env_name = getattr(env, "ENVIRONMENT", "production")
        self._trace_id = trace_id
        self._user_id = user_id
        self._user_role = user_role
        self._fwd = make_forwarder(env)

    def _build(self, level, type_, message, **kw) -> LogEntry:
        return LogEntry(
            level=level,
            type=type_,
            message=message,
            env=self._env_name,
            trace_id=self._trace_id,
            user_id=self._user_id,
            user_role=self._user_role,
            **kw,
        )

    async def _emit(self, entry: LogEntry) -> None:
        print(entry.to_json())
        if self._fwd:
            await self._fwd.push(entry)

    async def debug(self, msg, **kw):
        if self._env_name == "development":
            await self._emit(self._build(LogLevel.DEBUG, LogType.DEBUG, msg, **kw))

    async def info(self, msg, **kw):
        await self._emit(self._build(LogLevel.INFO, LogType.EVENT, msg, **kw))

    async def warn(self, msg, **kw):
        await self._emit(self._build(LogLevel.WARN, LogType.EVENT, msg, **kw))

    async def error(self, msg, exc: Exception = None, **kw):
        await self._emit(
            self._build(
                LogLevel.ERROR,
                LogType.ERROR,
                msg,
                error_type=type(exc).__name__ if exc else None,
                error_msg=str(exc) if exc else None,
                **kw,
            )
        )

    async def request(self, method, path, **kw):
        await self._emit(
            self._build(
                LogLevel.INFO,
                LogType.REQUEST,
                f"{method} {path}",
                method=method,
                path=path,
                **kw,
            )
        )

    async def response(self, method, path, status, duration_ms, **kw):
        level = LogLevel.WARN if status >= 400 else LogLevel.INFO
        await self._emit(
            self._build(
                level,
                LogType.RESPONSE,
                f"{method} {path} {status}",
                method=method,
                path=path,
                status=status,
                duration_ms=round(duration_ms, 2),
                **kw,
            )
        )

    async def event(self, name, data=None, **kw):
        await self._emit(
            self._build(
                LogLevel.INFO,
                LogType.EVENT,
                name,
                event_name=name,
                event_data=data or {},
                **kw,
            )
        )

    async def analytics(self, name, data=None, **kw):
        await self._emit(
            self._build(
                LogLevel.INFO,
                LogType.ANALYTICS,
                name,
                event_name=name,
                event_data=data or {},
                **kw,
            )
        )
