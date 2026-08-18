"""
econchile — charts demo (LIVE API + offline fallback)
======================================================

Shows what econchile does in the best possible way:

  1. "USD today" — pulled LIVE from the Banco Central de Chile API
     (requires BCCH_TOKEN in the environment; if missing or the API
     is down, it falls back to the bundled offline fixture).
  2. A clean USD/CLP monthly chart for 2000–2010 — live API data,
     aggregated to month-end, with the same offline fallback.

Run it with:
    export BCCH_TOKEN=*** .env | sed -n 's/^BCCH_TOKEN=***
    python examples/charts_demo.py
"""

import csv
import os
import re
import sys
from collections import OrderedDict

import matplotlib
matplotlib.use("Agg")  # headless-safe: no display needed
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
CSV_PATH = os.path.join(REPO_ROOT, "data", "macro-chile-lean.csv")
OUT_PNG = os.path.join(HERE, "dolar_2000_2010.png")

START_YEAR, END_YEAR = 2000, 2010

# Make the package importable when running from the repo (dev mode);
# when installed via pip, the normal import path already works.
if os.path.isdir(os.path.join(REPO_ROOT, "econchile")):
    sys.path.insert(0, REPO_ROOT)

try:
    from econchile import BcchClient, Series
    LIB_OK = True
except ImportError:
    LIB_OK = False


# --------------------------------------------------------------------------
# Offline fallback: read the bundled fixture (no token, no network)
# --------------------------------------------------------------------------
def _parse_period(text: str):
    m = re.match(r"([a-z]+)\.(\d{4})", text.strip().lower())
    if not m:
        return None
    months = {
        "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
        "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
    }
    month = months.get(m.group(1))
    if month is None:
        return None
    return (int(m.group(2)), month)


def _parse_number(text: str):
    if text is None:
        return None
    cleaned = text.strip().replace("\xa0", "").replace(" ", "")
    if not cleaned:
        return None
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _load_offline_series():
    """Return [(year, month, value)] from the bundled CSV (TCN column)."""
    out = []
    with open(CSV_PATH, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            period = _parse_period(row.get("Periodo", ""))
            value = _parse_number(row.get("TCN"))
            if period and value is not None:
                out.append((period[0], period[1], value))
    return sorted(out)


# --------------------------------------------------------------------------
# Live API path
# --------------------------------------------------------------------------
def _fetch_live():
    """Return (daily_obs, source_label) or (None, error_message)."""
    if not LIB_OK:
        return None, "econchile not installed (pip install econchile)"
    token = os.environ.get("BCCH_TOKEN", "")
    if not token:
        return None, "BCCH_TOKEN not set — falling back to offline fixture"
    try:
        client = BcchClient()
        obs = client.get(Series.USD, f"{START_YEAR}-01-01", f"{END_YEAR}-12-31",
                         use_cache=False).observations
        if not obs:
            return None, "API returned no observations"
        return obs, "Banco Central de Chile API (live)"
    except Exception as exc:  # any API failure → fall back gracefully
        return None, f"API unavailable ({type(exc).__name__}) — using offline fixture"


def _monthly_from_daily(daily_obs):
    """Aggregate daily obs to month-end values: [(year, month, value)]."""
    months = OrderedDict()
    for obs in daily_obs:
        if obs.value is None:
            continue
        y, m, _ = obs.date.split("-")
        key = (int(y), int(m))
        months[key] = float(obs.value)  # last observation of the month wins
    return [(y, m, v) for (y, m), v in months.items()]


def main():
    print("=" * 66)
    print("  econchile — USD/CLP demo")
    print("=" * 66)

    # --- 1. Try the live API ------------------------------------------------
    daily, source_label = _fetch_live()
    if daily:
        series = _monthly_from_daily(daily)
        print(f"  data source : {source_label}")
        print(f"  daily obs   : {len(daily)}  →  monthly: {len(series)}")
    else:
        series = _load_offline_series()
        print(f"  data source : {source_label}")
        print(f"  obs (offline fixture, quarterly): {len(series)}")

    # --- 2. USD today --------------------------------------------------------
    if daily:
        today = daily[-1]
        print(f"\n  USD today   : {today.date} → {today.value:,.2f} CLP  (live)")
    else:
        last_y, last_m, last_v = series[-1]
        print(f"\n  USD latest  : {last_y:04d}-{last_m:02d} → {last_v:,.2f} CLP  (fixture)")

    # --- 3. Sample lines for 2000-2010 ---------------------------------------
    window = [(y, m, v) for (y, m, v) in series if START_YEAR <= y <= END_YEAR]
    print(f"\n  USD/CLP sample, {START_YEAR}-{END_YEAR} ({len(window)} monthly obs):")
    step = max(1, len(window) // 6)
    for y, m, v in window[::step]:
        print(f"    {y:04d}-{m:02d}  →  {v:,.2f} CLP per USD")

    # --- 4. Chart -------------------------------------------------------------
    x = [f"{y}-{m:02d}" for y, m, _ in window]
    y = [v for _, _, v in window]

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    ax.plot(x, y, color="#0b5394", linewidth=2)
    ax.fill_between(range(len(x)), y, color="#0b5394", alpha=0.08)
    ax.set_title(f"USD/CLP — monthly, {START_YEAR}–{END_YEAR} (BCCh via econchile)")
    ax.set_ylabel("CLP per USD")
    tick_step = max(1, len(x) // 10)
    ax.set_xticks(range(0, len(x), tick_step))
    ax.set_xticklabels([x[i] for i in range(0, len(x), tick_step)], rotation=45, fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT_PNG)
    print(f"\n  chart saved → {os.path.relpath(OUT_PNG, HERE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
