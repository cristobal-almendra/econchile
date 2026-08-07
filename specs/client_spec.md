# client.py — Spec

## What it does

The **user-facing API** of econchile. Wraps `fetcher` (network) + `cache`
(SQLite) + `series_map` (catalog) + `types` (data structures) into a simple
`BcchClient` that users interact with.

The USER's mental model:
```python
from econchile import BcchClient
client = BcchClient()                    # token from BCCH_TOKEN env
df = client.get("UF", "2024-01-01", "2024-12-31")   # SeriesResult
results = client.search("ipc")           # catalog search
schema = client.list_series()            # all v0.1 series
```

## Key design

### Data flow for `get()` — cache-first
```
get(series, desde, hasta):
  1. key = make_key(series, desde, hasta)
  2. cache.get_series(...) → HIT? return it
  3. MISS → fetcher.get_series(...)  (hits real API)
  4. cache.set_series(...)           (store for next time)
  5. return result
```
- Cache-first: avoids redundant network calls within TTL (24h)
- On API failure: cache is already checked; if both miss → BcchApiError propagates
- `use_cache: bool = True` param to bypass cache when user wants fresh data

### Series identifier
- `get()`/`search()` accept `str` (human name like "UF", "USD", "IPC_VAR")
  OR `Series` enum member
- String lookup is case-insensitive and matches enum NAME, not just code:
  "uf" → Series.UF, "IPC_VAR" → Series.IPC_VAR, "F073.TCO.PRE.Z.D" → Series.USD
- Unknown name → raise `KeyError` with helpful message listing available series

### search()
- Keyword search over series metadata (spanish_title, english_title, name, code)
- Case-insensitive substring match
- Returns list of `SeriesMeta`
- "ipc" matches both IPC_VAR and IPC_INDEX; "dolar"/"dólar" matches USD

### list_series()
- Returns all v0.1 series as `list[SeriesMeta]` (ordered like the enum)

## Public API

### `class BcchClient`
```python
BcchClient(
    token: str | None = None,        # passed to Fetcher
    db_path: str | Path | None = None,  # passed to Cache
    ttl_seconds: int = 86400,        # passed to Cache
    timeout: int = 30,               # passed to Fetcher
)
```

| Method | Signature | Returns | Notes |
|--------|-----------|---------|-------|
| `get` | `get(series, desde, hasta, use_cache=True) -> SeriesResult` | SeriesResult | Main entry. Cache-first, then API |
| `search` | `search(keyword: str) -> list[SeriesMeta]` | list[SeriesMeta] | Catalog keyword search |
| `list_series` | `list_series() -> list[SeriesMeta]` | list[SeriesMeta] | All v0.1 series |
| `clear_cache` | `clear_cache() -> int` | int | Delegates to Cache.clear() |

`desde`/`hasta` validated as YYYY-MM-DD (reuse fetcher's validation via
Fetcher — client calls fetcher which validates; ALSO validate in client
before touching cache so bad dates never hit the cache lookup).

## Error behavior

| Situation | Raises |
|-----------|--------|
| Unknown series name | `KeyError` with helpful message |
| Bad desde/hasta | `ValueError` |
| Cache miss + API fail | `BcchApiError` (propagates from fetcher) |
| No token configured | `ValueError` (from Fetcher init) |

## Dependencies
- `econchile.fetcher`: `Fetcher`
- `econchile.cache`: `Cache`, `make_key`
- `econchile.series_map`: `Series`
- `econchile.types`: `SeriesResult`, `SeriesMeta`, `BcchApiError`
- stdlib: `os`, `re`, `pathlib`

## Test constraints
- NEVER hit real API — monkeypatch `Fetcher.get_series` or inject a fake
- Cache tests use `tmp_path` db (never `~/.econchile`)
- Constructor dependency injection: `BcchClient(token=..., db_path=tmp_path)` so
  tests can use a temp cache
- Test cache-first: fake fetcher that raises if called; seed cache; get() returns
  cached without calling fetcher
- Test cache-miss: fake fetcher returns result; get() stores it; second get()
  hits cache
