# Bootstrap Eclipse Temurin JDK into the project when the host has no Java 17+
# (shell executors ignore the Maven Docker image). Sourced from ci-ensure-maven.sh
# and GitLab CI Java jobs.
#
# Usage: . "${CI_PROJECT_DIR}/scripts/ci-ensure-java.sh"

set -e
ROOT="${CI_PROJECT_DIR:-.}"
JAVA_FEATURE="${JAVA_FEATURE:-21}"
INSTALL_DIR="${ROOT}/.java-toolchain"
STAMP="${INSTALL_DIR}/.installed-feature"

_java_ok() {
	if ! command -v java >/dev/null 2>&1; then
		return 1
	fi
	VER=$(
		java -version 2>&1 | head -1 | sed -E 's/.* version "([0-9]+).*/\1/'
	)
	[ -n "${VER}" ] && [ "${VER}" -ge 17 ]
}

if _java_ok; then
	return 0 2>/dev/null || exit 0
fi

if [ -f "${STAMP}" ] && [ "$(cat "${STAMP}")" = "${JAVA_FEATURE}" ]; then
	for candidate in "${INSTALL_DIR}"/jdk-* "${INSTALL_DIR}"/jdk; do
		if [ -x "${candidate}/bin/java" ]; then
			export JAVA_HOME="${candidate}"
			export PATH="${JAVA_HOME}/bin:${PATH}"
			if _java_ok; then
				return 0 2>/dev/null || exit 0
			fi
		fi
	done
fi

OS=$(uname -s)
ARCH=$(uname -m)
case "${OS}" in
Linux*) OS_KIND=linux ;;
Darwin*) OS_KIND=mac ;;
*)
	echo "ci-ensure-java: unsupported OS: ${OS}" >&2
	return 1 2>/dev/null || exit 1
	;;
esac
case "${ARCH}" in
arm64 | aarch64) JAVA_ARCH=aarch64 ;;
x86_64 | amd64) JAVA_ARCH=x64 ;;
*)
	echo "ci-ensure-java: unsupported ARCH: ${ARCH}" >&2
	return 1 2>/dev/null || exit 1
	;;
esac

URL="https://api.adoptium.net/v3/binary/latest/${JAVA_FEATURE}/ga/${OS_KIND}/${JAVA_ARCH}/jdk/hotspot/normal/eclipse?project=jdk"

mkdir -p "${INSTALL_DIR}"
echo "ci-ensure-java: installing Temurin JDK ${JAVA_FEATURE} into ${INSTALL_DIR}" >&2
rm -rf "${INSTALL_DIR}"/jdk-* "${INSTALL_DIR}/jdk" 2>/dev/null || true

if command -v curl >/dev/null 2>&1; then
	curl -sSL "${URL}" | tar -xzf - -C "${INSTALL_DIR}"
elif command -v wget >/dev/null 2>&1; then
	wget -qO- "${URL}" | tar -xzf - -C "${INSTALL_DIR}"
else
	echo "ci-ensure-java: need curl or wget to download JDK" >&2
	return 1 2>/dev/null || exit 1
fi

JAVA_HOME=""
for candidate in "${INSTALL_DIR}"/jdk-* "${INSTALL_DIR}/jdk"; do
	if [ -x "${candidate}/bin/java" ]; then
		JAVA_HOME="${candidate}"
		break
	fi
done

if [ -z "${JAVA_HOME}" ]; then
	echo "ci-ensure-java: JDK unpack did not produce bin/java under ${INSTALL_DIR}" >&2
	ls -la "${INSTALL_DIR}" >&2 || true
	return 1 2>/dev/null || exit 1
fi

echo "${JAVA_FEATURE}" > "${STAMP}"
export JAVA_HOME
export PATH="${JAVA_HOME}/bin:${PATH}"

if ! _java_ok; then
	echo "ci-ensure-java: installed JDK is not usable (need Java 17+)" >&2
	java -version >&2 || true
	return 1 2>/dev/null || exit 1
fi
