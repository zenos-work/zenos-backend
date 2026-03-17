from utils.loki import LokiForwarder
from utils.elk import ElkForwarder


def make_forwarder(env):
    """
    Returns configured forwarder. Priority: ELK_URL > LOKI_URL > None.
    Now returns None gracefully so logging falls back to stdout only.
    """
    elk_url = getattr(env, "ELK_URL", None)
    if elk_url:
        return ElkForwarder(
            url=elk_url,
            index=getattr(env, "ELK_INDEX", "zenos-logs"),
            api_key=getattr(env, "ELK_API_KEY", None),
        )

    loki_url = getattr(env, "LOKI_URL", None)
    if loki_url:
        return LokiForwarder(
            url=loki_url,
            user=getattr(env, "LOKI_USER", None),
            password=getattr(env, "LOKI_PASSWORD", None),
        )

    return None  # stdout only — no secrets needed
