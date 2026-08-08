# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-08-07

### Fixed

- **`OfflineClient` works without a token** — the token is now optional at
  construction; it is validated at fetch time. A missing token raises
  `BcchApiError` (before any network I/O) and the existing cache fallback
  treats it like any other API failure, so cache-only usage works without
  `BCCH_TOKEN` set. `BcchClient` cache hits also work token-less.
  Previously `OfflineClient()` could not even be constructed without a
  token, defeating its documented "survives API outages" purpose.

### Changed

- `Fetcher.__init__` no longer raises `ValueError` when no token is
  configured — construction never requires credentials. Docstrings and
  README/AGENTS.md updated accordingly.

### Added

- 5 new contract tests (206 total): token-less construction, cache
  served without a token, `BcchOfflineError` when no token AND no cache.

## [0.1.1] - 2026-08-07

### Fixed

- **Latin-1 responses now decode** — the BCCh API sometimes serves
  ISO-8859-1 with raw accented bytes (e.g. USD, TPM, IPC series). Decode
  order is now UTF-16 BOM → UTF-8 → latin-1 (latin-1 never fails), in both
  the fetcher and the parsers. Previously these series raised a raw
  `UnicodeDecodeError`.
- **Decode failures wrap as `BcchApiError`** — a truncated UTF-16 body now
  surfaces as `BcchApiError`, matching the documented error contract,
  instead of a raw `UnicodeDecodeError`.
- **Transient failures are retried** — the fetcher retries network errors,
  HTTP ≥ 500, and non-JSON/HTML bodies up to `max_retries` (default 2) with
  exponential backoff (`retry_backoff * 2**attempt`). HTTP 4xx and
  `Codigo != 0` business errors are never retried.
- **`OfflineClient` no longer masks bugs** — the cache fallback now triggers
  only on API/network failures (`BcchApiError`, `requests.RequestException`,
  `OSError`). Programming errors propagate instead of being silently hidden
  behind stale-cache serving.
- **Tests skip gracefully without the 8MB fixture** — `test_parsers.py`
  skips when `sample_response.json` is absent (e.g. when running tests from
  an sdist install) instead of crashing.

### Added

- `Fetcher(max_retries=..., retry_backoff=...)` — configurable retry policy.
- `[project.urls]` in `pyproject.toml` — Homepage/Repository links on PyPI.
- CI now also runs on **pull requests** to `main` (previously only tag
  pushes and manual dispatch).
- 13 new tests (201 total, all offline).

### Changed

- Removed the stale `result.to_frame()` example from the `BcchClient`
  docstring (pandas integration is not shipped yet).
- `AGENTS.md` gotchas updated for the new decode order and retry policy.

## [0.1.0] - 2026-08-06

Initial release.

- BCCh SIE REST client with 7 core series: UF, USD, TPM, IPC_VAR,
  IPC_INDEX, IMACEC, PIB.
- Typed results (`SeriesResult`, `Observation`, `SeriesMeta`), explicit
  date-window queries (never silent full-history downloads).
- SQLite cache with 24h TTL at `~/.econchile/cache.db`.
- Two clients: `BcchClient` (cache-first, interactive) and `OfflineClient`
  (API-first with cache fallback, cron/scheduled jobs).
- Published to PyPI via GitHub Actions trusted publisher (OIDC).
