# Mini — CI/CD Workflows

| Workflow | Trigger | Purpose |
|---|---|---|
| `python-tests.yml` | push/PR on `lunch-optimizer/**`, `NLP/**` | pytest + syntax check across Python 3.10/3.11 |
| `web-ci.yml` | push/PR on `dashboard-web/**` | `tsc --noEmit`, `eslint`, `next build --standalone` |
| `docker-build.yml` | push/PR on any buildable path + tags `v*.*.*` | Buildx image build + GHCR push |

## python-tests.yml

Runs in parallel across Python 3.10 and 3.11:

1. **nlp-research** — smoke tests (`pytest nlp_research/tests/`) + benchmark dry-run (`benchmark --smoke`). Only stdlib-ish deps (`pyyaml`, `python-dotenv`, `pytest`). torch/transformers tests are auto-skipped via `conftest.py` markers. Artifact: `benchmark-summary-py{version}.zip`.
2. **nlp-mvp-syntax** — AST parse all `.py` files under `NLP/nlp_mvp/`.
3. **lunch-optimizer-syntax** — AST parse all `.py` files under `lunch-optimizer/`.

Typical runtime: ~2 minutes per python version.

## web-ci.yml

1. Install with `npm ci` (cached)
2. `npx tsc --noEmit` — strict type check
3. `npm run lint -- --max-warnings 0`
4. `npm run build` with NEXT_PUBLIC_* baked to localhost
5. Verify `.next/standalone/server.js` exists

Typical runtime: ~3 minutes (cached).

## docker-build.yml

Builds 3 images in parallel via matrix:
- `ghcr.io/<owner>/mini-lunch-optimizer`
- `ghcr.io/<owner>/mini-nlp-api`
- `ghcr.io/<owner>/mini-dashboard-web`

**Tag strategy** (via `docker/metadata-action`):
- `latest` on `main`
- `sha-<7char>` on every build
- Semver tags (`v1.2.3` → `1.2.3`, `1.2`, `1`) on git tag push
- PR builds are **dry-run only** (no push) to catch Dockerfile regressions

Uses **GitHub Actions cache** (`type=gha`) for Docker layer reuse — torch wheel cache survives across PRs so nlp-api build drops from ~12 min to ~2 min on cache hit.

**Permissions required:**
- `packages: write` (granted by default to `GITHUB_TOKEN`)
- GHCR repository must exist; first successful push creates it

**compose-validate** job runs `docker compose config --quiet` to catch YAML errors.

## Dependabot

Grouped weekly updates for:
- 3 Python sub-projects (`lunch-optimizer`, `nlp_mvp`, `nlp_research`)
- 1 npm package (`dashboard-web`)
- GitHub Actions versions
- Docker base images

Minor/patch versions are batched into a single PR per project to avoid PR spam.

## Local equivalent commands

```bash
# Python tests
cd NLP && PYTHONPATH=. pytest nlp_research/tests/ -v

# Benchmark dry-run
cd NLP && PYTHONPATH=. python -m nlp_research.evaluation.benchmark --module all --smoke

# Web build
cd dashboard-web && npm ci && npx tsc --noEmit && npm run lint && npm run build

# Docker build (all 3)
docker compose build

# Compose validate
docker compose config --quiet
```
