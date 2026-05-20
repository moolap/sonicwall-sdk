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

**Do not push commits directly to `main`.** Land changes via **merge request** (`dev` → `main`). This matches the **Srasta** workflow: integration on **`main`**, **releases only when you push a version tag**.

CI includes **`validate:no-direct-push-to-main`** on **`main`** only (even if GitLab’s default branch is **`dev`**): the tip commit must be a **merge commit** (more than one parent). **GitLab “Squash merge”** yields one parent and **fails** that check—use a **merge commit** for `dev` → `main` (or turn off squash for that MR). Tags **`X.Y.Z`** or **`vX.Y.Z`** are checked by **`validate:tag-from-main`** (commit must be reachable from `main`).

Enforce human access with **protected branches** on **`main`**:

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
# Python (read-only smoke + address-object write in pending transaction)
cd packages/python
SONICWALL_HOST=192.168.1.1 SONICWALL_USER=admin SONICWALL_PASS=secret \
  uv run pytest tests/integration -m integration -v

# Python destructive write CRUD (service objects, NAT, access rules) — opt-in
SONICWALL_HOST=192.168.1.1 SONICWALL_USER=admin SONICWALL_PASS=secret \
  SONICWALL_INTEGRATION_WRITE=1 \
  uv run pytest tests/integration -m integration_write -v

# CLI equivalents (verbose output)
SONICWALL_HOST=192.168.1.1 SONICWALL_USER=admin SONICWALL_PASS=secret \
  uv run ../../smoke_test.py
SONICWALL_INTEGRATION_WRITE=1 uv run ../../validate_write_crud.py
```

Legacy env aliases `SW_HOST`, `SW_USER`, and `SW_PASS` are also supported.

Unit test runs exclude `integration` and `integration_write` by default (`pyproject.toml` `addopts`).
TypeScript/Go live-device tests are not implemented yet.

## MR Checklist

- [ ] DCO sign-off on all commits
- [ ] Tests added/updated for new behavior
- [ ] All three SDK languages updated (if adding a resource)
- [ ] `spec/openapi.yaml` updated
- [ ] `CHANGELOG.md` entry under `## Unreleased`
- [ ] CI pipeline green

## Community Standards

By participating, you agree to follow the project
[Code of Conduct](CODE_OF_CONDUCT.md).

## Branch and release flow (Srasta-style)

**Branches:** **`dev`** and **`main`** run the same **lint → test → build → security** jobs on every push. **Merging to `main` does not publish** to PyPI or npm.

**Releases:** When `main` has the commit you want to ship, you **tag** it **`X.Y.Z`** or **`vX.Y.Z`** (Srasta often uses **`v`**; both work here). That starts a **tag pipeline** that:

1. Runs the same checks again, plus **`validate:release-versions`** (root **`VERSION`** must match the tag, and Python / TypeScript / Go metadata must match **`VERSION`**).
2. Runs **`validate:tag-from-main`** (the tagged commit must be on the **`main`** line).
3. Runs **`python:release`**, **`typescript:release`**, and **`go:release`** (build/test + PyPI + npm; Go still needs a separate **`go/vX.Y.Z`** tag on the same commit for `go get` — the job prints the exact command).

**Typical loop**

1. Push to **`dev`** → green pipeline.
2. Merge **`dev` → `main`** via MR (**merge commit**, not squash if you rely on `validate:no-direct-push-to-main`).
3. On **`main`**, set **`VERSION`** to the release (e.g. `0.2.0`), run **`python3 scripts/sync_versions_from_file.py`**, commit, push to **`main`** (via MR from a short-lived branch is fine).
4. Tag and push: **`git tag 0.2.0`** (or **`git tag v0.2.0`**) && **`git push origin 0.2.0`** (or **`v0.2.0`**) — tag must point at the commit that contains the synced files.

Treat the SDK as one product: keep **`VERSION`**, **`pyproject.toml`**, **`package.json`**, and **`version.go`** aligned (use the sync script). No CI job pushes git commits for releases.

### CI runners (private vs GitLab shared)

Pipelines are pinned with **`default.tags`** in **`.gitlab-ci.yml`**. **GitLab matches every tag in the list on the same runner (AND).** You cannot list `gdlinux` and `macos` together unless one runner is tagged with both.

**Current default:** **`gdlinux`** and **`gdlinux-gpu`** (the assigned project runner in GitLab shows both).

**Other runner tags** used elsewhere in Gandiva (assign / link the runner to this project, bring it **online**, then point CI at it):

| Tag | Typical use |
|-----|-------------|
| **`gdlab-linux`** | Lab Linux runners (`gd-vm-infra`) |
| **`gdlab-spark`** | Spark lab runners |
| **`gdlab-mac`** | Mac lab runners |
| **`macos`** | e.g. `srasta-devkit` |

To use one of those pools **instead**, replace **`default.tags`** with a **single** tag (or a set that exists together on one runner), e.g. only `- gdlab-linux`. The comments under **`default.tags`** in **`.gitlab-ci.yml`** list the same options.

To let **several different runners** run the same pipeline without editing YAML, give them a **shared** tag (e.g. `sonicwall-sdk-ci`) in **`config.toml`** / GitLab runner settings and set **`default.tags`** to that tag only.

To avoid **GitLab.com shared runners** for this project: **Settings → CI/CD → Runners** → disable **Enable shared runners for this project**. Jobs then run only on runners that match **`default.tags`** and are available to the project.

Jobs use **`image: ...`** (Docker images). Your runners should use the **Docker** or **Kubernetes** executor unless you intentionally run on **shell** runners with those tools preinstalled on the host.

**Go / `.go` “Permission denied” warnings:** If the module cache or `golang.org/toolchain` ends up under **`${CI_PROJECT_DIR}/.go`**, Go stores many files as read-only. Git’s clean step then logs **`warning: failed to remove … Permission denied`**. The pipeline runs **`scripts/ci-clean-go-workspace.sh`** (chmod `u+rwx`, then `rm -rf`) in **`hooks:pre_get_sources_script`** (before Git cleans), in **`.integrity`**, and at the start of **`ci-ensure-go.sh`**. If warnings persist, files may be **root-owned** (e.g. bind-mounted build dirs); fix runner user/ownership or add a **`pre_clone_script`** on the runner host.

### Trusted publishing (PyPI and npm)

Register **GitLab CI/CD** as a trusted publisher for **PyPI** and **npm** (CI file **`.gitlab-ci.yml`**). The job uses GitLab **`environment: pypi`** for PyPI OIDC; keep your PyPI trusted publisher environment name aligned with that.

Optional fallbacks: **`PYPI_API_TOKEN`**, **`NPM_TOKEN`**. **npm OIDC** trusted publishing is limited to **GitLab.com shared runners** today; on **self-hosted runners**, set **`NPM_TOKEN`** (granular publish token) for **`typescript:release`**.