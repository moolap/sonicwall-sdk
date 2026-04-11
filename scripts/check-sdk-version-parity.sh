#!/bin/sh
# Fail if root VERSION, Python, TypeScript, and Go SDK versions diverge.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

V="$(tr -d ' \n\r\t' < VERSION)"
PY="$(sed -n 's/^version = "\([^"]*\)"$/\1/p' packages/python/pyproject.toml)"
TS="$(sed -n 's/^  "version": "\([^"]*\)",$/\1/p' packages/typescript/package.json)"
GO="$(sed -n 's/^const Version = "\([^"]*\)"$/\1/p' packages/go/version.go)"

ok=1
[ -n "$V" ] || ok=0
[ -n "$PY" ] || ok=0
[ -n "$TS" ] || ok=0
[ -n "$GO" ] || ok=0
if [ "$ok" != 1 ]; then
  echo "check-sdk-version-parity: could not parse one or more version fields" >&2
  echo "  VERSION file: '${V:-<empty>}'" >&2
  echo "  pyproject.toml: '${PY:-<empty>}'" >&2
  echo "  package.json: '${TS:-<empty>}'" >&2
  echo "  version.go: '${GO:-<empty>}'" >&2
  exit 1
fi

if [ "$V" != "$PY" ] || [ "$V" != "$TS" ] || [ "$V" != "$GO" ]; then
  echo "check-sdk-version-parity: mismatch (all must equal root VERSION):" >&2
  echo "  VERSION=$V pyproject=$PY package.json=$TS version.go=$GO" >&2
  exit 1
fi

echo "SDK version parity OK: $V"
