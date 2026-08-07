# cache.py — Spec

## What it does

SQLite-backed cache for BCCh API responses. Stores `SeriesResult` objects
(see `types.py`) with a 24-hour TTL. The fetcher checks the cache before
hitting the network; `offline.py` falls back to it when the API is down.

This is the SECOND layer of the fallback chain: API → **cache** → error.

## Key design

### Cache key
The cache key encodes WHICH query produced the data:
```
{series_code}|{desde}|{hasta}
```
e.g. `F073.TCO.PRE.Z.D|2024-01-01|2024-12-31`

Different date ranges of the same series are DIFFERENT cache entries.
This is critical — a cached full-history response must not be served
when the user asked for last week.

### Storage
SQLite table `cache`:

| Column | Type | Notes |
|--------|------|-------|
| `key` | TEXT PRIMARY KEY | The cache key above |
| `payload` | TEXT | JSON-serialized `SeriesResult` (via `to_dict()`) |
| `fetched_at` | TEXT | ISO timestamp when the API response was fetched |
| `expires_at` | TEXT | ISO timestamp = fetched_at + TTL |

### TTL
- Default TTL: 24 hours (86400 seconds)
- Configurable via constructor arg
- On `get()`, if `expires_at < now`, treat as a miss (return None) —
  and delete the row (don't serve stale data)

### Location
- Default DB path: `~/.econchile/cache.db` (created on first use)
- Overridable via constructor arg for tests
- Parent directory auto-created

## Public API

### `class Cache`
```python
Cache(db_path: str | Path | None = None, ttl_seconds: int = 86400)
```

| Method | Signature | Returns | Behavior |
|--------|-----------|---------|----------|
| `get` | `get(key: str) -> SeriesResult \| None` | `SeriesResult` or None | None if missing OR expired (expired rows deleted) |
| `set` | `set(key: str, result: SeriesResult) -> None` | None | Upserts; sets fetched_at=now, expires_at=now+ttl |
| `get_series` | `get_series(series: str, desde: str, hasta: str) -> SeriesResult \| None` | Same as get | Convenience: builds key from components |
| `set_series` | `set_series(series: str, desde: str, hasta: str, result: SeriesResult) -> None` | None | Convenience: builds key from components |
| `clear` | `clear() -> int` | Number of rows deleted | Empties the whole cache table |
| `size` | `size() -> int` | Row count | Total entries stored |

### `make_key(series: str, desde: str, hasta: str) -> str`
Module-level helper: `f"{series}|{desde}|{hasta}"`.

## Reconstruction from stored data

`get()` must rebuild a `SeriesResult` from the stored JSON payload:

- `series` field: stored as a string code (e.g. `"F073.TCO.PRE.Z.D"`).
  Reconstruct as the matching `Series` enum member IF it exists in the
  v0.1 catalog (`Series.from_code()`), else keep the raw string.
- `observations`: stored as list of `{"date": ..., "value": ...}`.
  Reconstruct as a list of `Observation(date=..., value=...)` objects.
- `fetched_at`: parse the ISO string back into a `datetime`.
- `source`: keep as stored (should be `"cache"` when read back).
- `metadata`: pass through as-is (dict).

## Error handling

- SQLite I/O failures → raise `BcchCacheError` (from `types.py`)
- Do NOT raise when a key is missing — `get()` returns None
- Do NOT raise on expired entries — treat as miss and delete

## Dependencies
- `sqlite3` (stdlib)
- `json` (stdlib)
- `datetime` (stdlib)
- `econchile.types`: `SeriesResult`, `Observation`, `BcchCacheError`
- `econchile.series_map`: `Series` (for code → enum reconstruction)

## Test constraints
- Tests MUST NOT touch `~/.econchile/` — always pass an explicit
  `db_path` (use `tmp_path` fixture)
- Use `monkeypatch`/explicit TTL for expiry tests — never sleep()
