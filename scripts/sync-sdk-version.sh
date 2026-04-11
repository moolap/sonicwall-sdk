#!/usr/bin/env bash
# Apply the semver in repository root VERSION to Python, TypeScript, and Go package metadata.
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
V="$(tr -d ' \n\r\t' < "$ROOT/VERSION")"
if ! [[ "$V" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$ ]]; then
  echo "sync-sdk-version: invalid semver in VERSION: $V" >&2
  exit 1
fi

perl -pi -e "s/^version = \"\\K[^\"]+/$V/" "$ROOT/packages/python/pyproject.toml"
perl -pi -e "s/^  \"version\": \"\\K[^\"]+/$V/" "$ROOT/packages/typescript/package.json"
perl -pi -e "s/^const Version = \"\\K[^\"]+/$V/" "$ROOT/packages/go/version.go"

echo "Synced SDK version to $V (pyproject.toml, package.json, version.go)."
