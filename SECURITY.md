# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.x (latest) | Yes |

Older minor versions receive security patches for 90 days after a new minor is released.

## Reporting a Vulnerability

**Do not open a public GitLab issue for security vulnerabilities.**

### Private Reporting (Preferred)

Use GitLab's built-in confidential security advisory system:

1. Navigate to the repository on GitLab
2. Go to **Security → Security advisories → New advisory**
3. Fill in the vulnerability details and submit

You will receive a response within the SLA windows below.

### Email (Fallback)

If you cannot access GitLab's advisory form, email **security@gandiva.tech** with:

- A description of the vulnerability
- Steps to reproduce
- Affected versions / languages
- Your assessment of severity (CVSS score if possible)
- Any suggested mitigations

Encrypt sensitive reports with our PGP key (fingerprint published at https://gandiva.tech/.well-known/security.txt).

## Response SLA

| Severity (CVSS) | Initial Response | Patch Target |
|-----------------|-----------------|--------------|
| Critical (9.0–10.0) | 24 hours | 48 hours |
| High (7.0–8.9) | 48 hours | 7 days |
| Medium (4.0–6.9) | 5 business days | 30 days |
| Low (0.1–3.9) | 10 business days | 90 days |

## CVE Process

For confirmed vulnerabilities we will:

1. Request a CVE from MITRE (or accept a reporter-supplied CVE)
2. Prepare a fix on a private branch
3. Coordinate disclosure timing with the reporter
4. Release the fix and publish a GitLab Security Advisory
5. Credit the reporter in the advisory (unless they prefer anonymity)

## Scope

This policy covers the `sonicwall-sdk` Python, TypeScript, and Go packages.

Out of scope (report directly to SonicWall):

- Vulnerabilities in SonicOS firmware or the SonicOS REST API itself
- Vulnerabilities in SonicWall hardware or management interfaces

## Security Best Practices for SDK Users

- Store SonicWall credentials in a secrets manager (Vault, AWS Secrets Manager, etc.) — never in source code or environment files committed to version control
- Enable SSL verification in production: pass `verify_ssl=True` when your SonicWall has a valid certificate
- Rotate the SonicOS management password regularly; the SDK re-authenticates automatically
- Restrict the management account used by the SDK to the minimum required privileges
- Audit pending-config usage: uncommitted changes are visible to all admin sessions until committed or rolled back