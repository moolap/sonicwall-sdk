# GitLab CI runners (private pool only)

This project is configured to use **Gandiva private runners**, not GitLab.com shared runners.

## GitLab project settings (already required)

In **Settings → CI/CD → Runners**:

| Setting | Required value |
|---------|----------------|
| **Enable shared runners for this project** | **Off** |
| Project/group runners with tags `gdlinux` + `gdlinux-gpu` | **Online** |

Current project state: `shared_runners_enabled` is **false** on `gandiva-tech/sonicwall-sdk`.

## How CI enforces the pool

In `.gitlab-ci.yml`:

- `default.tags` is `gdlinux` + `gdlinux-gpu` (GitLab **AND**s tags — the runner must have **both**).
- Job `validate:runner-pool` runs first in **lint** and fails if:
  - The runner description looks like a shared runner, or
  - The `gdlinux` tag is missing from `CI_RUNNER_TAGS`.

## Change runner pool

Edit `default.tags` in `.gitlab-ci.yml` (one tag per line). Examples documented in comments:

- `gdlab-linux`
- `gdlab-spark`
- `gdlab-mac`
- `macos`

Do not list unrelated tags together (e.g. `gdlinux` + `macos`) unless one runner actually has both.

## npm / PyPI release on private runners

Trusted publishing for **npm OIDC** does not work on self-hosted runners; set **`NPM_TOKEN`** in CI/CD variables for `typescript:release`. PyPI OIDC can work with GitLab trusted publishing when configured.
