# Scratch Examples Spec — "macro in few lines"

## Goal

Show Cristobal what econchile can do in the FEWEST lines possible, mixing
his library + matplotlib + (optional) pandas. These are TEST/PLAY scripts —
not project deliverables. They go in a `scratch/` directory at repo root
(create it), gitignored. If Cristobal likes them later, they get promoted
to examples/ in a future commit.

## Design principles

1. **Fewest lines wins.** Each script's core is ≤ 15 lines of user code.
2. **Human-readable output.** Print values with labels ("UF today: 40,844"),
   not raw dicts.
3. **Graceful token handling.** Read BCCH_TOKEN from env; if missing, try
   loading the repo's `.env` file (one level up: `../.env` — repo root)
   with a tiny manual parser (NO python-dotenv dependency). If still
   missing, print a friendly "set BCCH_TOKEN" message and exit.
4. **No API abuse.** Each live script makes at most a few requests, always
   with explicit date ranges (never full history) — the BCCh API ignores
   missing ranges and downloads 16K rows.
5. **Offline-friendly where possible.** Scripts that don't need the API
   use `examples/demo.py` data or cached results.

## Scripts to write (scratch/)

### 1. `scratch/uf_today.py` — THE 5-liner
Print the latest UF value and its date. Core must be ~5 lines:
```python
from econchile import BcchClient, Series
client = BcchClient()
r = client.get(Series.UF, "2026-01-01", "2026-12-31")
last = r.observations[-1]
print(f"UF {last.date}: {last.value:,.2f}")
```
(adjust date range to something recent-ish; use a fixed recent window like
the current year)

### 2. `scratch/plot_uf_usd.py` — two series on one chart (matplotlib)
Fetch UF and USD for a window, plot both as lines with a legend.
Include the 1-line conversion to matplotlib-friendly lists:
```python
dates = [o.date for o in r.observations]
values = [o.value for o in r.observations]
```
Use plt.plot, legend, tight_layout, show(). ~12-15 lines core.

### 3. `scratch/dashboard.py` — ALL 7 series, 7-panel grid (matplotlib)
Loop over the 7 Series members, fetch each with a recent window,
plot each in its own subplot (2x4 grid, 7 filled). Titles = series names.
~20 lines core. This is the "wow" script.

### 4. `scratch/pandas_uf.py` — pandas convenience (if pandas installed)
The 2-line conversion to a DataFrame:
```python
import pandas as pd
df = pd.DataFrame([(o.date, o.value) for o in r.observations], columns=["date", "value"])
print(df.tail())
```
Shows how a user bridges econchile → pandas. ~10 lines.

### 5. `scratch/cached_second_call.py` — demonstrate the cache
Call client.get() twice for the same series+window, print how fast the
second call is (time.perf_counter delta) and note it came from cache.
Shows the 24h TTL benefit. ~12 lines.

## Shared helper (optional but nice)
`scratch/_common.py` with `load_token()` and `fmt_number()` — the other
scripts import it. Keep it tiny.

## Rules
- Do NOT touch anything in econchile/, examples/, tests/, specs/.
- Create scratch/ + add `scratch/` to .gitignore (append a line).
- Do NOT install matplotlib/pandas (may not be present — guard imports
  with try/except ImportError and print "pip install matplotlib" hint).
- Do NOT commit anything.
- Scripts must run from repo root: `python scratch/uf_today.py` with
  `sys.path` bootstrap to import econchile from the repo (like
  examples/demo.py does).
- Each script prints a small header + friendly output.

## Verification
- Run each script. Live scripts (UF, USD, dashboard, pandas, cache) need
  the token — they should work (token is in ../.env).
- If matplotlib is missing, the plot scripts must exit gracefully with
  the install hint (they can't be fully verified — report that clearly).
- Report: which ran fully, which exited gracefully, any errors.

## Note to OpenCode
Cristobal may install matplotlib right after you finish — the scripts
should work the moment he does, with zero edits. Test what you can;
be explicit about what you couldn't verify.