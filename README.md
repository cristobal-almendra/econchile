# econchile

[![PyPI version](https://img.shields.io/pypi/v/econchile.svg)](https://pypi.org/project/econchile/)
[![Python versions](https://img.shields.io/pypi/pyversions/econchile.svg)](https://pypi.org/project/econchile/)
[![CI](https://github.com/cristobal-almendra/econchile/actions/workflows/workflow.yml/badge.svg)](https://github.com/cristobal-almendra/econchile/actions/workflows/workflow.yml)

Chilean macroeconomic data (Banco Central de Chile) for Python.

`econchile` is a thin, practical client for the BCCh SIE REST web service. It downloads official series (UF, USD, TPM, IPC_VAR, IPC_INDEX, IMACEC, PIB), parses them into clean, typed data, and keeps a local SQLite cache so repeat queries are instant and your scripts survive API outages.

## Install

```bash
pip install econchile
```

Requires Python 3.10+. To install from source instead:

```bash
git clone https://github.com/cristobal-almendra/econchile.git
cd econchile
pip install -e .
```

## Authentication

Request a free API token from the BCCh statistics database (SIE), see the official API documentation.

```bash
export BCCH_TOKEN="your-token-here"
```

The library reads `BCCH_TOKEN` from the environment — it does not load `.env` files itself. The token is required for v0.1.

## Quickstart

```python
from econchile import BcchClient, Series

client = BcchClient()

# Last 3 months of the UF (daily)
result = client.get(Series.UF, "2024-01-01", "2024-03-31")

for obs in result.observations:
    print(obs.date, obs.value)
```

Dates are always `YYYY-MM-DD`. Missing observations have `value=None`.

## The two clients

| Client | Strategy | Best for |
|--------|----------|----------|
| `BcchClient` | **Cache-first** — serves from the local cache when fresh, hits the API only on a miss | Interactive use, repeated queries |
| `OfflineClient` | **API-first** — always tries the API, falls back to the cache when it fails | Cron jobs and scripts that must not crash |

```python
from econchile.offline import OfflineClient

client = OfflineClient()
result = client.get(Series.USD, "2024-01-01", "2024-03-31")  # survives API outages
```

## Available series (v0.1)

| Series | BCCh code | Frequency | Meaning |
|--------|-----------|-----------|---------|
| `Series.UF` | `F073.UFF.PRE.Z.D` | daily | Unidad de Fomento |
| `Series.USD` | `F073.TCO.PRE.Z.D` | daily | Nominal exchange rate (CLP/USD) |
| `Series.TPM` | `F022.TPM.TIN.D001.NO.Z.D` | daily | Monetary policy rate |
| `Series.IPC_VAR` | `F074.IPC.VAR.Z.Z.C.M` | monthly | CPI, month-over-month change |
| `Series.IPC_INDEX` | `F074.IPC.IND.Z.2023.C.M` | monthly | CPI general index (base 2023=100) |
| `Series.IMACEC` | `F032.IMC.IND.Z.Z.EP18.Z.Z.0.M` | monthly | Economic activity index (base 2018=100) |
| `Series.PIB` | `F032.PIB.FLU.R.CLP.EP18.Z.Z.0.T` | quarterly | GDP, chained volumes (base 2018) |

More series are planned. Use `client.list_series()` for the full catalog and `client.search("ipc")` to find series by keyword:

```python
hits = client.search("ipc")     # matches name, code, Spanish and English titles
for meta in hits:
    print(meta.series_id, meta.spanish_title)
```

## Gotchas

- **Date format**: pass `YYYY-MM-DD` to `get()`; the library converts the API's native `DD-MM-YYYY` for you.
- **Missing data**: the BCCh API marks gaps as "ND". These become `value=None`, not zeros or exceptions, check for `None` before using a value.
- **Representations**: `IPC_VAR` is a monthly % change, `IPC_INDEX` is a base-2023 index. Same variable, different meaning.
- **Cache freshness**: cached results are reused for 24 hours by default; configure via `ttl_seconds` on `BcchClient(...)` or `OfflineClient(...)` (the cache lives at `~/.econchile/cache.db`).
- **Errors**: unknown series raise `KeyError`, malformed dates raise `ValueError`, API failures raise `BcchApiError` and `BcchOfflineError` when the offline fallback is also exhausted. **No token?** Both clients construct fine without one — the token is only needed when the API is actually called: `BcchClient` cache hits work, and `OfflineClient` serves cached data (a missing token is treated as an API failure, so the cache fallback applies).
- **Token with special characters**: BCCh API tokens may contain `/` characters. The library URL-encodes them automatically via `urllib.parse.urlencode` (`/` → `%2F`), so you can paste the token as-is. Only if you build request URLs *by hand* (e.g. `curl`) do you need to encode it yourself — `urllib.parse.quote(token)` — otherwise the BCCh API rejects the request.

## API

- `BcchClient.get(series, desde, hasta, use_cache=True)` — fetch a series over a date range; returns a `SeriesResult`.
- `OfflineClient.get(series, desde, hasta)` — same, but API-first with cache fallback.
- `BcchClient.search(keyword)` — case- and accent-insensitive catalog search → `list[SeriesMeta]`.
- `BcchClient.list_series()` — all series metadata → `list[SeriesMeta]`.
- `BcchClient.clear_cache()` — empty the local cache (returns the number of rows removed).

A `SeriesResult` has:

- `series` — the `Series` member
- `observations` — list of `Observation(date: str, value: float | None)`
- `fetched_at` — timestamp (UTC)
- `source` — `"api"`, `"cache"`, or `"partial"`
- `metadata` — series info (titles, frequency, representation)

## Development

```bash
pip install -e . && pip install pytest
python -m pytest tests/
```

## License

MIT
