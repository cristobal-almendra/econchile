# v0.1.3 — Launch hardening — Spec

## What this is

The pre-launch checklist (PHASE 1 + 2 + small docs), agreed by Hermes +
OpenCode consensus. Fixes the one real BLOCKER (PyPI publish from PR
triggers — confirmed: 0.1.2 was published by the PR check run at
22:56:28Z, before the `v0.1.2` tag even existed) plus cheap hardening.

## Changes

### 1. `.github/workflows/workflow.yml` — publish tag guard (BLOCKER)

Add a job-level guard to the `publish` job so it NEVER runs on
`pull_request` or `push` to main — only on `v*` tag pushes:

```yaml
  publish:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: test
```

Tests still run on PRs and main; only publishing is tag-gated. On a PR,
the `publish` job shows as **skipped** (not failed).

### 2. `econchile/parsers.py` — malformed response hardening

After decoding + `json.loads`, validate structure before touching fields.
All malformed shapes raise `ParsingError(-999, ...)`:

- top level not a dict (`null`, `[]`, `"42"`) → ParsingError
- `Series` missing or not a dict (`{"Codigo":0,"Series":null}` / `[]`) → ParsingError
- `seriesId` missing/empty → ParsingError
- `Obs` present but not a list → ParsingError

Deliberate documented behavior: a VALID response with an empty `Obs`
list returns `observations=[]` (no error) — an empty series is not
malformed. `Codigo != 0` still raises `ParsingError(codigo, descripcion)`
first (existing behavior, unchanged).

Result: no `AttributeError` / `KeyError` / `TypeError` ever leaks from
`parse_response` on weird-but-parseable JSON.

### 3. `econchile/fetcher.py` — HTTP 429 retry

`fetch_raw` retry loop: treat 429 as retryable alongside 5xx:

```python
retryable = http_status == 429 or http_status >= 500
if retryable and not is_last:
    continue
```

Same max_retries/backoff as today; persistent 429 → clean `BcchApiError`
after attempts are exhausted. (Retry-After header honoring: explicitly
OUT of scope — exponential backoff is fine for this traffic level.)

### 4. `README.md` — docs accuracy (2 small edits)

- Quickstart/Authentication: add the Windows PowerShell variant
  `$env:BCCH_TOKEN="your-token-here"` next to the `export` line.
- Replace the "survives API outages" comment with precise wording:
  "falls back to previously cached results when the API is unavailable".

### 5. `tests/test_release.py` (new) — release-level contract

- `test_publish_job_guarded_to_tags` — reads `workflow.yml`, asserts the
  `publish` job block contains `startsWith(github.ref, 'refs/tags/v')`.
  Regression guard: a future PR removing the guard fails CI.
- `test_version_matches_pyproject` — regex-parses `version = "..."` from
  `pyproject.toml` and compares to `econchile.__version__`. (No tomllib:
  CI runs Python 3.10.)
- `test_quickstart_documents_powershell_token` — README contains
  `$env:BCCH_TOKEN` (keeps the multi-platform auth docs honest).

### 6. Existing test files — added contract tests

- `tests/test_parsers.py` — parametrized malformed-response tests
  (`"null"`, `"[]"`, `"{}"`, `Series: null`, `Series: []`, missing
  `seriesId`, `Obs` not a list) → `ParsingError`; plus a guard: valid
  response with empty `Obs` → empty observations, no error.
- `tests/test_fetcher.py` — `429 then success` retries (2 calls);
  persistent 429 → `BcchApiError` after `max_retries + 1` attempts.

## Files touched (implementation)

1. `.github/workflows/workflow.yml`
2. `econchile/parsers.py`
3. `econchile/fetcher.py`
4. `README.md`

Test files (contract, Hermes-owned): `tests/test_release.py` (new),
`tests/test_parsers.py`, `tests/test_fetcher.py`.

## Acceptance

1. `publish` job has the tag guard; PRs never publish.
2. Malformed responses raise `ParsingError` (wrapped as `BcchApiError` by
   the fetcher) — no raw exceptions.
3. 429 is retried; persistent 429 raises clean `BcchApiError`.
4. README has `$env:BCCH_TOKEN` and precise offline wording.
5. `python -m pytest tests/ -q` → all green (206 + ~12 new).
6. No version bump in this branch (v0.1.3 bump happens at release time,
   same as v0.1.2). No new dependencies.
