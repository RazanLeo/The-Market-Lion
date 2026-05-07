#!/usr/bin/env bash
# Run full security scan: bandit (Python) + semgrep (multi-lang) + npm audit (frontend)
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
echo "==[1/3] bandit (Python static analysis)=="
( cd "$ROOT/backend" && pip install bandit semgrep --quiet >/dev/null 2>&1 || true ; bandit -r app -ll -ii ) || true

echo "==[2/3] semgrep (multi-lang)=="
( cd "$ROOT" && semgrep --config p/owasp-top-ten --config p/security-audit --severity ERROR --severity WARNING --error || true )

echo "==[3/3] npm audit (Frontend dependencies)=="
( cd "$ROOT/frontend" && npm audit --audit-level=high || true )

echo "Done. Review output above."
