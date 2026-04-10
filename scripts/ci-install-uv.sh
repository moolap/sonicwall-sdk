# Install Astral uv into the project without touching PEP 668–managed system Python.
# Intended to be sourced from GitLab CI so PATH persists for later before_script lines.
# Usage: . "${CI_PROJECT_DIR}/scripts/ci-install-uv.sh"
#
# The upstream install.sh layout varies: binaries may live in .uv-install/ or
# .uv-install/bin/, and newer releases add .uv-install/env for PATH.

set -e
ROOT="${CI_PROJECT_DIR:-.}"
export UV_INSTALL_DIR="${ROOT}/.uv-install"
mkdir -p "${UV_INSTALL_DIR}"

uv_on_path() {
	command -v uv >/dev/null 2>&1
}

apply_uv_path() {
	if [ -f "${UV_INSTALL_DIR}/env" ]; then
		# shellcheck disable=SC1090
		. "${UV_INSTALL_DIR}/env"
	fi
	export PATH="${UV_INSTALL_DIR}/bin:${UV_INSTALL_DIR}:${PATH}"
}

apply_uv_path

if uv_on_path; then
	:
elif command -v curl >/dev/null 2>&1; then
	curl -LsSf https://astral.sh/uv/install.sh | sh
	apply_uv_path
else
	pip install uv --quiet
	export PATH="${HOME}/.local/bin:${PATH}"
fi

if ! uv_on_path; then
	echo "ci-install-uv: uv not on PATH after install (UV_INSTALL_DIR=${UV_INSTALL_DIR})" >&2
	ls -la "${UV_INSTALL_DIR}" 2>/dev/null || true
	return 1 2>/dev/null || exit 1
fi
