import traceback
from urllib.parse import urlparse
from utils.context import RequestContext


async def with_logging(request, env, handler):
    """
    Wraps every request:
    1. Creates RequestContext with trace_id
    2. Logs inbound request
    3. Calls inner handler
    4. Logs response + duration_ms   ← FIX: this was missing
    5. Catches unhandled exceptions → logs + returns 500
    """
    url = urlparse(request.url)
    method = request.method
    path = url.path
    ctx = RequestContext(env, request)

    await ctx.log.request(method, path)

    try:
        response = await handler(ctx)
        status = getattr(response, "status", 200)

        await ctx.log.response(method, path, status, ctx.elapsed_ms)
        return response

    except Exception as exc:
        frames = traceback.extract_tb(exc.__traceback__) if exc.__traceback__ else []
        last_frame = frames[-1] if frames else None
        stack_trace = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )

        await ctx.log.error(
            f"Unhandled exception: {method} {path}",
            exc=exc,
            method=method,
            path=path,
        )
        from utils.helpers import error as err_resp

        details = None
        if getattr(env, "ENVIRONMENT", "production") == "development":
            details = {
                "trace_id": ctx.trace_id,
                "debug": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "file": last_frame.filename if last_frame else None,
                    "line": last_frame.lineno if last_frame else None,
                    "function": last_frame.name if last_frame else None,
                    "stack_trace": stack_trace,
                },
            }

        return err_resp("Internal server error", 500, details=details)
