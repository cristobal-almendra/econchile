# AGENTS.md

## What this is

Small Python 3.10+ OSS library wrapping the Banco Central de Chile (BCCh) SIE REST API: fetch official macro series (UF, USD, TPM, IPC, IMACEC, PIB), parse into typed data, cache in SQLite. Published on PyPI as `econchile` (v0.1.0, MIT).

## Commands

```bash
pip install -e ".[test]"     # editable install + pytest
python -m pytest tests/ -q   # 188 tests, must stay green
python examples/demo.py      # offline demo, runs without BCCH_TOKEN
```

`BCCH_TOKEN` comes from the environment only — the library does not load `.env` itself. `.env` is gitignored and holds a real token locally; never let it into a commit or diff.

## Conventions

- `specs/*.md` are the source of truth: one spec per module. Read the spec before touching a module.
- `tests/` are the contract. All 188 tests must stay green.
- **NEVER create or commit anything under `econchile/study/`** — private, gitignored annotated learning notes. Do not add `*_annotated.py` versions of new files.
- **NEVER commit `.env`, `.env.local`, or any secret.**
- `sample_response.json` (8MB real API fixture, UTF-16) stays tracked as-is — `tests/test_parsers.py` needs it. It is excluded from the sdist via MANIFEST.in. Do not trim, remove, or "fix" it.
- PyPI releases: push tag `v*` → CI runs tests (Python 3.10/3.11/3.12) then publishes via trusted publisher. No manual publish.

## Architecture

Resolution chain: API → SQLite cache → raise. Two clients: `BcchClient` is cache-first (serve fresh cache, hit API on miss); `OfflineClient` is API-first (try API, fall back to cache on failure). Cache lives at `~/.econchile/cache.db`, default TTL 24h.

## Gotchas

- Public API takes dates as `YYYY-MM-DD`; BCCh sends `DD-MM-YYYY` internally — converters handle the conversion, don't mix formats.
- BCCh marks missing data with `statusCode == "ND"` → parsed as `value=None`, never zero or an exception.
- BCCh response encoding is unstable: UTF-16 with BOM or UTF-8. Parsers must try `utf-16` (strips BOM) then fall back to `utf-8`.
- BCCh API tokens may contain `/` — the fetcher URL-encodes them automatically via `urlencode` (`/` → `%2F`). Never build API URLs by hand-formatting the raw token into the query string; always pass it through `urllib.parse.urlencode`/`quote`.

## Contribution flow

1. Read the relevant `specs/*.md` (write/update it if the feature isn't specced).
2. Write the test contract in `tests/` (tests fail first).
3. Implement in `econchile/`.
4. `python -m pytest tests/ -q` — all green.
5. Commit. No secrets, no `study/`, no fixture changes.
