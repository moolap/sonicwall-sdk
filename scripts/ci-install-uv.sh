# Install Astral uv into the project without touching PEP 668–managed system Python.
# Intended to be sourced from GitLab CI so PATH persists for later before_script lines.
# Usage: . "${CI_PROJECT_DIR}/scripts/ci-install-uv.sh"

set -e
ROOT="${CI_PROJECT_DIR:-.}"
export UV_INSTALL_DIR="${ROOT}/.uv-install"
mkdir -p "${UV_INSTALL_DIR}"
export PATH="${UV_INSTALL_DIR}/bin:${PATH}"

if command -v uv >/dev/null 2>&1; then
	:
elif command -v curl >/dev/null 2>&1; then
	curl -LsSf https://astral.sh/uv/install.sh | sh
else
	pip install uv --quiet
fi
