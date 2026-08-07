# Bug Fix Spec — cache.py `make_key` + `:memory:` support

Two confirmed bugs in `econchile/cache.py`. Fix both + add regression tests.

## Bug 1: `make_key()` does not normalize `Series` enums

**Repro:**
```python
>>> make_key(Series.USD, "2024-01-01", "2024-01-05")
'Series.USD|2024-01-01|2024-01-05'   # WRONG — enum repr, not code
>>> make_key("F073.TCO.PRE.Z.D", "2024-01-01", "2024-01-05")
'F073.TCO.PRE.Z.D|2024-01-01|2024-01-05'  # correct
```

**Root cause:** `make_key` f-strings the `series` arg directly. The module
already has `_series_code()` (normalizes `Series` → `.value`) but
`make_key` doesn't use it.

**Fix:** `make_key(series, desde, hasta)` → normalize via `_series_code(series)`:
```python
return f"{_series_code(series)}|{desde}|{hasta}"
```
- `make_key(Series.USD, ...)` → `F073.TCO.PRE.Z.D|...`
- `make_key("F073.TCO.PRE.Z.D", ...)` → identical (backwards compatible)
- `make_key` must keep accepting both `Series` and `str`

**Why it matters:** a caller passing the enum gets a DIFFERENT cache key
than a caller passing the code — same query, two cache entries, and the
second lookup always misses. Silent cache ineffectiveness.

## Bug 2: `Cache(db_path=":memory:")` is broken

**Repro:**
```python
c = Cache(db_path=":memory:")
c.set("k", result)   # works (creates table? no — schema already gone)
c.get("k")           # sqlite3.OperationalError: no such table: cache
```

**Root cause:** SQLite `:memory:` databases live INSIDE a connection.
`Cache._connect()` opens a NEW connection per call. `_init_db()` creates
the schema in a `with` block → the connection closes → the in-memory DB
(and its schema) is destroyed. Every later call opens a fresh empty
`:memory:` DB.

**Fix:** hold a persistent connection when `db_path == ":memory:"`:

```python
def __init__(...):
    self._db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    self._ttl_seconds = ttl_seconds
    self._memory_conn: sqlite3.Connection | None = None
    if str(self._db_path) == ":memory:":
        # :memory: DBs live inside a connection — keep one open for life.
        self._memory_conn = sqlite3.connect(":memory:")
    self._init_db()

def _connect(self) -> sqlite3.Connection:
    if self._memory_conn is not None:
        return self._memory_conn   # persistent — schema survives
    return sqlite3.connect(str(self._db_path))
```

Notes:
- Do NOT wrap the persistent connection in `with` in `_init_db` — use
  `try/finally` or just call `execute` without context-manager closing.
  Simplest: in `_init_db`, if `self._memory_conn` is set, run DDL on it
  directly; otherwise use the existing `with self._connect()` pattern.
- Same for `get`/`set` — the existing `with self._connect() as conn`
  pattern will close the persistent connection! Guard those: when using
  the persistent connection, don't context-close it. Pattern:
  ```python
  conn = self._connect()
  try:
      ... sqlite work ...
  finally:
      if self._memory_conn is None:
          conn.close()
  ```
  or extract a helper `_run(query, params)` that handles both cases.
- Keep the public behavior identical for file-based DBs (new connection
  per call is fine there).

**Why it matters:** `:memory:` is the standard way tests AND scripts
(playground options 4/5/6) avoid touching `~/.econchile/cache.db`. The
broken behavior silently fails cache-first clients.

## Test contract (add to tests/test_cache.py)

Add these tests — full bodies, not signatures:

1. `test_make_key_normalizes_enum` — `make_key(Series.USD, "2024-01-01", "2024-01-05") == "F073.TCO.PRE.Z.D|2024-01-01|2024-01-05"`
2. `test_make_key_enum_matches_string` — enum and code forms give the SAME key
3. `test_memory_cache_set_get_roundtrip` — `Cache(db_path=":memory:")`: set then get returns the result
4. `test_memory_cache_size` — size() works on `:memory:` cache
5. `test_memory_cache_get_missing_returns_none` — `:memory:` get on unknown key → None
6. `test_memory_cache_clear` — clear() works on `:memory:` cache

Keep existing tests untouched (they use `tmp_path` file DBs — must stay green).

## Verification
- `python -m pytest tests/test_cache.py -v` → all pass (old + new)
- `python -m pytest tests/ -q` → full suite still green (219 + 6)
- Quick repro check: the two snippets above behave correctly after the fix
