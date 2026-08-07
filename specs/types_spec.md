# types.py — Spec

## What it does

Defines the shared data structures that every module in econchile uses for
series metadata, observations, and value representation tagging.

## Enums

### `Frequency` (str, Enum)
Standard frequency codes matching BCCh API values:
- `DAILY`, `MONTHLY`, `QUARTERLY`, `ANNUAL`

### `Representation` (str, Enum)
Tags how a series value should be interpreted. This addresses the data gotcha
where the same variable name means different things in different sources
(e.g., IPC = MoM% in JSON but index level in CSV):

- `LEVEL` — absolute value (USD=950, PIB=51,629bn CLP)
- `INDEX` — index number with base year (IPC=103.5 base 2023)
- `MOM` — month-over-month % change
- `YOY` — year-over-year % change
- `UNKNOWN` — not yet tagged (default)

## Dataclasses

### `SeriesMeta` (frozen)
Static metadata about a BCCh series — what you'd get from `siete.buscar()`:

| Field | Type | Description |
|-------|------|-------------|
| `series_id` | `str` | BCCh series code (e.g. `F073.TCO.PRE.Z.D`) |
| `spanish_title` | `str` | Title in Spanish |
| `english_title` | `str` | Title in English |
| `frequency` | `Frequency` | Temporal frequency |
| `first_observation` | `str \| None` | First available date (YYYY-MM-DD) |
| `last_observation` | `str \| None` | Last available date (YYYY-MM-DD) |
| `representation` | `Representation` | How to interpret values (default UNKNOWN) |

Frozen = immutable after creation. Prevents accidental mutation in downstream code.

### `Observation` (frozen)
A single data point — replaces the loose `{"date": ..., "value": ...}` dict
that `parsers.py` currently returns:

| Field | Type | Description |
|-------|------|-------------|
| `date` | `str` | YYYY-MM-DD |
| `value` | `float \| None` | Numeric value or None if missing |

## Dependencies
- `dataclasses` (stdlib)
- `enum` (stdlib)
- No external deps, no econchile deps
