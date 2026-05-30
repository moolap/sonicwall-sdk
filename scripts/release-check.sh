#!/usr/bin/env sh
# Verify release metadata before tagging on main.
set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

V="$(tr -d '[:space:]' < VERSION)"
echo "Checking release version ${V}..."

python3 scripts/sync_versions_from_file.py >/dev/null

if ! git diff --quiet VERSION packages/python/pyproject.toml packages/typescript/package.json \
  packages/go/version.go packages/java/pom.xml \
  packages/java/src/main/java/tech/gandiva/sonicwall/Version.java 2>/dev/null; then
  echo "ERROR: VERSION and package files are out of sync. Commit sync output first." >&2
  git diff --stat VERSION packages/python/pyproject.toml packages/typescript/package.json \
    packages/go/version.go packages/java/pom.xml || true
  exit 1
fi

PY="$(sed -n 's/^version = "\([^"]*\)"$/\1/p' packages/python/pyproject.toml)"
TS="$(sed -n 's/^  "version": "\([^"]*\)",$/\1/p' packages/typescript/package.json)"
GO="$(sed -n 's/^const Version = "\([^"]*\)"$/\1/p' packages/go/version.go)"
JAVA="$(sed -n 's|^  <version>\([^<]*\)</version>$|'\''\1'\''|p' packages/java/pom.xml | head -1)"

for label val in "pyproject" "$PY" "package.json" "$TS" "version.go" "$GO" "pom.xml" "$JAVA"; do
  if [ "$val" != "$V" ]; then
    echo "ERROR: ${label}=${val} != VERSION=${V}" >&2
    exit 1
  fi
done

echo "OK — all package versions match VERSION=${V}"
echo ""
echo "Next steps (on main, after merge):"
echo "  git tag v${V}"
echo "  git push origin v${V}"
echo ""
echo "CI will publish PyPI/npm, push go/v${V}, deploy Java to GitLab Maven, and mirror to GitHub."
