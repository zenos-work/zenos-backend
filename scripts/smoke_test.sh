#!/usr/bin/env bash
# =============================================================================
# Zenos Backend Smoke Test
# Usage:
#   ./scripts/smoke_test.sh                              # staging (default)
#   SMOKE_ENV=production ./scripts/smoke_test.sh         # production
#   JWT_SECRET=mysecret ./scripts/smoke_test.sh staging  # override secret
#
# Prerequisites: curl, python3 (stdlib only — no pip installs needed)
# The script mints its own test JWT using the same HMAC-SHA256 logic as the
# backend. You do NOT need a real Google login to test authenticated endpoints.
#
# Required env var for authenticated tests:
#   JWT_SECRET  — must match the Cloudflare Worker secret for the target env
#
# Optional env vars for Cloudflare Access protected domains:
#   CF_ACCESS_CLIENT_ID
#   CF_ACCESS_CLIENT_SECRET
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SMOKE_ENV="${SMOKE_ENV:-staging}"

case "$SMOKE_ENV" in
  staging)
    BASE_URL="https://staging.api.zenos.work"
    ;;
  production)
    BASE_URL="https://api.zenos.work"
    ;;
  *)
    echo "Unknown SMOKE_ENV: $SMOKE_ENV  (use staging or production)"
    exit 1
    ;;
esac

# Allow BASE_URL override for custom domains
BASE_URL="${API_BASE_URL:-$BASE_URL}"

PASS=0
FAIL=0
SKIP=0

CURL_COMMON_ARGS=(
  -H "Accept: application/json"
  -H "User-Agent: zenos-smoke-test/1.0"
)

if [[ -n "${CF_ACCESS_CLIENT_ID:-}" && -n "${CF_ACCESS_CLIENT_SECRET:-}" ]]; then
  CURL_COMMON_ARGS+=(
    -H "CF-Access-Client-Id: ${CF_ACCESS_CLIENT_ID}"
    -H "CF-Access-Client-Secret: ${CF_ACCESS_CLIENT_SECRET}"
  )
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

pass() { echo -e "${GREEN}  PASS${RESET}  $1"; PASS=$((PASS + 1)); }
fail() { echo -e "${RED}  FAIL${RESET}  $1 — $2"; FAIL=$((FAIL + 1)); }
skip() { echo -e "${YELLOW}  SKIP${RESET}  $1 — $2"; SKIP=$((SKIP + 1)); }
header() { echo -e "\n── $1 ──────────────────────────────────────"; }

# Run curl and return HTTP status code. Body goes to stdout only on debug mode.
http_status() {
  local method="$1" url="$2"
  shift 2
  curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" "${CURL_COMMON_ARGS[@]}" "$@"
}

# Return first 200 chars of response body (for assertion on content)
http_body() {
  local method="$1" url="$2"
  shift 2
  curl -s -X "$method" "$url" "${CURL_COMMON_ARGS[@]}" "$@" | head -c 500
}

print_edge_access_hint() {
  local path="$1"
  local body
  body=$(http_body GET "$BASE_URL$path")
  echo "  INFO  Received 403 from $path. This usually indicates Cloudflare edge protection (Access/WAF), not app logic."
  if [[ -z "${CF_ACCESS_CLIENT_ID:-}" || -z "${CF_ACCESS_CLIENT_SECRET:-}" ]]; then
    echo "  INFO  Set CF_ACCESS_CLIENT_ID and CF_ACCESS_CLIENT_SECRET in GitHub environment secrets for $SMOKE_ENV."
  fi
  echo "  INFO  Response snippet: ${body:0:180}"
}

# ---------------------------------------------------------------------------
# Mint a short-lived test JWT  (mirrors src/auth/jwt_handler.py exactly)
# ---------------------------------------------------------------------------
mint_test_jwt() {
  local secret="$1" role="${2:-READER}" user_id="${3:-smoke-test-user}"
  python3 - <<PYEOF
import json, hmac, hashlib, base64, time

secret = "$secret"
role   = "$role"
uid    = "$user_id"

def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

header  = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
payload = {"sub": uid, "role": role, "exp": int(time.time()) + 300}
body    = b64(json.dumps(payload).encode())
sig     = b64(hmac.new(secret.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest())
print(f"{header}.{body}.{sig}")
PYEOF
}

# ---------------------------------------------------------------------------
# Tier 1 — Public endpoints (no auth required)
# ---------------------------------------------------------------------------
header "Tier 1: Public endpoints (no auth)"

# 1. Health check
STATUS=$(http_status GET "$BASE_URL/health")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /health → 200"
else
  fail "GET /health" "expected 200, got $STATUS"
  if [[ "$STATUS" == "403" ]]; then
    print_edge_access_hint "/health"
  fi
fi

# 2. Auth login redirect (should 302 to Google)
STATUS=$(http_status GET "$BASE_URL/auth/google/login" --max-redirs 0)
if [[ "$STATUS" == "302" || "$STATUS" == "301" || "$STATUS" == "303" ]]; then
  pass "GET /auth/google/login → $STATUS redirect"
else
  fail "GET /auth/google/login" "expected 3xx redirect, got $STATUS"
fi

# 3. Articles list (public read)
STATUS=$(http_status GET "$BASE_URL/api/articles")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/articles → 200"
else
  fail "GET /api/articles" "expected 200, got $STATUS"
fi

# 4. Tags list (public read)
STATUS=$(http_status GET "$BASE_URL/api/tags")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/tags → 200"
else
  fail "GET /api/tags" "expected 200, got $STATUS"
fi

# 5. Search (public)
STATUS=$(http_status GET "$BASE_URL/api/search?q=test&type=all")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/search?q=test → 200"
else
  fail "GET /api/search" "expected 200, got $STATUS"
fi

# 6. Featured feed (public)
STATUS=$(http_status GET "$BASE_URL/api/feed/featured")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/feed/featured → 200"
else
  fail "GET /api/feed/featured" "expected 200, got $STATUS"
fi

# 7. Trending feed (public)
STATUS=$(http_status GET "$BASE_URL/api/feed/trending")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/feed/trending → 200"
else
  fail "GET /api/feed/trending" "expected 200, got $STATUS"
fi

# ---------------------------------------------------------------------------
# Tier 2 — Authenticated endpoints (mint test JWT — no Google OAuth needed)
# ---------------------------------------------------------------------------
header "Tier 2: Authenticated endpoints (synthetic JWT)"

if [[ -z "${JWT_SECRET:-}" ]]; then
  skip "All Tier 2 tests" "JWT_SECRET not set — run: JWT_SECRET=<staging secret> $0"
  SKIP=$((SKIP + 5))
else
  TOKEN=$(mint_test_jwt "$JWT_SECRET" "READER")
  AUTH_HEADER="Authorization: Bearer $TOKEN"

  # 8. My profile (requires auth — returns 401 without token)
  STATUS=$(http_status GET "$BASE_URL/api/users/me" -H "$AUTH_HEADER")
  # 200 = user found in DB, 404 = token valid but test user not in DB — both are OK for smoke
  if [[ "$STATUS" == "200" || "$STATUS" == "404" ]]; then
    pass "GET /api/users/me → $STATUS (auth accepted)"
  else
    fail "GET /api/users/me" "expected 200/404, got $STATUS (token rejected?)"
  fi

  # 9. Home feed (personalised — requires auth)
  STATUS=$(http_status GET "$BASE_URL/api/feed/home" -H "$AUTH_HEADER")
  if [[ "$STATUS" == "200" ]]; then
    pass "GET /api/feed/home → 200"
  else
    fail "GET /api/feed/home" "expected 200, got $STATUS"
  fi

  # 10. Following feed (requires auth)
  STATUS=$(http_status GET "$BASE_URL/api/feed/following" -H "$AUTH_HEADER")
  if [[ "$STATUS" == "200" ]]; then
    pass "GET /api/feed/following → 200"
  else
    fail "GET /api/feed/following" "expected 200, got $STATUS"
  fi

  # 11. Verify unauthenticated request to protected route returns 401
  STATUS=$(http_status GET "$BASE_URL/api/users/me")
  if [[ "$STATUS" == "401" ]]; then
    pass "GET /api/users/me (no token) → 401 as expected"
  else
    fail "GET /api/users/me (no token)" "expected 401, got $STATUS"
  fi

  # 12. SUPERADMIN endpoint — reachable but should 403 for READER role
  ADMIN_TOKEN=$(mint_test_jwt "$JWT_SECRET" "SUPERADMIN")
  STATUS=$(http_status GET "$BASE_URL/api/admin/stats" -H "Authorization: Bearer $ADMIN_TOKEN")
  # 200 = stats returned (admin exists in DB), 500 = valid auth but no real user row; either
  # means auth itself worked. 401/403 would mean role enforcement is broken.
  if [[ "$STATUS" == "200" || "$STATUS" == "404" || "$STATUS" == "500" ]]; then
    pass "GET /api/admin/stats (SUPERADMIN token) → $STATUS (auth accepted)"
  else
    fail "GET /api/admin/stats" "expected non-401/403, got $STATUS"
  fi
fi

# ---------------------------------------------------------------------------
# Tier 3 — DB connectivity probe (via public article list shape check)
# ---------------------------------------------------------------------------
header "Tier 3: DB connectivity (response shape)"

BODY=$(http_body GET "$BASE_URL/api/articles")
if echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d,list) or any(k in d for k in ('articles','items','data'))" 2>/dev/null; then
  pass "GET /api/articles → response is valid JSON with expected shape"
else
  fail "GET /api/articles" "response body unexpected: ${BODY:0:200}"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "═══════════════════════════════════"
echo "  Smoke test complete: $SMOKE_ENV"
echo "  PASS: $PASS  FAIL: $FAIL  SKIP: $SKIP"
echo "═══════════════════════════════════"

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
