# Roadmap

Python is the **reference implementation**. TypeScript and Go follow after Python behavior is validated on real firmware.

## Now (Python correctness)

- [x] Live-device pytest harness (`tests/integration/`, env-gated)
- [x] Unified env vars (`SONICWALL_*` and `SW_*`)
- [x] `UnsupportedEndpointError` for firmware/API limitations
- [x] Run smoke + write CRUD on lab SonicWall; update `docs/current-status.md`
- [x] Live-validate access-rule / NAT / service-object writes (or document read-only)
- [ ] Expand Python unit tests for access rules, NAT, service objects

## Next (Python hardening)

- [ ] Config-mode negotiation improvements and clearer errors
- [ ] Contract capture → endpoint support matrix automation
- [ ] Pre-release script: lint + unit tests + optional live smoke

## Later (multi-language parity)

- [x] Port SonicOS 7.x Digest + bearer auth to TypeScript
- [x] Port SonicOS 7.x Digest + bearer auth to Go
- [x] Port SonicOS 7.x Digest + bearer auth to Java
- [x] Port Python payload fallbacks to TypeScript and Go
- [x] Port Python payload fallbacks to Java (access rules, NAT, service objects writes)
- [x] `UnsupportedEndpointError` / firmware limitation detection in TS, Go, Java
- [ ] Go unit test suite (auth + firmware errors; expand CRUD coverage)
- [x] Java SDK scaffold (`packages/java`) with address-object CRUD + list APIs
- [x] Java unit + WireMock integration tests (auth, errors, wire format, all list services)

## OSS / release

- [x] Public repo mirror to GitHub (`mirror:github` CI job — set `GITHUB_MIRROR_TOKEN`)
- [x] Tag aligned release (`VERSION` + PyPI/npm + `go/v*` tag)
- [x] Go module path aligned with GitHub mirror (`github.com/moolap/sonicwall-sdk/go`)
- [x] Java GitLab Maven release job (`java:release`)
- [ ] Maven Central publishing for Java
- [ ] Package metadata URL alignment complete (PyPI/npm/Java registry docs)
- [ ] Git history secret scan before broad announcement
