#!/bin/sh
# Same logic as GitLab job security:osv-scan (.gitlab-ci.yml).
# Local host:  ./scripts/ci-osv-scan.sh
# CI-like Docker: ./scripts/ci-osv-scan.sh --docker
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
CI_PROJECT_DIR=${CI_PROJECT_DIR:-$ROOT}
OSV_SCANNER_VERSION=${OSV_SCANNER_VERSION:-v2.3.5}
OSV_BIN=${OSV_BIN:-${CI_PROJECT_DIR}/.osv-scanner-bin}

if [ "${1:-}" = "--docker" ]; then
  SHA=$(git -C "${ROOT}" rev-parse HEAD)
  exec docker run --rm \
    -v "${ROOT}:${ROOT}" \
    -w "${ROOT}" \
    -e CI_PROJECT_DIR="${ROOT}" \
    -e CI_RUNNER_EXECUTOR=docker \
    -e CI_COMMIT_SHA="${SHA}" \
    -e OSV_SCANNER_VERSION="${OSV_SCANNER_VERSION}" \
    -e OSV_BIN=/tmp/osv-scanner-bin \
    alpine:3.20 \
    sh -c 'apk add --no-cache git curl ca-certificates && sh "'"${ROOT}"'/scripts/ci-osv-scan.sh"'
fi

if [ -z "${CI_COMMIT_SHA:-}" ]; then
  CI_COMMIT_SHA=$(git -C "${CI_PROJECT_DIR}" rev-parse HEAD 2>/dev/null || echo "")
fi

cd "${CI_PROJECT_DIR}"

install_missing_tools() {
  NEED=""
  command -v git >/dev/null 2>&1 || NEED="${NEED} git"
  command -v curl >/dev/null 2>&1 || NEED="${NEED} curl"
  if [ -z "${NEED}" ]; then
    return 0
  fi

  if command -v apk >/dev/null 2>&1; then
    apk add --no-cache git curl ca-certificates
  elif command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y --no-install-recommends git curl ca-certificates
  fi
}

install_missing_tools
command -v git >/dev/null 2>&1 || { echo "ERROR: git required" >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "ERROR: curl required" >&2; exit 1; }

if [ "${CI_RUNNER_EXECUTOR:-}" = "shell" ]; then
  HEAD_SHA=$(git rev-parse HEAD 2>/dev/null || echo "")
  echo "HEAD=${HEAD_SHA} expected=${CI_COMMIT_SHA}"
  NEED_CHECKOUT=0
  if [ "${HEAD_SHA}" != "${CI_COMMIT_SHA}" ]; then NEED_CHECKOUT=1; fi
  if [ -n "${CI_COMMIT_SHA}" ] && ! git cat-file -e "${CI_COMMIT_SHA}^{commit}" 2>/dev/null; then
    NEED_CHECKOUT=1
  fi
  if [ "${NEED_CHECKOUT}" -eq 1 ]; then
    if [ -z "${CI_JOB_TOKEN:-}" ] || [ -z "${CI_SERVER_HOST:-}" ] || [ -z "${CI_PROJECT_PATH:-}" ]; then
      echo "ERROR: shell checkout needs CI_JOB_TOKEN, CI_SERVER_HOST, CI_PROJECT_PATH" >&2
      exit 1
    fi
    AUTH_ORIGIN="https://gitlab-ci-token:${CI_JOB_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git"
    git remote set-url origin "${AUTH_ORIGIN}"
    git fetch --unshallow origin 2>/dev/null || git fetch origin "${CI_COMMIT_REF_NAME:-dev}"
    git checkout -f "${CI_COMMIT_SHA}"
  fi
  git clean -ffdx
fi

ARCH=$(uname -m)
OS=$(uname -s)
case "${OS}" in
  Linux)
    case "${ARCH}" in
      x86_64) DL_SUFFIX=linux_amd64 ;;
      aarch64|arm64) DL_SUFFIX=linux_arm64 ;;
      *) echo "osv-scanner: unsupported arch ${ARCH}" >&2; exit 1 ;;
    esac
    ;;
  Darwin)
    case "${ARCH}" in
      x86_64) DL_SUFFIX=darwin_amd64 ;;
      arm64|aarch64) DL_SUFFIX=darwin_arm64 ;;
      *) echo "osv-scanner: unsupported arch ${ARCH}" >&2; exit 1 ;;
    esac
    ;;
  *) echo "osv-scanner: unsupported OS ${OS}" >&2; exit 1 ;;
esac

mkdir -p "${OSV_BIN}"
URL="https://github.com/google/osv-scanner/releases/download/${OSV_SCANNER_VERSION}/osv-scanner_${DL_SUFFIX}"
if [ ! -x "${OSV_BIN}/osv-scanner" ]; then
  echo "Downloading osv-scanner ${OSV_SCANNER_VERSION} (${DL_SUFFIX})..."
  curl -fsSL -o "${OSV_BIN}/osv-scanner" "${URL}"
  chmod +x "${OSV_BIN}/osv-scanner"
fi
PATH="${OSV_BIN}:${PATH}"
export PATH

echo "Scanning lockfiles at ${CI_COMMIT_SHA:-HEAD}"
osv-scanner scan \
  --lockfile=packages/python/uv.lock \
  --lockfile=pnpm-lock.yaml \
  --lockfile=packages/go/go.mod

echo "OK — osv-scanner found no issues (same pass criteria as CI)."
