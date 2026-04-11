#!/usr/bin/env bash
# Run on default-branch push only (see .gitlab-ci.yml sdk:release).
# Publishes the current semver from the merge commit, then bumps patch for the next dev cycle,
# commits [skip ci], pushes to the default branch, and merges that commit into dev.
set -euo pipefail

ROOT="${CI_PROJECT_DIR:?}"
cd "$ROOT"

if [ -z "${GITLAB_PUSH_TOKEN:-}" ]; then
	echo "ci-sdk-release: set CI/CD variable GITLAB_PUSH_TOKEN (project access token, scope: api + write_repository)." >&2
	exit 1
fi

if echo "${CI_COMMIT_MESSAGE:-}" | grep -qiE '\[(skip ci|ci skip)\]'; then
	echo "ci-sdk-release: skipping (commit message contains skip ci marker)"
	exit 0
fi

if echo "${CI_COMMIT_MESSAGE:-}" | grep -qiE '\[skip release\]'; then
	echo "ci-sdk-release: skipping ([skip release] in commit message — no registry publish or version bump)"
	exit 0
fi

DEFAULT_BRANCH="${CI_DEFAULT_BRANCH:?}"
REMOTE_URL="https://gitlab-ci-token:${GITLAB_PUSH_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git"

export PATH="${ROOT}/.uv-install/bin:${ROOT}/.uv-install:${PATH}"

echo "ci-sdk-release: publishing current versions from merge commit"
( cd "${ROOT}/packages/python" && uv build )
if [ -n "${PYPI_API_TOKEN:-}" ]; then
	( cd "${ROOT}/packages/python" && uv publish --token "${PYPI_API_TOKEN}" )
else
	( cd "${ROOT}/packages/python" && uv publish )
fi

( cd "${ROOT}/packages/typescript" && pnpm install --frozen-lockfile && pnpm run build )
if [ -n "${NPM_TOKEN:-}" ]; then
	echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" >"${HOME}/.npmrc"
fi
( cd "${ROOT}/packages/typescript" && pnpm publish --no-git-checks --access public )

( cd "${ROOT}/packages/go" && go build ./... && go test ./... )

NEW_VER="$(python3 "${ROOT}/scripts/bump_sdk_version.py")"
echo "ci-sdk-release: bumped workspace to ${NEW_VER} for continued development"

git config user.email "${GIT_USER_EMAIL:-gitlab-ci@${CI_SERVER_HOST}}"
git config user.name "${GIT_USER_NAME:-GitLab CI}"

git add packages/python/pyproject.toml packages/typescript/package.json packages/go/version.go
git commit -m "chore: bump version to ${NEW_VER} for development [skip ci]"

if git remote get-url push-origin >/dev/null 2>&1; then
	git remote set-url push-origin "${REMOTE_URL}"
else
	git remote add push-origin "${REMOTE_URL}"
fi

git push push-origin "HEAD:refs/heads/${DEFAULT_BRANCH}"

git fetch push-origin "${DEFAULT_BRANCH}" dev

git checkout -B dev "push-origin/dev"
git merge --no-ff "push-origin/${DEFAULT_BRANCH}" -m "chore: sync dev with ${DEFAULT_BRANCH} after release ${NEW_VER} [skip ci]"
git push push-origin "HEAD:refs/heads/dev"

echo "ci-sdk-release: published release from merge commit; ${DEFAULT_BRANCH} and dev now at ${NEW_VER}"
