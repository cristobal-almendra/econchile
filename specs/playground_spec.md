# playground.py — Spec

## What it is

An **interactive, menu-driven script** that lets a user test econchile like a
real user would — WITHOUT needing the API token or network for most options.
Runs from the project root: `python playground.py`.

This is a dev/learning tool, NOT part of the library. No tests, no annotated
version. Style: simple, friendly, with clear numbered output.

## Menu structure

Print a numbered menu. The user picks an option (input()), the script runs it,
shows output, then returns to the menu until they choose Exit.

```
═══════════════════════════════════════
  econchile playground — try it out
═══════════════════════════════════════
  1. List all series (catalog)
  2. Search series by keyword
  3. Parse the real API sample (offline)
  4. Cache round-trip (in-memory DB)
  5. Offline fallback (simulated API failure)
  6. Live API query (needs BCCH_TOKEN)
  0. Exit
═══════════════════════════════════════
```

## Options in detail

### 1. List all series
- `BcchClient(db_path=":memory:", token="dummy").list_series()`
- Print: name (enum), code, frequency, representation, english title.
- NO network, NO real token needed.

### 2. Search series
- Prompt: "Search term: " → `client.search(term)`
- Print each hit: code + english title. Show that search is case- and
  accent-insensitive (e.g. searching "dolar" finds the USD series).
- If no hits: "No matches — try 'ipc', 'dolar', 'uf', 'pib'."

### 3. Parse real API sample (offline)
- Read `sample_response.json` from the project root (UTF-16 BOM bytes).
- `parse_response(raw)` → print: series_id, total observations,
  first 3 observations, count of None values (ND points).
- This proves the full parsing pipeline works on REAL BCCh data, offline.

### 4. Cache round-trip (in-memory DB)
- Build a `SeriesResult` by parsing the sample response.
- `Cache(db_path=":memory:")` → `set(key, result)` → `get(key)`.
- Print: key, hit/miss, observations count before vs after, source.
- Proves serialization → storage → reconstruction works.

### 5. Offline fallback (simulated API failure)
- `OfflineClient(token="bad-token", db_path=":memory:")`
- Call `.get(Series.UF, "2024-01-01", "2024-01-10")` — the API will FAIL
  (bad token) and the cache is empty.
- Catch `BcchOfflineError`, print `e.context` (series, desde, hasta,
  api_error, cache_had_data).
- Message: "This is what happens when the API is down AND the cache is cold.
  A real user would see this error. With a warm cache, you'd get data instead."
- NOTE: this makes a REAL network call (the bad token still hits the API
  and gets rejected). It's safe — no valid token is used — but mention in
  output that it needs internet.

### 6. Live API query (needs BCCH_TOKEN)
- Check `os.environ.get("BCCH_TOKEN")`. If missing: print a friendly
  "BCCH_TOKEN not set — export it first" message and return to menu.
- If set: `BcchClient().get(Series.UF, "2024-01-01", "2024-03-31")`,
  print first 5 observations, total count, source.
- Wrap in try/except BcchError to show a graceful failure message.

### 0. Exit
- "¡Chao! — come back anytime." and quit.

## Behavior rules

- After each option, wait for Enter before showing the menu again
  (so output isn't lost).
- Invalid menu choice → friendly "Pick a number 0-6." and re-prompt.
- Every option that could hit the network (5, 6) should print a small
  note like "(needs internet)".
- Keep output compact — no giant dumps. Truncate long lists (e.g. show
  first 5 of N).
- Windows-friendly: pure ASCII in the box drawing (or unicode — but the
  user is on Windows PowerShell, so prefer plain `=`/`-` bars over
  box-drawing chars to avoid encoding issues).

## Files
- Create: `playground.py` at project root.
- Do NOT modify: econchile/, tests/, sample_response.json, .env.

## Verification
- `python playground.py` runs; menu shows; option 1-4 work with NO token
  and NO network; option 5 reaches the API safely; option 6 prompts for
  token. Test each option at least once via scripted input
  (echo "1\n2\nipc\n3\n4\n5\n0\n" | python playground.py).
