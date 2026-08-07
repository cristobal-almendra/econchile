# v0.1.1 — Bugfix batch (reliability) — Spec

## What this is

The first post-release maintenance release. Fixes the 5 blockers and 2
packaging/CI gaps found in the consolidated Hermes + OpenCode review of
v0.1.0. No new features. All existing 188 tests must stay green; the new
contract tests below must go from RED to GREEN.

## Scope (exactly these changes, nothing else)

| # | Change | Files |
|---|--------|-------|
| 1 | **latin-1 decode fallback** — BCCh live responses may be ISO-8859-1 (raw accented bytes, e.g. "dólar" as `0xF3`). Decode order: UTF-16 BOM → UTF-8 → latin-1 (latin-1 never fails). | `fetcher.py` (`_decode`), `parsers.py` (bytes branch of `parse_response`) |
| 2 | **Wrap decode failures** — a truncated UTF-16-BOM body (odd byte count) still raises `UnicodeDecodeError`; it must surface as `BcchApiError`, never raw. | `fetcher.py` (`fetch_raw`) |
| 3 | **Retry logic** — 2 retries (3 attempts total) with exponential backoff for *transient* failures only. | `fetcher.py` (`fetch_raw` + `Fetcher.__init__`) |
| 4 | **Narrow `OfflineClient.get` exception catch** — only API/network failures fall back to cache; programming errors must propagate. | `offline.py` |
| 5 | **Fix stale docstring** — `client.py` module docstring advertises `result.to_frame()` which does not exist. Remove the line (pandas is deferred, not advertised). | `client.py` |
| 6 | **`[project.urls]`** — PyPI page must link the repo. | `pyproject.toml` |
| 7 | **CI runs on pull requests** — currently only tag pushes + manual dispatch; add `pull_request:` trigger on `main`. | `.github/workflows/workflow.yml` |
| 8 | Docstring updates — encoding notes in `fetcher.py` and `parsers.py` module docstrings must mention the latin-1 fallback. | `fetcher.py`, `parsers.py` |

Out of scope: version bump (done at release time), stale-cache serving,
new series, `to_frame()`, safe_float thousands separators, dedup of
`_decode`/`_series_code` helpers, thread-safety, `OfflineClient` top-level
export.

## Design decisions

### 3a. Retry policy (the important one)

Retry ONLY what is plausibly transient:

| Failure | Retry? |
|---------|--------|
| `requests.RequestException` (network, timeout, connection) | ✅ yes |
| HTTP status >= 500 | ✅ yes |
| Non-JSON body / HTML "Página no encontrada" page (HTTP 200) → `json.JSONDecodeError` | ✅ yes |
| HTTP status 4xx (bad token, not found) | ❌ no |
| `Codigo != 0` business error (`ParsingError`) | ❌ no |
| `UnicodeDecodeError` (truncated UTF-16) | ❌ no — wrap as `BcchApiError` immediately |

Mechanics:
- `Fetcher.__init__(token=..., timeout_seconds=30, timeout=None, max_retries=2, retry_backoff=0.5)` — `max_retries` = retries AFTER the first attempt (3 total attempts at default). `retry_backoff` = base seconds; sleep `retry_backoff * 2**attempt` between attempts. `retry_backoff=0` disables sleeping (tests).
- The retry loop lives in `fetch_raw` around the GET + parse sequence. `BcchClient`/`OfflineClient` constructors are unchanged (they get the defaults).
- Network errors must STILL report only the exception TYPE (never `str(exc)`, which embeds the URL → token leak). Preserve the existing `from None` behavior.
- `BcchApiError.context["http_status"]` (already set by `_get` for HTTP >= 400) is the discriminator: `>= 500` retryable, `< 500` not. Business-error wraps (no `http_status` key) are never retried.

### 4. OfflineClient catch clause

Replace bare `except Exception as exc:` with:

```python
except (BcchApiError, requests.RequestException, OSError) as exc:
```

(`TimeoutError` is a subclass of `OSError` since 3.3; `requests.Timeout` is a
subclass of `RequestException` — both covered.) Everything else propagates
unmasked. The fallback body (cache get → `BcchOfflineError`) is unchanged.

### 5. client.py docstring

Delete the line `df = result.to_frame()                     # pandas DataFrame`
and adjust the comment on the following line so the example stays valid:

```python
    client = BcchClient()                      # token from BCCH_TOKEN env
    result = client.get("UF", "2024-01-01", "2024-12-31")
    hits = client.search("ipc")                # catalog search
    catalog = client.list_series()             # all v0.1 series
```

## Error behavior (after this release)

| Situation | Raises |
|-----------|--------|
| latin-1 / UTF-8 / UTF-16-BOM response | parsed normally |
| Truncated UTF-16 body | `BcchApiError` (was raw `UnicodeDecodeError`) |
| Transient failure that recovers | succeeds after retry (no error) |
| Persistent transient failure | `BcchApiError` after `max_retries+1` attempts |
| HTTP 4xx / `Codigo != 0` | `BcchApiError` after exactly 1 attempt |
| Programming error inside `Fetcher.fetch` in `OfflineClient.get` | original exception propagates (no cache fallback, no `BcchOfflineError`) |

## Test contract (tests/ — RED first, then GREEN)

New tests (all offline, mocked `requests.get` / stubbed `Fetcher.fetch`):

- `tests/test_fetcher.py`
  - `TestFetchEncoding.test_latin1_response_parsed` — raw latin-1 bytes with
    accented title parse correctly. **RED now** (UnicodeDecodeError).
  - `TestFetchErrors.test_undecodable_body_wrapped_as_bcch_api_error` — BOM +
    odd byte count → `BcchApiError`, not raw `UnicodeDecodeError`. **RED now**.
  - `TestFetchRetry` (new class):
    - `test_network_error_retries_then_succeeds` — 2× ConnectionError then
      valid response → success, 3 calls. **RED now**.
    - `test_network_error_exhausts_retries` — persistent → `BcchApiError`,
      exactly 3 calls. **RED now** (currently 1 call).
    - `test_html_body_retries_then_succeeds` — HTML page then valid response
      → success, 2 calls. **RED now**.
    - `test_html_body_exhausts_retries` — persistent HTML → `BcchApiError`,
      3 calls. **RED now**.
    - `test_http_500_retries` — persistent 500 → `BcchApiError`, 3 calls.
      **RED now**.
    - `test_http_401_not_retried` — 4xx → 1 call only. GREEN guard.
    - `test_business_error_not_retried` — `Codigo != 0` → 1 call only. GREEN guard.
    - `test_token_with_slash_is_url_encoded` — `tok/en/123` → `tok%2Fen%2F123`
      in the URL. GREEN guard.
  - Existing `test_network_error_wrapped` and `test_http_500_raises_bcch_api_error`
    get `max_retries=0, retry_backoff=0` + a comment (they test wrapping, not
    retry; keeps the suite fast).
- `tests/test_parsers.py`
  - Skip guard in the `single_series_response` fixture: if
    `sample_response.json` is absent (sdist installs), `pytest.skip(...)`
    instead of a hard `FileNotFoundError`. GREEN guard (fixture edit).
  - `TestParseResponse.test_latin1_bytes_handled` — raw latin-1 bytes →
    parsed dict with accented title intact. **RED now**.
- `tests/test_offline.py`
  - `TestNonApiExceptions` (new class):
    - `test_non_api_exception_propagates` — `ValueError` from fetch must
      propagate even when the cache has data. **RED now** (current code
      masks it behind the cache fallback).
    - `test_network_error_still_falls_back` — `requests.ConnectionError`
      still serves the cache. GREEN guard.

## Acceptance criteria

1. `python -m pytest tests/ -q` → all green (188 old + new, ~199 total).
2. RED list above went RED before implementation (verified by Hermes).
3. No changes to `econchile/types.py`, `cache.py`, `series_map.py`,
   `converters.py`, `client.py` (except the docstring line), or any spec/test
   outside the listed files.
4. No new dependencies. No `.env`/`study/`/fixture changes.
5. Existing public API signatures of `BcchClient`/`OfflineClient` unchanged.
