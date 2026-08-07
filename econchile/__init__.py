"""econchile — Chilean macroeconomic data, made simple."""

__version__ = "0.1.0"

from econchile.client import BcchClient
from econchile.series_map import Series
from econchile.types import SeriesMeta, SeriesResult

__all__ = ["BcchClient", "Series", "SeriesMeta", "SeriesResult", "__version__"]
