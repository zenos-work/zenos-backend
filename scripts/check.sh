#!/usr/bin/env bash
# =============================================================================
# Zenos Backend — Coverage & Build Check
# Usage:
#   ./scripts/check.sh                     # run lint + coverage + build check
#   ./scripts/check.sh --no-lint           # skip ruff lint step
#   ./scripts/check.sh --no-build          # skip build/dry-run step
#   MIN_COVERAGE=90 ./scripts/check.sh     # override minimum coverage threshold
#
# Prerequisites: uv, node/npx (for wrangler build check)
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
MIN_COVERAGE="${MIN_COVERAGE:-72}"
RUN_LINT=true
RUN_BUILD=true

for arg in "$@"; do
  case "$arg" in
    --no-lint)  RUN_LINT=false ;;
    --no-build) RUN_BUILD=false ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: $0 [--no-lint] [--no-build]"
      exit 1
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

section() { echo -e "\n${CYAN}${BOLD}══ $1 ══${RESET}"; }
ok()      { echo -e "${GREEN}  ✔  $1${RESET}"; }
warn()    { echo -e "${YELLOW}  ⚠  $1${RESET}"; }
fail()    { echo -e "${RED}  ✖  $1${RESET}"; }

FAILURES=0
mark_fail() { fail "$1"; FAILURES=$((FAILURES + 1)); }

# ---------------------------------------------------------------------------
# 1. Lint (ruff)
# ---------------------------------------------------------------------------
if $RUN_LINT; then
  section "Lint — ruff"
  if uv run ruff check src tests; then
    ok "ruff: no issues found"
  else
    mark_fail "ruff reported lint errors (see above)"
  fi
fi

# ---------------------------------------------------------------------------
# 2. Coverage — pytest-cov
# ---------------------------------------------------------------------------
section "Tests & Coverage"

COVERAGE_REPORT_DIR="htmlcov"

set +e
uv run pytest \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml \
  --cov-report=json:coverage.json \
  --cov-report="html:${COVERAGE_REPORT_DIR}" \
  --cov-fail-under="${MIN_COVERAGE}"
PYTEST_EXIT=$?
set -e

COVERAGE_PCT="unknown"
if [[ -f coverage.json ]]; then
  COVERAGE_PCT=$(uv run python - <<'PY'
import json
with open('coverage.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data.get('totals', {}).get('percent_covered', 'unknown'))
PY
)
fi

if [[ $PYTEST_EXIT -eq 0 ]]; then
  ok "All tests passed — source coverage ${COVERAGE_PCT}% (threshold: ${MIN_COVERAGE}%)"
else
  if [[ "$COVERAGE_PCT" != "unknown" ]] && awk "BEGIN {exit !(${COVERAGE_PCT} < ${MIN_COVERAGE})}"; then
    mark_fail "Coverage below ${MIN_COVERAGE}% threshold (current: ${COVERAGE_PCT}%)"
  else
    mark_fail "Tests failed (exit code ${PYTEST_EXIT})"
  fi
fi

echo ""
echo "  Coverage reports written to:"
echo "    • coverage.xml  (Cobertura — CI)"
echo "    • coverage.json (machine-readable)"
echo "    • ${COVERAGE_REPORT_DIR}/  (HTML — open index.html)"

# ---------------------------------------------------------------------------
# 3. Build / dry-run (wrangler)
# ---------------------------------------------------------------------------
if $RUN_BUILD; then
  section "Build — wrangler dry-run"

  # pywrangler deploy --dry-run validates the Worker bundle without uploading
  if uv run pywrangler deploy --dry-run 2>&1; then
    ok "Build check passed (wrangler dry-run)"
  else
    mark_fail "wrangler dry-run failed (see above)"
  fi
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
section "Summary"

if [[ $FAILURES -eq 0 ]]; then
  echo -e "${GREEN}${BOLD}  All checks passed.${RESET}"
  exit 0
else
  echo -e "${RED}${BOLD}  ${FAILURES} check(s) failed — review output above.${RESET}"
  exit 1
fi
