#!/usr/bin/env sh
# Run live SonicWall validation from repo root (requires device credentials).
#
#   cp .env.example .env   # edit .env (gitignored)
#   ./scripts/validate_local_device.sh
#
# Or export SONICWALL_HOST / SONICWALL_USER / SONICWALL_PASS in the shell.
#
# Destructive write CRUD (service/NAT/access-rule tests):
#   SONICWALL_INTEGRATION_WRITE=1 ./scripts/validate_local_device.sh --write

set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT/packages/python"

WRITE="${SONICWALL_INTEGRATION_WRITE:-}"
RUN_WRITE=0
for arg in "$@"; do
  case "$arg" in
    --write) RUN_WRITE=1 ;;
  esac
done
if [ "$WRITE" = "1" ] || [ "$WRITE" = "true" ] || [ "$WRITE" = "yes" ]; then
  RUN_WRITE=1
fi

uv sync --all-extras --quiet

echo "==> Smoke test (read + address-object write)"
uv run python ../../smoke_test.py

if [ "$RUN_WRITE" = "1" ]; then
  echo "==> Write CRUD validation (destructive)"
  uv run python ../../validate_write_crud.py
else
  echo "==> Skipping write CRUD (set SONICWALL_INTEGRATION_WRITE=1 or pass --write)"
fi

echo "==> Integration pytest (optional)"
if uv run pytest tests/integration -m integration -q; then
  echo "Integration tests passed."
else
  echo "Integration tests failed or were skipped."
  exit 1
fi
