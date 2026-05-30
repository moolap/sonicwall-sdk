# Versioning and releases

All four SDKs (Python, TypeScript, Go, Java) ship as **one product** with a single
[Semantic Versioning](https://semver.org/) number (e.g. `0.1.0`).

## Source of truth

| File | Role |
|------|------|
| [`VERSION`](../VERSION) | Canonical semver for the whole repo |
| `packages/python/pyproject.toml` | PyPI package `sonicwall-sdk` |
| `packages/typescript/package.json` | npm package `@sonicwall/sdk` |
| `packages/go/version.go` | Go module version constant |
| `packages/java/pom.xml` | Maven artifact `tech.gandiva:sonicwall-sdk` |

Before tagging, maintainers run:

```bash
python3 scripts/sync_versions_from_file.py
```

CI job **`validate:release-versions`** fails if the git tag, `VERSION`, and any package file disagree.

## Release policy (mainline only)

Releases are cut **only from `main`**, never from `dev`:

1. Integrate on **`dev`**, merge to **`main`** via merge request (merge commit).
2. On **`main`**, bump **`VERSION`**, sync package files, commit.
3. Tag the commit on **`main`**: `0.2.0` or `v0.2.0` (both accepted).
4. Push the tag — CI runs tests, **`validate:tag-from-main`**, publishes artifacts, and mirrors to GitHub.

**`dev` is not published** and is **not mirrored** to the public GitHub repo.

## Public GitHub mirror

After each push to **`main`** or a release tag, CI mirrors to:

**https://github.com/moolap/sonicwall-sdk**

You can browse source, clone, or download tarballs/zipballs from **`main`** or any release tag on GitHub. For production, **pin a release tag** (`v0.1.0`), not a moving branch tip.

See [mirroring.md](mirroring.md) for maintainer setup.

## Installing a specific version

Replace `0.1.0` / `v0.1.0` with the version you want. List tags on GitHub: **Releases** or `git tag -l`.

### Python (PyPI — preferred)

```bash
pip install sonicwall-sdk==0.1.0
uv add sonicwall-sdk==0.1.0
```

`pyproject.toml`: `sonicwall-sdk = "==0.1.0"` or a range like `>=0.1.0,<0.2.0`.

### Python (from GitHub tag)

```bash
pip install "git+https://github.com/moolap/sonicwall-sdk.git@v0.1.0#subdirectory=packages/python"
```

Or clone and install locally:

```bash
git clone --branch v0.1.0 --depth 1 https://github.com/moolap/sonicwall-sdk.git
pip install ./sonicwall-sdk/packages/python
```

### TypeScript / Node (npm — preferred)

```bash
pnpm add @sonicwall/sdk@0.1.0
npm install @sonicwall/sdk@0.1.0
```

`package.json`: `"@sonicwall/sdk": "0.1.0"` (exact) or `"^0.1.0"` (compatible within major).

### TypeScript (from GitHub tag)

Clone, build, and link or pack:

```bash
git clone --branch v0.1.0 --depth 1 https://github.com/moolap/sonicwall-sdk.git
cd sonicwall-sdk
pnpm install --frozen-lockfile
pnpm --filter @sonicwall/sdk run build
pnpm add file:./packages/typescript   # from your app repo
```

### Go (module proxy — preferred)

The Go module path is `github.com/gandiva-tech/sonicwall-sdk/go`. Releases use a **second tag** on the same commit:

| Tag | Purpose |
|-----|---------|
| `v0.1.0` (or `0.1.0`) | Same as other languages; used by CI |
| `go/v0.1.0` | Required for `go get` / pkg.go.dev |

```bash
go get github.com/gandiva-tech/sonicwall-sdk/go@v0.1.0
```

`go.mod`:

```go
require github.com/gandiva-tech/sonicwall-sdk/go v0.1.0
```

After tagging on GitLab `main`, push the Go module tag (CI prints the command):

```bash
git tag go/v0.1.0 <commit-sha> && git push origin go/v0.1.0
```

### Go (from GitHub checkout)

```bash
git clone --branch v0.1.0 --depth 1 https://github.com/moolap/sonicwall-sdk.git
```

In your app's `go.mod`:

```go
replace github.com/gandiva-tech/sonicwall-sdk/go => ../sonicwall-sdk/packages/go
```

### Java (Maven — from source today)

Java is not yet published to Maven Central. Pin the semver in your POM and build from a **mainline tag** on GitHub:

```bash
git clone --branch v0.1.0 --depth 1 https://github.com/moolap/sonicwall-sdk.git
cd sonicwall-sdk/packages/java && mvn install
```

```xml
<dependency>
  <groupId>tech.gandiva</groupId>
  <artifactId>sonicwall-sdk</artifactId>
  <version>0.1.0</version>
</dependency>
```

## Checking the version at runtime

| SDK | API |
|-----|-----|
| Python | `importlib.metadata.version("sonicwall-sdk")` |
| TypeScript | Lockfile / `package.json` dependency version |
| Go | `sonicwall.Version` |
| Java | `tech.gandiva.sonicwall.Version.VERSION` |

## Changelog

User-visible changes are listed in [CHANGELOG.md](../CHANGELOG.md) per release.
