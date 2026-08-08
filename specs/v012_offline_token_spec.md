# v0.1.2 — OfflineClient token fix — Spec

## What this is

The only relevant bugfix from the Hermes + OpenCode consensus triage
(observation 7): **the offline client cannot be constructed without a
token**, which defeats its documented purpose ("survives API outages",
cache fallback when the API is unavailable).

## Root cause

- `Fetcher.__init__` raises `ValueError` **at construction** when no token
  is passed and `BCCH_TOKEN` is unset (`econchile/fetcher.py:137-140`).
- `OfflineClient.__init__` instantiates a `Fetcher` (`econchile/offline.py:65`),
  so `OfflineClient()` **cannot even be constructed** without a token —
  even for pure cache reads. A cron job with no token and a warm cache
  crashes at import/construction instead of serving last-known-good data.

## Design decision

**Defer token validation to fetch time, and raise `BcchApiError` (not
`ValueError`) when the token is missing.**

Why `BcchApiError`:
- `OfflineClient.get()` already catches `(BcchApiError, requests.RequestException, OSError)`
  and falls back to the cache — a missing token becomes just another
  "API unavailable" case, handled by the existing fallback with **zero
  logic changes in `offline.py`**.
- `BcchClient.get()` (cache-first) still raises for API calls without a
  token — but cache hits keep working, which is a free improvement.

Why fetch-time, not construction-time:
- Construction must not require network credentials; the object is valid
  even if the credential arrives later (or never, for cache-only use).
- The check happens in `fetch_raw()` before any network I/O, so no HTTP
  request is ever attempted without a token.

## Changes

### `econchile/fetcher.py`
1. `__init__`: remove the construction-time `raise ValueError(...)` when
   `self._token` is falsy. Keep `self._token = token if token is not None
   else os.environ.get("BCCH_TOKEN")` (may now be `None`).
2. `fetch_raw()`: at the top, before any date validation / URL building /
   network I/O:
   ```python
   if not self._token:
       raise BcchApiError(
           "BCCh API token required: pass token=... or set the BCCH_TOKEN env var",
           series=code, desde=desde, hasta=hasta,
       )
   ```
   (import `BcchApiError` from `econchile.types` — check current imports.)
3. Update the `__init__` docstring `Raises:` section: no longer raises
   `ValueError` at construction; `BcchApiError` is raised at fetch time.

### `econchile/offline.py`
- No logic changes. Update docstring only: `ValueError: If no token is
  configured (from Fetcher)` → `BcchApiError: If the API is unreachable
  because no token is configured (raised at fetch time)`. The existing
  fallback already handles it.

### `econchile/client.py`
- Docstring only: the `Raises:`/token note referencing the construction-time
  `ValueError` → now `BcchApiError` at fetch time. Cache hits work without
  a token.

### Docs
- `README.md` "Errors" bullet: note that a missing token raises
  `BcchApiError` only when the API is actually called; `OfflineClient`
  serves cache without a token.
- `AGENTS.md` gotchas: add one line — token optional at construction;
  missing token = API failure at fetch time (offline fallback applies).

## Tests (contract, must fail before implementation)

New tests (all offline, no network, no real token needed):

1. `tests/test_fetcher.py`:
   - `test_constructor_without_token_ok` — `Fetcher(token=None)` with
     `BCCH_TOKEN` deleted from env → constructs without raising.
   - `test_fetch_without_token_raises_bcch_api_error` — same setup, then
     `.fetch(Series.USD, ...)` → `BcchApiError` (context mentions token).
2. `tests/test_offline.py` (new class `TestNoToken`):
   - `test_constructs_without_token` — `OfflineClient(token=None)` with env
     token deleted → constructs.
   - `test_cache_served_without_token` — construct without token, seed
     cache via `offline._cache.set_series(...)`, `get()` → cached result
     returned (no network, no stub needed — the real fetcher raises
     `BcchApiError` before any I/O).
   - `test_offline_error_without_token` — construct without token, empty
     cache, `get()` → `BcchOfflineError`.

Expected RED: tests 1–3 fail at construction (`ValueError`); tests 4–5
also fail at construction. After the fix: all 5 green, plus the existing
201 stay green.

## Acceptance

1. `OfflineClient()` and `BcchClient()` construct without a token.
2. `OfflineClient.get()` serves cached data without a token.
3. `OfflineClient.get()` with no token AND no cache → `BcchOfflineError`
   (a `BcchError` subclass), not `ValueError`.
4. `BcchClient.get()` cache-miss without a token → `BcchApiError`.
5. `python -m pytest tests/ -q` → all green (201 + 5 new).
6. No changes to `offline.py` logic, no version bump, no new dependencies.
