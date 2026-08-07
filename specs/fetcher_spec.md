# fetcher.py — Spec

## What it does

Sync HTTP client that fetches BCCh REST API responses for a single series,
converts them into `SeriesResult` objects, and raises `BcchApiError` on API
errors. This is the FIRST layer of the fallback chain: **API → cache → error**.

## API endpoint (confirmed by live tests)

```
GET https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx
    ?token={TOKEN}
    &function=GetSeries
    &timeseries={SERIES_CODE}
    &firstDate={YYYY-MM-DD}
    &lastDate={YYYY-MM-DD}
```

### Confirmed facts (from live curl tests, do NOT re-verify):
- **`firstDate`/`lastDate` are the correct range params.** The Python
  library docs say `desde`/`hasta`, but the REST endpoint IGNORES those —
  passing `desde`/`hasta` returns the FULL history (16,068 obs).
  Using `firstDate`/`lastDate` correctly returns only the requested window.
- **Response encoding is UNSTABLE.** Sometimes UTF-16 with BOM
  (`FF FE`), sometimes plain UTF-8. The decoder MUST detect: check for
  BOM → decode utf-16; otherwise try utf-8. Do NOT hardcode one encoding.
- Multi-series via repeated `timeseries` params returns error `Codigo: -50`.
  One series per request. Batching is the CALLER's job (fetch in a loop).
- Error responses come back as HTTP 200 with `Codigo != 0` in the JSON body.

## Public API

### `class Fetcher`
```python
Fetcher(token: str | None = None, timeout_seconds: int = 30)
```
- `token`: API key. If None, read from env var `BCCH_TOKEN`.
- `timeout_seconds`: HTTP timeout.

| Method | Signature | Returns | Behavior |
|--------|-----------|---------|----------|
| `fetch` | `fetch(series, desde, hasta) -> SeriesResult` | `SeriesResult` | Fetches + parses + wraps in SeriesResult |
| `fetch_raw` | `fetch_raw(series, desde, hasta) -> dict` | Raw parsed dict | Lower-level: just the parsed response dict (for tests/debug) |

### `series` parameter
Accepts either a `Series` enum member (from `series_map.py`) or a raw
code string. Normalize internally with `str(series)` / `Series.from_code()`.

### `desde`/`hasta` parameters
Strings in `YYYY-MM-DD`. **Mapped to `firstDate`/`lastDate` in the URL.**

## Request flow (fetch)

1. Normalize `series` to a code string.
2. Validate `desde`/`hasta` look like `YYYY-MM-DD` (regex) — raise
   `ValueError` early with a clear message if not.
3. Build URL with `firstDate`/`lastDate` (NOT desde/hasta).
4. `requests.get(url, timeout=...)` — on network/HTTP errors, wrap in
   `BcchApiError`.
5. Decode response body (BOM detection: utf-16 vs utf-8).
6. `parse_response()` from parsers.py → clean dict.
   - It raises `ParsingError` on `Codigo != 0` → wrap in `BcchApiError`.
7. Build `SeriesResult`:
   - `series`: the `Series` enum member (via `Series.from_code`) or raw string
   - `observations`: `Observation(date=..., value=...)` objects
   - `fetched_at`: `datetime.now(timezone.utc)`
   - `source`: `"api"`
   - `metadata`: from the parsed dict (`descripEsp`, `descripIng`, `series_infos`)

## Error handling
- `BcchApiError(message, ...)` from `types.py` for:
  - Network errors (DNS, connection refused, timeout)
  - Non-200 HTTP status
  - `Codigo != 0` in response (wrap `ParsingError`)
- `ValueError` for malformed `desde`/`hasta` (client error, not API error)

## Dependencies
- `requests` (external — add to pyproject dependencies)
- `re` (stdlib, for YYYY-MM-DD validation)
- `os` (env var)
- `econchile.parsers`: `parse_response`
- `econchile.types`: `SeriesResult`, `Observation`, `BcchApiError`
- `econchile.series_map`: `Series`

## Test constraints
- Tests MUST NOT hit the real API. Use `responses` library or monkeypatch
  `requests.get` with fake responses.
- Fake responses must include BOTH encodings (UTF-16 BOM and UTF-8) to
  cover the encoding-detection logic.
- No `.env` dependency in tests — always pass `token` explicitly or
  monkeypatch the env var.
