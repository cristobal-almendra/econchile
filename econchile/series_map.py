"""
BCCh macroeconomic series — v0.1 core catalog.

Each member maps a human-readable name to a BCCh series code.
Metadata (frequency, representation) is attached via :meth:`meta`.

Usage::

    >>> Series.USD
    <Series.USD: 'F073.TCO.PRE.Z.D'>
    >>> Series.USD.value
    'F073.TCO.PRE.Z.D'
    >>> Series.USD.meta()
    SeriesMeta(series_id='F073.TCO.PRE.Z.D', ...)
"""

from enum import Enum

from econchile.types import Frequency, Representation, SeriesMeta


class Series(str, Enum):
    """BCCh macroeconomic series — v0.1 core catalog."""

    # ── Core macro ──
    UF = "F073.UFF.PRE.Z.D"
    USD = "F073.TCO.PRE.Z.D"
    TPM = "F022.TPM.TIN.D001.NO.Z.D"

    # ── Inflation ──
    IPC_VAR = "F074.IPC.VAR.Z.Z.C.M"
    IPC_INDEX = "F074.IPC.IND.Z.2023.C.M"

    # ── Growth ──
    IMACEC = "F032.IMC.IND.Z.Z.EP18.Z.Z.0.M"
    PIB = "F032.PIB.FLU.R.CLP.EP18.Z.Z.0.T"

    def meta(self) -> SeriesMeta:
        """Return static metadata for this series."""
        return _META_MAP[self]

    @classmethod
    def from_code(cls, code: str) -> "Series":
        """Look up a Series member by BCCh code.

        Raises KeyError if the code is not in v0.1 catalog.
        """
        for member in cls:
            if member.value == code:
                return member
        raise KeyError(code)

    @classmethod
    def list_all(cls) -> list["Series"]:
        """Return all v0.1 series as a list."""
        return list(cls)


# ── Internal metadata lookup table ──────────────────────────────────────────

_META_MAP: dict[Series, SeriesMeta] = {
    Series.UF: SeriesMeta(
        series_id=Series.UF.value,
        spanish_title="Unidad de Fomento (UF)",
        english_title="Unidad de Fomento (UF)",
        frequency=Frequency.DAILY,
        first_observation=None,
        last_observation=None,
        representation=Representation.LEVEL,
    ),
    Series.USD: SeriesMeta(
        series_id=Series.USD.value,
        spanish_title="Tipo de cambio nominal (dólar observado $CLP/USD)",
        english_title="Nominal exchange rate (Observed dollar $CLP/USD)",
        frequency=Frequency.DAILY,
        first_observation=None,
        last_observation=None,
        representation=Representation.LEVEL,
    ),
    Series.TPM: SeriesMeta(
        series_id=Series.TPM.value,
        spanish_title="Tasa de política monetaria (TPM)",
        english_title="Monetary policy rate (MPR)",
        frequency=Frequency.DAILY,
        first_observation=None,
        last_observation=None,
        representation=Representation.LEVEL,
    ),
    Series.IPC_VAR: SeriesMeta(
        series_id=Series.IPC_VAR.value,
        spanish_title="IPC variación mensual",
        english_title="CPI monthly change",
        frequency=Frequency.MONTHLY,
        first_observation=None,
        last_observation=None,
        representation=Representation.MOM,
    ),
    Series.IPC_INDEX: SeriesMeta(
        series_id=Series.IPC_INDEX.value,
        spanish_title="IPC índice general base 2023=100",
        english_title="CPI general index base 2023=100",
        frequency=Frequency.MONTHLY,
        first_observation=None,
        last_observation=None,
        representation=Representation.INDEX,
    ),
    Series.IMACEC: SeriesMeta(
        series_id=Series.IMACEC.value,
        spanish_title="Imacec empalmado, serie original (índice 2018=100)",
        english_title="Imacec spliced, original series (index 2018=100)",
        frequency=Frequency.MONTHLY,
        first_observation=None,
        last_observation=None,
        representation=Representation.INDEX,
    ),
    Series.PIB: SeriesMeta(
        series_id=Series.PIB.value,
        spanish_title="PIB, volumen a precios del año anterior encadenado (base 2018)",
        english_title="GDP, volume at previous year prices chained (base 2018)",
        frequency=Frequency.QUARTERLY,
        first_observation=None,
        last_observation=None,
        representation=Representation.LEVEL,
    ),
}