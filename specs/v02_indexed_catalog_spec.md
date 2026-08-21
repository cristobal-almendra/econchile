# v0.2 — Indexed series catalog expansion — Spec

## What this is

Expand the **indexed** (searchable-in-the-library) series catalog from
7 to **28 members** — every new code **live-verified against the BCCh
API** before inclusion (the "verify before build" rule). No guesses.

Terminology: the enum is the **indexed catalog** — series the library
knows about, searchable via `search()`, usable via `Series.X` or
`client.get("name")`. The full BCCh catalog (~30k series) stays
reachable via raw codes (already supported) and is documented, not
indexed.

## The verified list (28 members — 7 existing + 21 new)

All codes below returned real values from the live API (June 2026
unless noted). Full verification log: `scratch/verify_catalog.py` +
follow-up reverify runs.

### FX & money (7)
| Member | Code | Freq | Repr |
|---|---|---|---|
| UF | F073.UFF.PRE.Z.D | DAILY | LEVEL |
| USD | F073.TCO.PRE.Z.D | DAILY | LEVEL |
| EURO | F072.EUR.USD.N.O.D | DAILY | LEVEL | *(USD per EUR — docstring must say so!)* |
| TCM | F073.TCM.IND.199502.D | DAILY | INDEX |
| TCR | F073.TCR.IND.199101.M | MONTHLY | INDEX |
| UTM | F073.UTR.PRE.Z.M | MONTHLY | LEVEL |
| IVP | F073.IVP.PRE.Z.D | DAILY | LEVEL |

*(CRM dropped — dead code, 0 values in 5 years.)*

### Rates (2)
| Member | Code | Freq | Repr |
|---|---|---|---|
| TPM | F022.TPM.TIN.D001.NO.Z.D | DAILY | LEVEL |
| TASA_HIPOTECARIA | F022.VIV.TIP.MA03.UF.Z.M | MONTHLY | LEVEL |

### Prices (5)
| Member | Code | Freq | Repr |
|---|---|---|---|
| IPC_VAR | F074.IPC.VAR.Z.Z.C.M | MONTHLY | MOM | *(keep existing base — backwards-compat)* |
| IPC_ANUAL | G073.IPC.V12.2023.M | MONTHLY | YOY |
| IPC_INDEX | F074.IPC.IND.Z.2023.C.M | MONTHLY | INDEX |
| IPC_SAE | F074.IPCSAE.VAR.Z.2023.C.M | MONTHLY | MOM |
| IPP | F075.IPP.IND.P0551.2014.Z.M | MONTHLY | INDEX | *(BCCh stopped updating after 2023-08 — keep, note in docstring)* |

*(COBRE_IPM / COBRE_IPP dropped — dead codes.)*

### Activity (7)
| Member | Code | Freq | Repr |
|---|---|---|---|
| IMACEC | F032.IMC.IND.Z.Z.EP18.Z.Z.0.M | MONTHLY | INDEX |
| IMACEC_SA | F032.IMC.IND.Z.Z.EP18.Z.Z.1.M | MONTHLY | INDEX |
| IMACEC_NO_MINERO | F032.IMC.IND.Z.Z.EP18.N03.Z.0.M | MONTHLY | INDEX |
| PIB | F032.PIB.FLU.R.CLP.EP18.Z.Z.0.T | QUARTERLY | LEVEL |
| PIB_SA | F032.PIB.FLU.R.CLP.EP18.Z.Z.1.T | QUARTERLY | LEVEL |
| PIB_CORRIENTE | F032.PIB.FLU.N.CLP.EP18.Z.Z.0.T | QUARTERLY | LEVEL |
| PIB_NO_MINERO | F032.PIB.FLU.R.CLP.EP18.N03.Z.0.T | QUARTERLY | LEVEL |

### Labor (3)
| Member | Code | Freq | Repr |
|---|---|---|---|
| DESEMPLEO | F049.DES.TAS.INE9.10.M | MONTHLY | LEVEL |
| FUERZA_TRABAJO | F049.FTR.PMT.INE9.01.M | MONTHLY | LEVEL |
| OCUPADOS | F049.OCU.PMT.INE9.01.M | MONTHLY | LEVEL |

### Expectations (2)
| Member | Code | Freq | Repr |
|---|---|---|---|
| TPM_EXPECTED | F089.TPM.TAS.11.M | MONTHLY | LEVEL |
| IPC_EXPECTED | F089.IPC.V12.14.M | MONTHLY | YOY | *(11-month-ahead 12m inflation expectation)* |

### External (1)
| Member | Code | Freq | Repr |
|---|---|---|---|
| EXPORTACIONES_COBRE | F068.B1.FLU.A1.0.C.N.Z.Z.Z.Z.6.0.M | MONTHLY | LEVEL |

### Macro (1)
| Member | Code | Freq | Repr |
|---|---|---|---|
| PIB_PER_CAPITA | F012.PPCP.FLU.N.7.AME.CL.USD.FMI.Z.0.A | ANNUAL | LEVEL | *(PPP USD, FMI — verified 2023-25)* |

**Count: 28 (7 existing + 21 new).**

## Implementation

1. `econchile/series_map.py` — add 19 enum members (grouped, with the
   docstring noting EURO's USD/EUR convention and IPP's staleness) +
   19 `_META_MAP` entries (titles ES/EN, Frequency, Representation).
2. `econchile/__init__.py` — exports unchanged (Series already exported).
3. README — replace "Available series (v0.1)" table with "Indexed
   series (v0.2)" (26 rows, grouped) + a "Full BCCh catalog" subsection:
   raw codes work, link to `data/bcch_catalog.csv` (see below).
4. `data/bcch_catalog.csv` — generated from the user's xlsx
   (chapter, name, code), committed (check size; if > 1MB, use a GitHub
   release asset + link instead).
5. Walkthrough notebook — update the 7-series output + count.

## Tests (contract)

- Update `tests/test_series_map.py`: 7 → 26 (count, membership,
  `from_code` roundtrips for every member, no duplicate codes).
- Update `tests/test_release.py` if it asserts a series count.
- New: every member's code must be unique; `list_all()` returns 26.
- The live API is NOT called in tests (offline contract only — the
  codes were verified separately).

## Risks / notes

- **EURO units**: `F072.EUR.USD.N.O.D` = USD per 1 EUR (~0.86) — NOT
  CLP/EUR. Docstring + README must state this to avoid misuse.
- **IPP staleness**: last value 2023-08. Keep (official series) but
  document.
- Renaming `IPC_VAR`'s code from `F074.IPC.VAR.Z.Z.C.M` (old base)
  → `F074.IPC.VAR.Z.2023.C.M` (current base 2023): verify the old code
  still resolves before changing (backwards-compat). If it does, keep
  both aliases working via `from_code`.
- **sdist size**: catalog CSV must not bloat the wheel (check MANIFEST).

## Out of scope (v0.2)

- pandas/DataFrame helpers (still deferred — bcch-sdk differentiation)
- async
- full-catalog search endpoint (raw codes + CSV are enough)
- representation warnings on empty ranges (deferred)
