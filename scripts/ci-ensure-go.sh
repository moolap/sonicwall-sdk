# Bootstrap Go into the project when the host has no toolchain (shell executors
# ignore the golang Docker image). Intended to be sourced from GitLab CI.
#
# Usage: . "${CI_PROJECT_DIR}/scripts/ci-ensure-go.sh"

set -e
ROOT="${CI_PROJECT_DIR:-.}"
if [ -f "${ROOT}/scripts/ci-clean-go-workspace.sh" ]; then
	sh "${ROOT}/scripts/ci-clean-go-workspace.sh"
elif [ -d "${ROOT}/.go" ]; then
	chmod -R u+rwx "${ROOT}/.go" 2>/dev/null || true
	rm -rf "${ROOT}/.go" 2>/dev/null || true
fi
# Match packages/go/go.mod; patch level is the bootstrap tarball from go.dev
GO_BOOTSTRAP_VERSION="${GO_BOOTSTRAP_VERSION:-1.25.10}"
INSTALL_DIR="${ROOT}/.go-toolchain"

_go_version_ok() {
	if ! command -v go >/dev/null 2>&1; then
		return 1
	fi
	INSTALLED=$(go env GOVERSION 2>/dev/null | sed 's/^go//')
	# Accept exact match or newer patch on the same minor line (go.mod pins 1.25.x).
	case "${INSTALLED}" in
		"${GO_BOOTSTRAP_VERSION}"|1.25.1[0-9]|1.25.[2-9][0-9]*) return 0 ;;
		*) return 1 ;;
	esac
}

if _go_version_ok; then
	return 0 2>/dev/null || exit 0
fi

if command -v go >/dev/null 2>&1; then
	echo "ci-ensure-go: system Go $(go env GOVERSION) < ${GO_BOOTSTRAP_VERSION}, bootstrapping..." >&2
fi

mkdir -p "${INSTALL_DIR}"
OS=$(uname -s)
ARCH=$(uname -m)
case "${OS}" in
Linux*) OS_KIND=linux ;;
Darwin*) OS_KIND=darwin ;;
*)
	echo "ci-ensure-go: unsupported OS: ${OS}" >&2
	return 1 2>/dev/null || exit 1
	;;
esac
case "${ARCH}" in
arm64 | aarch64) GOARCH=arm64 ;;
x86_64 | amd64) GOARCH=amd64 ;;
*)
	echo "ci-ensure-go: unsupported ARCH: ${ARCH}" >&2
	return 1 2>/dev/null || exit 1
	;;
esac

TARBALL="go${GO_BOOTSTRAP_VERSION}.${OS_KIND}-${GOARCH}.tar.gz"
URL="https://go.dev/dl/${TARBALL}"

if [ ! -x "${INSTALL_DIR}/go/bin/go" ]; then
	if command -v curl >/dev/null 2>&1; then
		curl -sSL "${URL}" | tar -xzf - -C "${INSTALL_DIR}"
	elif command -v wget >/dev/null 2>&1; then
		wget -qO- "${URL}" | tar -xzf - -C "${INSTALL_DIR}"
	else
		echo "ci-ensure-go: need curl or wget to download Go" >&2
		return 1 2>/dev/null || exit 1
	fi
fi

export PATH="${INSTALL_DIR}/go/bin:${PATH}"
if ! _go_version_ok; then
	echo "ci-ensure-go: cached Go $(${INSTALL_DIR}/go/bin/go env GOVERSION 2>/dev/null || echo unknown) < ${GO_BOOTSTRAP_VERSION}, reinstalling..." >&2
	rm -rf "${INSTALL_DIR}/go"
	if command -v curl >/dev/null 2>&1; then
		curl -sSL "${URL}" | tar -xzf - -C "${INSTALL_DIR}"
	elif command -v wget >/dev/null 2>&1; then
		wget -qO- "${URL}" | tar -xzf - -C "${INSTALL_DIR}"
	else
		echo "ci-ensure-go: need curl or wget to download Go" >&2
		return 1 2>/dev/null || exit 1
	fi
fi
