import json
from js import fetch as js_fetch, Headers
from .log_models import LogEntry


class ElkForwarder:
    def __init__(self, url, index="zenos-logs", api_key=None):
        self.bulk_url = f'{url.rstrip("/")}/_bulk'
        self.index = index
        self.api_key = api_key

    async def push(self, entry: LogEntry) -> None:
        try:
            action = json.dumps({"index": {"_index": self.index}})
            doc = entry.to_json()
            headers = [("Content-Type", "application/x-ndjson")]
            if self.api_key:
                headers.append(("Authorization", f"ApiKey {self.api_key}"))
            await js_fetch(
                self.bulk_url,
                method="POST",
                headers=Headers.new(headers),
                body=f"{action}\n{doc}\n",
            )
        except Exception:
            pass
