# Spec — PyPI Trusted Publisher workflow (.github/workflows/workflow.yml)

## Context

Cristobal registered a PyPI Trusted Publisher on pypi.org:
- PyPI project: `econchile`
- GitHub owner: `cristobal-almendra`
- GitHub repo: `econchile`
- Workflow filename: `workflow.yml` (MUST be this exact filename — the
  publisher registration matches on it)

Trusted Publishing = OIDC-based. GitHub Actions gets a short-lived PyPI
token automatically. NO API token, NO secrets, nothing stored. This is the
modern recommended publish path.

## Requirements

Create ONE file: `.github/workflows/workflow.yml`

### Trigger
- On tag push matching `v*` (e.g. `v0.1.0`) — the standard release flow.
- Also `workflow_dispatch:` so Cristobal can trigger manually for testing.

### Jobs

1. **test** job (gate): `ubuntu-latest`, matrix `3.10 / 3.11 / 3.12`:
   - checkout, setup-python with `cache: pip`
   - `pip install -e ".[test]"`
   - `python -m pytest tests/ -q`
   - Note: tests are fully offline — no `BCCH_TOKEN`, no network, no secrets.

2. **publish** job: `needs: test` (never publish broken tests), `ubuntu-latest`:
   - `permissions: contents: read, id-token: write` ← **id-token: write is
     REQUIRED** for OIDC trusted publishing; without it the upload fails
     with a permissions error.
   - checkout, setup-python `3.11`
   - `pip install build`
   - `python -m build` (produces dist/*.whl + dist/*.tar.gz)
   - Publish via the official action:
     `uses: pypa/gh-action-pypi-publish@release/v1` with `packages-dir: dist`
   - NO explicit `password`/`token` inputs — the action handles OIDC
     automatically when `id-token: write` is set.

### Constraints
- Filename MUST be `workflow.yml` (registered name).
- Do NOT create a separate CI workflow — the test job lives inside this file.
- No secrets, no environment variables referencing tokens.
- Standard actions only: `actions/checkout@v4`, `actions/setup-python@v5`,
  `pypa/gh-action-pypi-publish@release/v1`.
- Follow the official PyPI trusted-publishing examples
  (https://docs.pypi.org/trusted-publishers/) — verify syntax carefully;
  YAML indentation errors break the whole workflow.

## Verification (by delegating agent)

1. YAML parses: `python -c "import yaml; yaml.safe_load(open('.github/workflows/workflow.yml'))"`
   (if PyYAML unavailable, do a strict manual review).
2. `id-token: write` present under publish job permissions.
3. `needs: test` present on publish job.
4. Trigger is `v*` tags (+ workflow_dispatch).
5. No token/password strings anywhere in the file.
6. Report the full file content in the summary.

## Out of scope
- No CI-only workflow file (tests are inside this workflow).
- No commit/push (Cristobal commits).
- No README badge changes.
