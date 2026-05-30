# GitLab → GitHub mirror

Development and releases stay on **GitLab** (`dev` → MR → `main`, tags, CI).

The public open-source copy is mirrored to:

**https://github.com/moolap/sonicwall-sdk**

Only **`main`** and **release tags** are pushed. The `dev` branch is not mirrored.

Consumer-facing versioning and install instructions: **[releases.md](releases.md)**.

## One-time setup

### 1. Create the GitHub repository

Create `moolap/sonicwall-sdk` on GitHub (empty repo is fine; no README required).

### 2. Create a GitHub token (do not commit or paste in chat)

**Fine-grained PAT** (recommended):

1. GitHub → **Settings** → **Developer settings** → **Fine-grained tokens** → **Generate**
2. Repository access: **Only** `moolap/sonicwall-sdk`
3. Permissions → **Contents:** Read and write
4. Generate and copy the token once

**Classic PAT** alternative: scope `public_repo` (public repo) or `repo` (private).

### 3. Add the token to GitLab CI/CD

GitLab project → **Settings** → **CI/CD** → **Variables**:

| Key | Value | Flags |
|-----|--------|--------|
| `GITHUB_MIRROR_TOKEN` | your GitHub PAT | Masked, Protected |

Optional override:

| Key | Value |
|-----|--------|
| `GITHUB_REPO` | `moolap/sonicwall-sdk` (default in `.gitlab-ci.yml`) |

### 4. Trigger the mirror

After the variable is set:

1. Merge to **`main`** on GitLab, or  
2. Push a release tag (`v0.1.0` / `0.1.0`) on the mainline  

Pipeline job **`mirror:github`** runs in the **release** stage. If the token is missing, the job **skips** (exit 0) with a log message.

## Verify

Open https://github.com/moolap/sonicwall-sdk and confirm:

- `main` matches GitLab `main` at the same commit SHA  
- Release tags appear after you tag on GitLab  
- No `.env` or secrets in the tree  

## Manual push (fallback)

```bash
git remote add github https://github.com/moolap/sonicwall-sdk.git
git checkout main
git pull origin main
git push github main
git push github --tags
```

Use a credential helper or PAT locally; do not store the PAT in the repository.

## Package URLs

The Go module path is **`github.com/moolap/sonicwall-sdk/go`**, aligned with the public GitHub mirror. `go get` and pkg.go.dev use the **`go/vX.Y.Z`** tag pushed by CI on each release.
