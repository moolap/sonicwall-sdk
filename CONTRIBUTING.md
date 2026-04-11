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

Branch off `main`. Rebase before opening an MR — do not merge main into your branch.

**Do not push commits directly to `main`.** All changes should land via merge request. Enforce that by **protecting `main`** in GitLab (CI cannot block `git push`):

1. **Settings → Repository → Protected branches** → protect **`main`**.
2. **Allowed to push:** **No one**.
3. **Allowed to merge:** roles that may merge MRs (e.g. Maintainers).

Optional: **Merge requests → Pipelines must succeed** on the MR, since `main` may not run a push pipeline after merge (see `.gitlab-ci.yml` `workflow`).

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

## Unified SDK version

All three language packages ship the **same semver**. The canonical value lives in the repository root **`VERSION`** file; CI enforces that it matches:

- `packages/python/pyproject.toml` (`version = …`)
- `packages/typescript/package.json` (`"version"`)
- `packages/go/version.go` (`const Version`)

**Process:** Treat the SDK as one product. For any user-visible bug fix, feature, or behavior change, update **Python, TypeScript, and Go** in the same merge request (or split MRs that land together before release). Do not release languages at different versions.

To bump after editing **`VERSION`**:

```bash
./scripts/sync-sdk-version.sh
```

Commit the updated files together. **Release tags** for npm and Go must use the same numbers, e.g. `typescript/v0.2.0` and `go/v0.2.0` when `VERSION` is `0.2.0`.

**First PyPI publish:** With the current tree, the version is **`0.1.0`** (see `VERSION`). The first successful `python:release` on `main` uploads that version unless you bump first.

## Release Process

**Python (PyPI):** A **push to `main`** that changes **`packages/python/pyproject.toml`** (usually a version bump) triggers `python:release` after lint/test/build/security pass on that pipeline. Tags and other branches do **not** publish Python to PyPI. Because CI requires parity with **`VERSION`**, bump **`VERSION`** and run **`./scripts/sync-sdk-version.sh`** (or update all four places by hand) so `pyproject.toml` changes in the same commit.

**TypeScript / Go:** Tag-driven:

- `typescript/v0.2.0` → publishes npm package
- `go/v0.2.0` → Go module tag

Only maintainers should merge to `main` and push version tags. Use [Changesets](https://github.com/changesets/changesets) for TypeScript versioning.

Merging to `main` runs a **full** GitLab pipeline again (not only the publish job).

### Trusted publishing (PyPI and npm)

CI is wired for **OIDC trusted publishing** (short-lived tokens, no long-lived publish secrets). Before your first release, register this repo in each registry:

1. **PyPI** — project → *Manage* → *Publishing* → *Add a new pending publisher* → **GitLab CI/CD**. Use CI file **`.gitlab-ci.yml`**, namespace/project, and environment **`pypi`** (must match `python:release` → `environment.name` in `.gitlab-ci.yml`).
2. **npm** — package → *Settings* → *Trusted publishing* → **GitLab CI/CD**. CI file **`.gitlab-ci.yml`**. Requires **GitLab.com shared runners**; npm does not support self-hosted runners for this yet.

After a successful publish, remove any legacy **`PYPI_API_TOKEN`** / **`NPM_TOKEN`** CI variables if you no longer need the fallback paths in `.gitlab-ci.yml`. For a **private** GitLab repo, npm may publish but **not** attach provenance (npm limitation).