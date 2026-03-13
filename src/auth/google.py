from js import fetch as js_fetch
from js import Headers
from urllib.parse import urlencode

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


async def exchange_code(code: str, env) -> dict:
    print("Exchanging code")
    # Step 1: exchange code for access token
    req_headers = Headers.new([("Content-Type", "application/x-www-form-urlencoded")])
    body = urlencode(
        {
            "code": code,
            "client_id": env.GOOGLE_CLIENT_ID,
            "client_secret": env.GOOGLE_CLIENT_SECRET,
            "redirect_uri": f"{env.FRONTEND_URL}/auth/google/callback",
            "grant_type": "authorization_code",
        }
    )
    # print(f"Body: {body}")
    resp = await js_fetch(
        GOOGLE_TOKEN_URL, method="POST", headers=req_headers, body=body
    )
    print(f"Response status: {resp.status}")
    token_data = await resp.json()
    # print(f"Token data: {token_data}")

    # Check for token exchange error
    if hasattr(token_data, "error") or not hasattr(token_data, "access_token"):
        return {"error": "Google token exchange failed"}

    access_token = token_data.access_token

    # Step 2: get user info
    user_headers = Headers.new([("Authorization", f"Bearer {access_token}")])
    user_resp = await js_fetch(GOOGLE_USER_URL, headers=user_headers)
    user_data = await user_resp.json()

    # Check for user info error
    if not hasattr(user_data, "id") or not hasattr(user_data, "email"):
        return {"error": "Google auth failed"}

    return {
        "id": user_data.id,
        "email": user_data.email,
        "name": user_data.name,
        "picture": getattr(user_data, "picture", ""),
    }
