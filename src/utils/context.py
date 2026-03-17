import uuid
import time
from utils.logger import Logger


class RequestContext:
    """
    Created once per request. Carries trace_id and a
    pre-configured Logger through handler → service.
    Every log entry for a request shares the same trace_id.
    """

    __slots__ = ("trace_id", "started_at", "log", "request", "env")

    def __init__(self, env, request, user: dict = None):
        self.trace_id = str(uuid.uuid4())
        self.started_at = time.time()
        self.request = request
        self.env = env
        self.log = Logger(
            env=env,
            trace_id=self.trace_id,
            user_id=user["sub"] if user else None,
            user_role=user["role"] if user else None,
        )

    @property
    def elapsed_ms(self) -> float:
        return (time.time() - self.started_at) * 1000
