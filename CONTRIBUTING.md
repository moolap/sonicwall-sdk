# Contributing to SonicWall SDK

Thank you for your interest in contributing! This document covers the contribution workflow for all three SDK languages.

## Developer Certificate of Origin (DCO)

All commits must be signed off with the DCO. Add `-s` to your commit command:

```bash
git commit -s -m "feat(python): add service object resource"
```

This adds a `Signed-off-by: Your Name <email@example.com>` line confirming you have the right to submit the code under the project's Apache-2.0 license. See https://developercertificate.org/.

Pull requests with commits lacking sign-off will not be merged.

## Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/<short-desc>` | `feat/python-dhcp-resource` |
| Bug fix | `fix/<short-desc>` | `fix/ts-session-race` |
| Docs | `docs/<short-desc>` | `docs/go-quickstart` |
| Chore | `chore/<short-desc>` | `chore/update-deps` |

Branch off **`dev`** for everyday work (or open MRs into `dev`). Rebase before opening an MR — do not merge unrelated history into your branch.

**Do not push commits directly to `main`.** All changes should land via merge request. Enforce that by **protecting `main`** in GitLab (CI cannot block `git push`):

1. **Settings → Repository → Protected branches** → protect **`main`**.
2. **Allowed to push:** **No one**.
3. **Allowed to merge:** roles that may merge MRs (e.g. Maintainers).

CI does **not** run on merge requests—only on **pushes** to branches (e.g. `dev`, feature branches) and on **`main`** after merge. Rely on a green **`dev`** pipeline before you merge to `main`. If GitLab has **Pipelines must succeed** enabled for MRs, turn it off or CI will block merges unnecessarily.

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body]

Signed-off-by: Your Name <email@example.com>
```

**Types:** `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `perf`

**Scopes:** `python`, `typescript`, `go`, `spec`, `ci`, `docs`

Examples:
```
feat(python): add NAT policy resource with full CRUD
fix(go): prevent double-unlock in authManager.reauthenticate
docs(typescript): add transaction pattern example
```

Breaking changes: add `!` after scope and a `BREAKING CHANGE:` footer.

## Development Setup

### Prerequisites

- Python 3.10+, `uv` (https://docs.astral.sh/uv/)
- Node.js 20+, `pnpm` 10
- Go 1.25.9+
- `golangci-lint` (https://golangci-lint.run/usage/install/)

### Python

```bash
cd packages/python
uv sync --all-extras
# Run linting
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
# Run tests
uv run pytest tests/ -v --cov=sonicwall --cov-report=term-missing
```

### TypeScript

```bash
cd packages/typescript
pnpm install
# Run linting
pnpm run lint
# Type check
pnpm run typecheck
# Run tests
pnpm run test
# Build
pnpm run build
```

### Go

```bash
cd packages/go
go mod tidy
# Lint
golangci-lint run ./...
# Test (with race detector)
go test -race ./...
# Test with coverage
go test -race -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## Adding a New Resource

1. Add the OpenAPI path to `spec/openapi.yaml`
2. Implement the Python resource in `packages/python/src/sonicwall/resources/`
3. Implement the TypeScript resource in `packages/typescript/src/resources/`
4. Implement the Go service in `packages/go/`
5. Add tests for all three
6. Update `docs/sonicwall-quirks.md` if the endpoint has unusual behavior

## Code Style

- **Python**: `ruff` for linting and formatting, `mypy` strict mode
- **TypeScript**: `eslint` with strict config, no `any` types without justification
- **Go**: `gofmt` + `golangci-lint` with default ruleset

## Testing Against a Real SonicWall

The test suite uses mocked HTTP servers by default. To run integration tests against a real device:

```bash
# Python
SONICWALL_HOST=192.168.1.1 SONICWALL_USER=admin SONICWALL_PASS=secret \
  uv run pytest tests/ -m integration -v

# TypeScript
SONICWALL_HOST=192.168.1.1 SONICWALL_USER=admin SONICWALL_PASS=secret \
  pnpm run test:integration

# Go
SONICWALL_HOST=192.168.1.1 SONICWALL_USER=admin SONICWALL_PASS=secret \
  go test -tags=integration -race ./...
```

Integration tests are skipped if `SONICWALL_HOST` is not set.

## MR Checklist

- [ ] DCO sign-off on all commits
- [ ] Tests added/updated for new behavior
- [ ] All three SDK languages updated (if adding a resource)
- [ ] `spec/openapi.yaml` updated
- [ ] `CHANGELOG.md` entry under `## Unreleased`
- [ ] CI pipeline green

## Branch and release flow

**`dev`** and **`main`** run the same **lint → test → build → security** jobs on every push. Only **`main`** also runs **`sdk:release`** (after those stages succeed).

Typical loop:

1. Commit on **`dev`** and push → pipeline on `dev` must be green.
2. Open a merge request **`dev` → `main`** and merge when ready (there is **no** MR pipeline; you already verified **`dev`** above). Merging starts a **`main`** push pipeline.
3. **`sdk:release`** on that `main` push:
   - Publishes the **current** versions in `packages/python/pyproject.toml`, `packages/typescript/package.json`, and `packages/go/version.go` to **PyPI** and **npm** (and runs **Go build/test** as a sanity check).
   - **Bumps the patch** version in all three places (e.g. `0.1.0` → `0.1.1`) for the next development cycle.
   - Commits with **`[skip ci]`**, pushes to **`main`**, then **merges `main` into `dev`** and pushes **`dev`** so both branches show the new “next” version.

Keep the three package versions equal before you merge to `main`. Treat the SDK as one product: behavior changes should land in Python, TypeScript, and Go together when possible.

**Merges that must not publish** (e.g. docs-only while the package version is unchanged): put **`[skip release]`** in the merge commit subject/body so `sdk:release` exits without calling PyPI/npm or bumping versions. Otherwise every merge to `main` is treated as a release of the current semver.

**Go module installs** (`go get`) still follow the usual **`go/vX.Y.Z` git tags** on this repo; the release job does not create those tags automatically. Tag **`go/v0.1.0`** (etc.) when you need proxy-friendly Go releases, or extend CI later.

### GitLab: `GITLAB_PUSH_TOKEN`

The release job must **push commits** to **`main`** and **`dev`**. Add a masked CI/CD variable **`GITLAB_PUSH_TOKEN`**: a [project access token](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html) (or PAT) with **api** and **write_repository**, allowed to push to protected branches (often as **Maintainer**). Without it, `sdk:release` fails at the git push step.

### Trusted publishing (PyPI and npm)

Register **GitLab CI/CD** as a trusted publisher for **PyPI** and **npm** (CI file **`.gitlab-ci.yml`**). The job uses GitLab **`environment: pypi`** for PyPI OIDC; keep your PyPI trusted publisher environment name aligned with that.

Optional fallbacks: **`PYPI_API_TOKEN`**, **`NPM_TOKEN`**. npm trusted publishing needs **GitLab.com shared runners** (not self-hosted) per npm’s docs.