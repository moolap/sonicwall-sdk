# Roadmap

Python is the **reference implementation**. TypeScript and Go follow after Python behavior is validated on real firmware.

## Now (Python correctness)

- [x] Live-device pytest harness (`tests/integration/`, env-gated)
- [x] Unified env vars (`SONICWALL_*` and `SW_*`)
- [x] `UnsupportedEndpointError` for firmware/API limitations
- [ ] Run smoke + write CRUD on lab SonicWall; update `docs/current-status.md`
- [ ] Live-validate access-rule / NAT / service-object writes (or document read-only)
- [ ] Expand Python unit tests for access rules, NAT, service objects

## Next (Python hardening)

- [ ] Config-mode negotiation improvements and clearer errors
- [ ] Contract capture → endpoint support matrix automation
- [ ] Pre-release script: lint + unit tests + optional live smoke

## Later (multi-language parity)

- [ ] Port SonicOS 7.x Digest + bearer auth to TypeScript
- [ ] Port SonicOS 7.x Digest + bearer auth to Go
- [ ] Port Python payload fallbacks to TypeScript and Go
- [ ] Go unit test suite (currently none)
- [ ] TypeScript tests beyond address objects

## OSS / release

- [ ] Tag aligned release (`VERSION` + PyPI/npm + `go/v*` tag)
- [ ] Public repo mirror and package metadata URL alignment
- [ ] Git history secret scan before broad announcement
