# parsers.py — Spec & Test Contract

## What it does

Parses raw BCCh REST API JSON responses (UTF-16 encoded) into clean, typed Python
dicts that the rest of econchile can consume. Uses `converters.safe_float` and
`converters.safe_date` under the hood for value normalization.

## API response format (confirmed from real data)

```json
{
  "Codigo": 0,                    // 0 = success, non-zero = error
  "Descripcion": "Success",      // human-readable status
  "Series": {
    "seriesId": "F073.TCO.PRE.Z.D",
    "descripEsp": "...",
    "descripIng": "...",
    "Obs": [
      {
        "indexDateString": "09-08-1982",  // DD-MM-YYYY
        "value": "55.65",                  // string, "NaN" when ND
        "statusCode": "OK"                 // "OK" = data, "ND" = no data
      }
    ]
  },
  "SeriesInfos": []               // metadata, empty in single-series calls
}
```

## Public functions

### 1. `parse_response(raw_text: str) -> dict`
- Takes raw HTTP response body (UTF-16 string with BOM)
- Returns cleaned dict: `{"series_id": str, "observations": list[dict], "metadata": dict}`
- Raises `ParsingError` if Codigo != 0

### 2. `parse_observations(obs_list: list[dict]) -> list[dict]`
- Takes the raw `Obs` array
- Returns list of `{"date": "YYYY-MM-DD", "value": float | None}`
- Checks `statusCode` before parsing value
- Uses `safe_date()` and `safe_float()` from converters

## Encoding handling
- BCCh API returns UTF-16 with BOM (bytes: FF FE)
- Use `raw_text.encode('utf-16')` or detect from BOM
- The library's entry point (`fetcher.py`/`client.py`) handles HTTP; `parse_response`
  receives already-decoded string. Test with both raw bytes and decoded string.

## Error handling
- Define `ParsingError(Exception)` for API-level errors (Codigo != 0)
- Define `SeriesNotFoundError(ParsingError)` if Codigo indicates missing series
- Use existing `safe_float` / `safe_date` — they never crash, return None

## Dependencies
- `econchile.converters`: `safe_float`, `safe_date`
- `json` (stdlib)
- `datetime` (stdlib, for date format conversion)