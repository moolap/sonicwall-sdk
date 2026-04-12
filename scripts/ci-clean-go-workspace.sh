#!/usr/bin/env sh
# Remove repo-local .go/ (leaked GOMODCACHE / golang.org toolchain tree). Go marks module
# cache files read-only; without chmod, git clean and rm fail with Permission denied.
set -f
ROOT="${CI_PROJECT_DIR:-.}"
[ -n "$ROOT" ] || exit 0
d="${ROOT}/.go"
[ -d "$d" ] || exit 0
chmod -R u+rwx "$d" 2>/dev/null || true
rm -rf "$d" 2>/dev/null || true
