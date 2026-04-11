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

## Release Process

Releases are triggered by git tags pushed to `main`:

- `python/v0.2.0` → publishes Python package to PyPI
- `typescript/v0.2.0` → publishes npm package
- `go/v0.2.0` → creates Go module tag

Only maintainers can push version tags. Use [Changesets](https://github.com/changesets/changesets) for TypeScript versioning.