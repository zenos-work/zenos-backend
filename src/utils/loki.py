import json
import base64
from js import fetch as js_fetch, Headers
from .log_models import LogEntry


class LokiForwarder:
    def __init__(self, url: str, user: str = None, password: str = None):
        self.push_url = f'{url.rstrip("/")}/loki/api/v1/push'
        self.user = user
        self.password = password

    async def push(self, entry: LogEntry) -> None:
        try:
            payload = {
                "streams": [
                    {
                        "stream": {
                            "service": entry.service,
                            "env": entry.env,
                            "level": entry.level,
                            "type": entry.type,
                        },
                        "values": [
                            [
                                str(int(entry.timestamp * 1_000_000_000)),
                                entry.to_json(),
                            ]
                        ],
                    }
                ]
            }
            headers = [("Content-Type", "application/json")]
            if self.user and self.password:
                creds = base64.b64encode(
                    f"{self.user}:{self.password}".encode()
                ).decode()
                headers.append(("Authorization", f"Basic {creds}"))
            await js_fetch(
                self.push_url,
                method="POST",
                headers=Headers.new(headers),
                body=json.dumps(payload),
            )
        except Exception:
            pass  # never let logging failure affect the response
