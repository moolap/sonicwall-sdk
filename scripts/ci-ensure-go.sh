# Bootstrap Go into the project when the host has no toolchain (shell executors
# ignore the golang Docker image). Intended to be sourced from GitLab CI.
#
# Usage: . "${CI_PROJECT_DIR}/scripts/ci-ensure-go.sh"

set -e
ROOT="${CI_PROJECT_DIR:-.}"
# Match packages/go/go.mod; patch level is the bootstrap tarball from go.dev
GO_BOOTSTRAP_VERSION="${GO_BOOTSTRAP_VERSION:-1.25.9}"
INSTALL_DIR="${ROOT}/.go-toolchain"

if command -v go >/dev/null 2>&1; then
	return 0 2>/dev/null || exit 0
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
