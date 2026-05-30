#!/usr/bin/env sh
# Run live SonicWall validation from repo root (requires SONICWALL_* env vars).
set -eu

cd "$(dirname "$0")/../packages/python"

if ! uv run python -c "from sonicwall._live_validation import live_device_configured; import sys; sys.exit(0 if live_device_configured() else 1)" 2>/dev/null; then
  echo "Set SONICWALL_HOST and SONICWALL_PASS (or SW_HOST / SW_PASS) before running." >&2
  exit 1
fi

echo "== smoke_test.py =="
uv run ../../smoke_test.py

if [ "${SONICWALL_INTEGRATION_WRITE:-}" = "1" ] || [ "${SONICWALL_INTEGRATION_WRITE:-}" = "true" ]; then
  echo "== validate_write_crud.py =="
  uv run ../../validate_write_crud.py
else
  echo "Skipping write CRUD (set SONICWALL_INTEGRATION_WRITE=1 to enable)."
fi
