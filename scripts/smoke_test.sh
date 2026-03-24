#!/usr/bin/env bash
# =============================================================================
# Zenos Backend Smoke Test
# Usage:
#   ./scripts/smoke_test.sh                              # staging (default)
#   SMOKE_ENV=local ./scripts/smoke_test.sh              # local dev server
#   SMOKE_ENV=production ./scripts/smoke_test.sh         # production
#   JWT_SECRET=mysecret ./scripts/smoke_test.sh          # override secret
#   API_BASE_URL=http://localhost:8787 SMOKE_ENV=local ./scripts/smoke_test.sh
#
# Environments:
#   local      → http://127.0.0.1:8787  JWT_SECRET auto-read from .env
#   staging    → https://staging.api.zenos.work
#   production → https://api.zenos.work
#
# Prerequisites: curl, python3 (stdlib only — no pip installs needed)
# The scr
ipt mints its own test JWT using the same HMAC-SHA256 logic as the
# backend. You do NOT need a real Google login to test authenticated endpoints.
#
# Required env var for authenticated tests (staging/production only):
#   JWT_SECRET  — must match the Cloudflare Worker secret for the target env
#                 (auto-read from .env when SMOKE_ENV=local)
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
  local)
    BASE_URL="http://127.0.0.1:8787"
    ;;
  staging)
    BASE_URL="https://staging.api.zenos.work"
    ;;
  production)
    BASE_URL="https://api.zenos.work"
    ;;
  *)
    echo "Unknown SMOKE_ENV: $SMOKE_ENV  (use local, staging, or production)"
    exit 1
    ;;
esac

# Allow BASE_URL override for custom ports etc.
BASE_URL="${API_BASE_URL:-$BASE_URL}"

# ---------------------------------------------------------------------------
# Auto-resolve JWT_SECRET for local runs
# ---------------------------------------------------------------------------
# When running locally, read JWT_SECRET from .env so authenticated Tier 3+
# tests run automatically without requiring the caller to set it manually.
if [[ "$SMOKE_ENV" == "local" && -z "${JWT_SECRET:-}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  ENV_FILE="${SCRIPT_DIR}/../.env"
  if [[ -f "$ENV_FILE" ]]; then
    JWT_SECRET=$(grep -E '^JWT_SECRET=' "$ENV_FILE" | head -1 | cut -d'=' -f2- | tr -d '"'"'" | xargs)
    if [[ -n "$JWT_SECRET" ]]; then
      echo "  INFO  JWT_SECRET auto-loaded from .env for local smoke test"
    fi
  fi
fi

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
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

pass() { echo -e "${GREEN}  PASS${RESET}  $1"; PASS=$((PASS + 1)); }
fail() { echo -e "${RED}  FAIL${RESET}  $1 — $2"; FAIL=$((FAIL + 1)); }
skip() { echo -e "${YELLOW}  SKIP${RESET}  $1 — $2"; SKIP=$((SKIP + 1)); }
header() { echo -e "\n${CYAN}${BOLD}── $1 ──────────────────────────────────────${RESET}"; }

# Print response body alongside FAIL line — avoids needing wrangler tail.
fail_with_body() {
  local label="$1" reason="$2" method="${3:-GET}" url="$4"
  fail "$label" "$reason"
  local body
  body=$(curl -s -X "$method" "$url" "${CURL_COMMON_ARGS[@]}" | head -c 300)
  echo -e "         body: ${body}"
}

# Return HTTP status code only.
http_status() {
  local method="$1" url="$2"
  shift 2
  curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" "${CURL_COMMON_ARGS[@]}" "$@"
}

# Return short body snippet (for error hints).
http_body_snippet() {
  local method="$1" url="$2"
  shift 2
  curl -s -X "$method" "$url" "${CURL_COMMON_ARGS[@]}" "$@" | head -c 500
}

# Return full response body.
http_body_full() {
  local method="$1" url="$2"
  shift 2
  curl -s -X "$method" "$url" "${CURL_COMMON_ARGS[@]}" "$@"
}

print_edge_access_hint() {
  local path="$1"
  local body
  body=$(http_body_snippet GET "$BASE_URL$path")
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
  fail_with_body "GET /api/articles" "expected 200, got $STATUS" GET "$BASE_URL/api/articles"
fi

# 4. Articles list filtered by content_type
STATUS=$(http_status GET "$BASE_URL/api/articles?content_type=article")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/articles?content_type=article → 200"
else
  fail_with_body "GET /api/articles?content_type=article" "expected 200, got $STATUS" GET "$BASE_URL/api/articles?content_type=article"
fi

# 5. Articles list with search param
STATUS=$(http_status GET "$BASE_URL/api/articles?search=test")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/articles?search=test → 200"
else
  fail_with_body "GET /api/articles?search=test" "expected 200, got $STATUS" GET "$BASE_URL/api/articles?search=test"
fi

# 6. Content types list
STATUS=$(http_status GET "$BASE_URL/api/articles/content-types")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/articles/content-types → 200"
else
  fail_with_body "GET /api/articles/content-types" "expected 200, got $STATUS" GET "$BASE_URL/api/articles/content-types"
fi

# 7. Tags list (public read)
STATUS=$(http_status GET "$BASE_URL/api/tags")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/tags → 200"
else
  fail "GET /api/tags" "expected 200, got $STATUS"
fi

# 8. Search — all types
STATUS=$(http_status GET "$BASE_URL/api/search?q=test&type=all")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/search?q=test&type=all → 200"
else
  fail_with_body "GET /api/search?q=test&type=all" "expected 200, got $STATUS" GET "$BASE_URL/api/search?q=test&type=all"
fi

# 9. Search — articles only
STATUS=$(http_status GET "$BASE_URL/api/search?q=test&type=articles")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/search?q=test&type=articles → 200"
else
  fail_with_body "GET /api/search?q=test&type=articles" "expected 200, got $STATUS" GET "$BASE_URL/api/search?q=test&type=articles"
fi

# 10. Search — tags only
STATUS=$(http_status GET "$BASE_URL/api/search?q=test&type=tags")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/search?q=test&type=tags → 200"
else
  fail_with_body "GET /api/search?q=test&type=tags" "expected 200, got $STATUS" GET "$BASE_URL/api/search?q=test&type=tags"
fi

# 11. Search — authors only
STATUS=$(http_status GET "$BASE_URL/api/search?q=test&type=authors")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/search?q=test&type=authors → 200"
else
  fail_with_body "GET /api/search?q=test&type=authors" "expected 200, got $STATUS" GET "$BASE_URL/api/search?q=test&type=authors"
fi

# 12. Search — invalid short query returns 400
STATUS=$(http_status GET "$BASE_URL/api/search?q=x")
if [[ "$STATUS" == "400" ]]; then
  pass "GET /api/search?q=x → 400 (too short, expected)"
else
  fail "GET /api/search?q=x" "expected 400, got $STATUS"
fi

# 13. Featured feed (public)
STATUS=$(http_status GET "$BASE_URL/api/feed/featured")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/feed/featured → 200"
else
  fail "GET /api/feed/featured" "expected 200, got $STATUS"
fi

# 14. Trending feed (public)
STATUS=$(http_status GET "$BASE_URL/api/feed/trending")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/feed/trending → 200"
else
  fail "GET /api/feed/trending" "expected 200, got $STATUS"
fi

# ---------------------------------------------------------------------------
# Tier 2 — Auth guard checks (no token → must 401)
# ---------------------------------------------------------------------------
header "Tier 2: Auth guard checks (unauthenticated → 401)"

# 15. Users/me without token
STATUS=$(http_status GET "$BASE_URL/api/users/me")
if [[ "$STATUS" == "401" ]]; then
  pass "GET /api/users/me (no token) → 401"
else
  fail "GET /api/users/me (no token)" "expected 401, got $STATUS"
fi

# 16. Home feed without token — returns 200 (public general feed; personalised when authed)
STATUS=$(http_status GET "$BASE_URL/api/feed/home")
if [[ "$STATUS" == "200" ]]; then
  pass "GET /api/feed/home (no token) → 200 (public general feed OK)"
else
  fail_with_body "GET /api/feed/home (no token)" "expected 200, got $STATUS" GET "$BASE_URL/api/feed/home"
fi

# 17. Following feed without token
STATUS=$(http_status GET "$BASE_URL/api/feed/following")
if [[ "$STATUS" == "401" ]]; then
  pass "GET /api/feed/following (no token) → 401"
else
  fail "GET /api/feed/following (no token)" "expected 401, got $STATUS"
fi

# 18. Create article without token
STATUS=$(http_status POST "$BASE_URL/api/articles" \
  -H "Content-Type: application/json" \
  -d '{"title":"test","content":"test"}')
if [[ "$STATUS" == "401" ]]; then
  pass "POST /api/articles (no token) → 401"
else
  fail "POST /api/articles (no token)" "expected 401, got $STATUS"
fi

# 19. Admin stats without token
STATUS=$(http_status GET "$BASE_URL/api/admin/stats")
if [[ "$STATUS" == "401" ]]; then
  pass "GET /api/admin/stats (no token) → 401"
else
  fail "GET /api/admin/stats (no token)" "expected 401, got $STATUS"
fi

# ---------------------------------------------------------------------------
# Tier 3 — Authenticated endpoints (READER role JWT)
# ---------------------------------------------------------------------------
header "Tier 3: Authenticated endpoints (READER role)"

if [[ -z "${JWT_SECRET:-}" ]]; then
  skip "All Tier 3 tests" "JWT_SECRET not set — set JWT_SECRET or use SMOKE_ENV=local (reads from .env)"
  SKIP=$((SKIP + 7))
else
  TOKEN=$(mint_test_jwt "$JWT_SECRET" "READER" "smoke-reader-$$")
  AUTH="-H \"Authorization: Bearer $TOKEN\""

  # 20. My profile — 200 (user in DB) or 404 (token valid, no user row)
  STATUS=$(http_status GET "$BASE_URL/api/users/me" -H "Authorization: Bearer $TOKEN")
  if [[ "$STATUS" == "200" || "$STATUS" == "404" ]]; then
    pass "GET /api/users/me (READER) → $STATUS (auth accepted)"
  else
    fail_with_body "GET /api/users/me (READER)" "expected 200/404, got $STATUS" GET "$BASE_URL/api/users/me"
  fi

  # 21. Home feed (personalised)
  STATUS=$(http_status GET "$BASE_URL/api/feed/home" -H "Authorization: Bearer $TOKEN")
  if [[ "$STATUS" == "200" ]]; then
    pass "GET /api/feed/home (READER) → 200"
  else
    fail_with_body "GET /api/feed/home" "expected 200, got $STATUS" GET "$BASE_URL/api/feed/home"
  fi

  # 22. Following feed
  STATUS=$(http_status GET "$BASE_URL/api/feed/following" -H "Authorization: Bearer $TOKEN")
  if [[ "$STATUS" == "200" ]]; then
    pass "GET /api/feed/following (READER) → 200"
  else
    fail_with_body "GET /api/feed/following" "expected 200, got $STATUS" GET "$BASE_URL/api/feed/following"
  fi

  # 23. My articles
  STATUS=$(http_status GET "$BASE_URL/api/articles/mine" -H "Authorization: Bearer $TOKEN")
  if [[ "$STATUS" == "200" ]]; then
    pass "GET /api/articles/mine (READER) → 200"
  else
    fail_with_body "GET /api/articles/mine" "expected 200, got $STATUS" GET "$BASE_URL/api/articles/mine"
  fi

  # 24. Create article with READER role — must 403 (only AUTHOR+ can write)
  STATUS=$(http_status POST "$BASE_URL/api/articles" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title":"smoke test article","content":"smoke test content"}')
  if [[ "$STATUS" == "403" ]]; then
    pass "POST /api/articles (READER) → 403 (write guard OK)"
  else
    fail "POST /api/articles (READER)" "expected 403, got $STATUS"
  fi

  # 25. Admin stats with READER token — must 403
  STATUS=$(http_status GET "$BASE_URL/api/admin/stats" -H "Authorization: Bearer $TOKEN")
  if [[ "$STATUS" == "403" ]]; then
    pass "GET /api/admin/stats (READER) → 403 (role guard OK)"
  else
    fail "GET /api/admin/stats (READER)" "expected 403, got $STATUS"
  fi

  # 26. Invalid / expired token — must 401
  STATUS=$(http_status GET "$BASE_URL/api/users/me" -H "Authorization: Bearer invalid.token.here")
  if [[ "$STATUS" == "401" ]]; then
    pass "GET /api/users/me (bad token) → 401"
  else
    fail "GET /api/users/me (bad token)" "expected 401, got $STATUS"
  fi
fi

# ---------------------------------------------------------------------------
# Tier 4 — Admin / SUPERADMIN endpoints
# ---------------------------------------------------------------------------
header "Tier 4: Admin endpoints (SUPERADMIN role)"

if [[ -z "${JWT_SECRET:-}" ]]; then
  skip "All Tier 4 tests" "JWT_SECRET not set"
  SKIP=$((SKIP + 3))
else
  ADMIN_TOKEN=$(mint_test_jwt "$JWT_SECRET" "SUPERADMIN" "smoke-admin-$$")

  # 27. Admin stats — auth accepted (200/500 both mean the auth layer passed)
  STATUS=$(http_status GET "$BASE_URL/api/admin/stats" -H "Authorization: Bearer $ADMIN_TOKEN")
  if [[ "$STATUS" == "200" || "$STATUS" == "404" || "$STATUS" == "500" ]]; then
    pass "GET /api/admin/stats (SUPERADMIN) → $STATUS (auth accepted)"
  else
    fail "GET /api/admin/stats (SUPERADMIN)" "expected non-401/403, got $STATUS"
  fi

  # 28. Admin users list — auth accepted
  STATUS=$(http_status GET "$BASE_URL/api/admin/users" -H "Authorization: Bearer $ADMIN_TOKEN")
  if [[ "$STATUS" == "200" || "$STATUS" == "404" || "$STATUS" == "500" ]]; then
    pass "GET /api/admin/users (SUPERADMIN) → $STATUS (auth accepted)"
  else
    fail "GET /api/admin/users (SUPERADMIN)" "expected non-401/403, got $STATUS"
  fi

  # 29. READER token on admin endpoint — must still 403
  READER_TOKEN=$(mint_test_jwt "$JWT_SECRET" "READER" "smoke-reader2-$$")
  STATUS=$(http_status GET "$BASE_URL/api/admin/stats" -H "Authorization: Bearer $READER_TOKEN")
  if [[ "$STATUS" == "403" ]]; then
    pass "GET /api/admin/stats (READER token on admin route) → 403"
  else
    fail "GET /api/admin/stats (READER on admin)" "expected 403, got $STATUS"
  fi
fi

# ---------------------------------------------------------------------------
# Tier 5 — DB connectivity (response shape assertions)
# ---------------------------------------------------------------------------
header "Tier 5: DB connectivity (response shape)"

# 30. Articles list returns items/pagination shape
BODY=$(http_body_full GET "$BASE_URL/api/articles")
if echo "$BODY" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert isinstance(d, list) or any(k in d for k in ('articles','items','data'))
" 2>/dev/null; then
  pass "GET /api/articles → valid JSON with expected shape"
else
  fail "GET /api/articles" "response body unexpected: ${BODY:0:200}"
fi

# 31. Tags list returns array
BODY=$(http_body_full GET "$BASE_URL/api/tags")
if echo "$BODY" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert isinstance(d, list) or 'tags' in d
" 2>/dev/null; then
  pass "GET /api/tags → valid JSON array/object"
else
  fail "GET /api/tags" "response body unexpected: ${BODY:0:200}"
fi

# 32. Search all returns articles/tags/authors keys
BODY=$(http_body_full GET "$BASE_URL/api/search?q=test&type=all")
if echo "$BODY" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert 'articles' in d and 'tags' in d and 'authors' in d
" 2>/dev/null; then
  pass "GET /api/search?type=all → JSON has articles, tags, authors keys"
else
  fail "GET /api/search?type=all" "response body unexpected: ${BODY:0:200}"
fi

# 33. Content types returns content_types key
BODY=$(http_body_full GET "$BASE_URL/api/articles/content-types")
if echo "$BODY" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert 'content_types' in d and isinstance(d['content_types'], list)
" 2>/dev/null; then
  pass "GET /api/articles/content-types → JSON has content_types list"
else
  fail "GET /api/articles/content-types" "response body unexpected: ${BODY:0:200}"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "═══════════════════════════════════════════════"
echo "  Smoke test complete: $SMOKE_ENV  ($BASE_URL)"
echo "  PASS: $PASS  FAIL: $FAIL  SKIP: $SKIP"
echo "═══════════════════════════════════════════════"

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
