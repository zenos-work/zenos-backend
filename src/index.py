import json
from js import Response, Headers
from workers import WorkerEntrypoint
from urllib.parse import urlparse
from auth.router import handle_auth


def json_resp(data, status=200):
    headers = Headers.new(
        [
            ("Content-Type", "application/json"),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type,Authorization"),
        ]
    )
    return Response.new(json.dumps(data), status=status, headers=headers)


class Default(WorkerEntrypoint):
    async def on_fetch(self, request):
        env = self.env
        url = urlparse(request.url)
        path = url.path
        method = request.method

        if method == "OPTIONS":
            headers = Headers.new(
                [
                    ("Access-Control-Allow-Origin", "*"),
                    ("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS"),
                    ("Access-Control-Allow-Headers", "Content-Type,Authorization"),
                ]
            )
            return Response.new(None, status=204, headers=headers)

        if path == "/health":
            return json_resp(
                {"status": "ok", "service": "zenos-api", "env": env.ENVIRONMENT}
            )

        if path.startswith("/auth/"):
            return await handle_auth(request, env, path)

        return json_resp({"error": "Not found"}, 404)
