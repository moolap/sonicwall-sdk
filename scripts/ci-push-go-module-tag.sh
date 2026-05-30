#!/usr/bin/env sh
# Create and push the Go module tag (go/vX.Y.Z) for the current release commit.
# Requires CI_COMMIT_TAG, CI_COMMIT_SHA, CI_SERVER_HOST, CI_PROJECT_PATH.
set -eu

if [ -z "${CI_COMMIT_TAG:-}" ]; then
  echo "ERROR: CI_COMMIT_TAG is required" >&2
  exit 1
fi

TAG_VER="${CI_COMMIT_TAG#v}"
GO_TAG="go/v${TAG_VER}"

if ! echo "${TAG_VER}" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+'; then
  echo "ERROR: unsupported tag format: ${CI_COMMIT_TAG}" >&2
  exit 1
fi

if command -v apk >/dev/null 2>&1; then
  apk add --no-cache git >/dev/null 2>&1 || true
fi

git config user.email "ci@sonicwall-sdk.local"
git config user.name "sonicwall-sdk CI"

if git rev-parse "${GO_TAG}" >/dev/null 2>&1; then
  existing="$(git rev-parse "${GO_TAG}")"
  if [ "${existing}" != "${CI_COMMIT_SHA}" ]; then
    echo "ERROR: ${GO_TAG} exists at ${existing}, expected ${CI_COMMIT_SHA}" >&2
    exit 1
  fi
  echo "Tag ${GO_TAG} already points at ${CI_COMMIT_SHA}"
else
  git tag "${GO_TAG}" "${CI_COMMIT_SHA}"
  echo "Created tag ${GO_TAG} at ${CI_COMMIT_SHA}"
fi

if [ -n "${GITLAB_PUSH_TOKEN:-}" ]; then
  AUTH_ORIGIN="https://oauth2:${GITLAB_PUSH_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git"
elif [ -n "${CI_JOB_TOKEN:-}" ] && [ -n "${CI_SERVER_HOST:-}" ] && [ -n "${CI_PROJECT_PATH:-}" ]; then
  AUTH_ORIGIN="https://gitlab-ci-token:${CI_JOB_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git"
else
  echo "ERROR: set GITLAB_PUSH_TOKEN (write_repository) or run in GitLab CI with CI_JOB_TOKEN" >&2
  exit 1
fi

git push "${AUTH_ORIGIN}" "refs/tags/${GO_TAG}"
echo "Pushed ${GO_TAG} to origin"
