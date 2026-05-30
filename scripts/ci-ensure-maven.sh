# Bootstrap Apache Maven into the project when the host has no mvn (shell executors
# ignore the Maven Docker image). Intended to be sourced from GitLab CI.
#
# Usage: . "${CI_PROJECT_DIR}/scripts/ci-ensure-maven.sh"

set -e
ROOT="${CI_PROJECT_DIR:-.}"
MAVEN_VERSION="${MAVEN_VERSION:-3.9.9}"
INSTALL_DIR="${ROOT}/.maven-tool"
MAVEN_HOME="${INSTALL_DIR}/apache-maven-${MAVEN_VERSION}"

_mvn_ok() {
	command -v mvn >/dev/null 2>&1
}

if _mvn_ok; then
	return 0 2>/dev/null || exit 0
fi

if ! command -v java >/dev/null 2>&1; then
	echo "ci-ensure-maven: java not found on PATH (required for Maven)" >&2
	return 1 2>/dev/null || exit 1
fi

mkdir -p "${INSTALL_DIR}"
OS=$(uname -s)
ARCH=$(uname -m)
case "${OS}" in
Linux*) OS_KIND=linux ;;
Darwin*) OS_KIND=osx ;;
*)
	echo "ci-ensure-maven: unsupported OS: ${OS}" >&2
	return 1 2>/dev/null || exit 1
	;;
esac
case "${ARCH}" in
arm64 | aarch64) MAVEN_ARCH=aarch64 ;;
x86_64 | amd64) MAVEN_ARCH=amd64 ;;
*)
	echo "ci-ensure-maven: unsupported ARCH: ${ARCH}" >&2
	return 1 2>/dev/null || exit 1
	;;
esac

TARBALL="apache-maven-${MAVEN_VERSION}-bin.tar.gz"
URL="https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/${TARBALL}"

if [ ! -x "${MAVEN_HOME}/bin/mvn" ]; then
	echo "ci-ensure-maven: installing Maven ${MAVEN_VERSION} into ${INSTALL_DIR}" >&2
	if command -v curl >/dev/null 2>&1; then
		curl -sSL "${URL}" | tar -xzf - -C "${INSTALL_DIR}"
	elif command -v wget >/dev/null 2>&1; then
		wget -qO- "${URL}" | tar -xzf - -C "${INSTALL_DIR}"
	else
		echo "ci-ensure-maven: need curl or wget to download Maven" >&2
		return 1 2>/dev/null || exit 1
	fi
fi

export MAVEN_HOME
export PATH="${MAVEN_HOME}/bin:${PATH}"

if ! _mvn_ok; then
	echo "ci-ensure-maven: mvn still not on PATH after install" >&2
	return 1 2>/dev/null || exit 1
fi
