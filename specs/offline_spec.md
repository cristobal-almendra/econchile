# offline.py — Spec

## What it does

The **resilience layer** of econchile. Implements the fallback chain:

```
API → cache → BcchOfflineError (helpful message)
```

Distinct from `client.py`:
- `client.py.get()` is **cache-first** (performance: serve TTL-fresh cache
  without touching the network).
- `offline.py` is **API-first** (freshness: always try the live API, and
  only fall back to the cache when the API *fails*).

Use case: scheduled jobs / scripts that must not crash when the BCCh API
is down or rate-limiting. `offline.py` degrades gracefully: fresh data
when possible, last-known-good from cache when not, and a clear, actionable
error when neither is available.

## Public API

### `class OfflineClient`
```python
OfflineClient(token: str | None = None,
              db_path: str | Path | None = None,
              ttl_seconds: int = 86400,
              timeout: int = 30)
```
Same construction as `BcchClient` — wraps `Fetcher` + `Cache`.

| Method | Signature | Returns | Behavior |
|--------|-----------|---------|----------|
| `get` | `get(series, desde, hasta) -> SeriesResult` | `SeriesResult` | API-first, cache fallback, error last |

### `get()` semantics

1. Resolve `series` (accept `Series` enum, human name, or raw code —
   reuse the same resolution logic as `client.py`).
2. Validate `desde`/`hasta` (reuse `fetcher._validate_dates`).
3. Try `fetcher.fetch(series, desde, hasta)`:
   - **Success** → return the fresh `SeriesResult` (source=`"api"`),
     AND write it to the cache (so the fallback is warm next time).
   - **Failure** (`BcchApiError`, network error, timeout) → go to step 4.
4. Try `cache.get(key)`:
   - **Hit** → return the cached `SeriesResult` (source as stored,
     typically `"api"` from when it was fetched — the caller can check
     `result.source` or the cache's own timestamp).
   - **Miss / expired** → go to step 5.
5. Raise `BcchOfflineError` with a helpful message:
   - The original API error (type + message).
   - The series and date window that failed.
   - A hint that the cache had nothing usable.
   - If a cache hit was EXPIRED, include its timestamp so the user knows
     how stale the data would have been.

### Error context (BcchOfflineError)
Use `BcchOfflineError(message, **context)` from `types.py` — it stores
kwargs in `self.context`. Include:
- `series` — the resolved code
- `desde`, `hasta` — the window
- `api_error` — str of the original exception
- `cache_had_data` — bool (False if miss, True if expired-but-present)

## Key design rules

1. **Cache writes on API success** — the fallback is only useful if it's
   warm. Every successful fetch refreshes the cached copy.
2. **Cache reads tolerate expiry for fallback** — different from
   `client.py`! For resilience, serving slightly-stale data is better than
   crashing. The spec's `Cache.get()` deletes expired rows, so offline
   should either (a) use a lower-level read that returns expired entries,
   or (b) accept that expired == miss and report it. **Decision: keep it
   simple — use `Cache.get()` as-is (expired == miss) and report
   `cache_had_data=False`.** Stale-serving is a v0.2 enhancement.
3. **Never mask the original error** — the raised `BcchOfflineError`
   must include the original API error string so debugging is possible.
4. **No new dependencies** — reuses `Fetcher`, `Cache`, `types`.

## Dependencies
- `econchile.fetcher`: `Fetcher`, `_validate_dates`
- `econchile.cache`: `Cache`, `make_key`
- `econchile.series_map`: `Series`
- `econchile.types`: `SeriesResult`, `BcchOfflineError`
- `econchile.client`: `_resolve_series` (reuse — do NOT reimplement)

## Test constraints
- No real API calls — monkeypatch `Fetcher.fetch` (or `requests.get`).
- Fake a cache with `tmp_path` DB.
- Cover the three paths: API success, API failure + cache hit,
  API failure + cache miss (→ `BcchOfflineError`).
- Verify cache is WRITTEN on API success.
- Verify `BcchOfflineError.context` contains the original API error.
