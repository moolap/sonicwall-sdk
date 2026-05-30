# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-05-19

### Added
- Java SDK with full CRUD parity, WireMock tests, and Digest+bearer auth.
- Digest `auth-int` + bearer auth (with cookie fallback) in TypeScript, Go, and Java.
- `UnsupportedEndpointError` / firmware limitation detection in TypeScript, Go, and Java.
- Release automation: `go/vX.Y.Z` tag push, Java GitLab Maven deploy, GitHub mirror of tags.
- Consumer release guide (`docs/releases.md`).

### Changed
- Go module path: `github.com/moolap/sonicwall-sdk/go` (public GitHub mirror).
- Live validation results documented in `docs/current-status.md`.

## [0.1.0] - 2026-05-01

### Added
- Initial public multi-language SonicWall SDK release.
- Python package with async-first client, sync wrapper, typed models, and typed exceptions.
- TypeScript package with typed client, resources, transaction helper, and tests.
- Go module with idiomatic client/services, transaction helper, and tests.
- Core resources: address objects, access rules, NAT policies, service objects, interfaces, and DHCP.
- CI pipeline with lint, test, build, security scanning, and tag-based release gates.
- Documentation for Python, TypeScript, Go, firmware quirks, endpoint support matrix, and release readiness.

