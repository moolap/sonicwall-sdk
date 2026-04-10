# Release Readiness Checklist

Use this checklist before adopting a new SDK version in production.

## 1) Test and build baseline

- [ ] Install Python dev deps: `cd packages/python && uv sync --extra dev`
- [ ] Run unit tests: `uv run pytest -q`
- [ ] Run lint/type checks if enabled in CI (`ruff`, `mypy`)

## 2) Authentication verification

- [ ] Verify expected auth mode for your device firmware:
  - Python: Digest `auth-int` + bearer token
  - TypeScript/Go: Basic + `smngsess` cookie
- [ ] Confirm bad-credential behavior is explicit and actionable
- [ ] Confirm session-expiry recovery re-authenticates and retries once

## 3) Live-device smoke validation

- [ ] Run smoke test against a non-production SonicWall:
  `cd packages/python && uv run ../../smoke_test.py --host <host> --user <user> --password <pass>`
- [ ] Run one-shot raw contract capture to collect endpoint payload shapes:
  `cd packages/python && uv run ../../collect_contract.py --host <host> --user <user> --password <pass>`
- [ ] Validate read endpoints (address objects, access rules, interfaces, NAT, services, DHCP)
- [ ] Validate write transaction (create + delete test object) and automatic commit
- [ ] Validate rollback behavior by forcing an exception inside `pending()`

## 4) Operational safety

- [ ] Confirm TLS policy (`verify_ssl` / `WithTLSSkipVerify`) matches environment
- [ ] Verify device admin session limits and client lifecycle (`disconnect`)
- [ ] Confirm logging/observability captures auth failures and retry behavior

## 5) Rollout

- [ ] Publish changelog entry describing auth behavior and firmware notes
- [ ] Tag release version and package artifacts
- [ ] Run pilot rollout on one environment before broad deployment
