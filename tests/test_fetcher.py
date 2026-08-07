"""
Tests for econchile.fetcher — sync HTTP client for the BCCh REST API.

NEVER hits the real API: every test monkeypatches ``requests.get`` with
a scripted fake (the ``fake_get`` fixture).  Both response encodings are
covered — plain UTF-8 and UTF-16 with BOM — so the encoding-detection
logic is exercised end to end.  Every test passes an explicit token (or
monkeypatches ``BCCH_TOKEN``), so the suite runs with or without the env
var set.

Run with:
    pytest tests/test_fetcher.py -v
"""

import json
from datetime import datetime

import pytest
import requests

from econchile.fetcher import Fetcher
from econchile.series_map import Series
from econchile.types import BcchApiError, Observation, SeriesResult

DEFAULT_SERIES = "F073.TCO.PRE.Z.D"


def make_response(codigo=0, descripcion="Success", obs=None, encoding="utf-8"):
    """Helper to build a fake API response body.

    obs: list of {"indexDateString", "value", "statusCode"} dicts.
    encoding: "utf-8" or "utf-16" — controls whether a BOM is added.
    Returns bytes ready for requests.Response._content.
    """
    payload = {
        "Codigo": codigo,
        "Descripcion": descripcion,
        "Series": {
            "seriesId": DEFAULT_SERIES,
            "descripEsp": "Tipo de cambio nominal (dólar observado $CLP/USD)",
            "descripIng": "Nominal exchange rate (Observed dollar $CLP/USD)",
            "Obs": obs
            if obs is not None
            else [
                {"indexDateString": "02-01-2024", "value": "897.68", "statusCode": "OK"},
                {"indexDateString": "03-01-2024", "value": "901.13", "statusCode": "OK"},
            ],
        },
        "SeriesInfos": [],
    }
    text = json.dumps(payload)
    if encoding == "utf-16":
        # utf-16-le has NO BOM, so prepend it explicitly: FF FE (the
        # exact signature the fetcher's decoder looks for).
        return b"\xff\xfe" + text.encode("utf-16-le")
    return text.encode("utf-8")


@pytest.fixture
def fake_get(monkeypatch):
    """Monkeypatch requests.get to return a canned response.

    Set fake_get.response_body = <bytes> before calling.
    Records the URL for assertions.
    """

    def fake(url, **kwargs):
        fake.urls.append(url)
        resp = requests.Response()
        resp.status_code = 200
        resp._content = fake.response_body
        return resp

    fake.urls = []
    fake.response_body = make_response()
    monkeypatch.setattr("requests.get", fake)
    return fake


@pytest.fixture
def sample_series():
    """Series.USD — typical v0.1 series."""
    return Series.USD


# ─── URL construction and parameter mapping ────────────────────────────


class TestFetchURL:
    """URL construction and parameter mapping."""

    def test_uses_firstdate_lastdate_params(self, fake_get):
        """URL contains firstDate/lastDate, NOT desde/hasta."""
        Fetcher(token="test-token-123").fetch(Series.USD, "2024-01-01", "2024-01-31")
        url = fake_get.urls[0]
        assert "firstDate=2024-01-01" in url
        assert "lastDate=2024-01-31" in url
        assert "desde=" not in url
        assert "hasta=" not in url

    def test_contains_token(self, fake_get):
        """URL contains the token parameter."""
        Fetcher(token="test-token-123").fetch(Series.USD, "2024-01-01", "2024-01-31")
        assert "token=test-token-123" in fake_get.urls[0]

    def test_contains_timeseries_code(self, fake_get):
        """URL contains timeseries=F073.TCO.PRE.Z.D."""
        Fetcher(token="test-token-123").fetch(Series.USD, "2024-01-01", "2024-01-31")
        assert "timeseries=F073.TCO.PRE.Z.D" in fake_get.urls[0]


# ─── Response encoding detection ───────────────────────────────────────


class TestFetchEncoding:
    """Response encoding detection."""

    def test_utf8_response_parsed(self, fake_get):
        """Plain UTF-8 response body is parsed correctly."""
        fake_get.response_body = make_response(encoding="utf-8")
        result = Fetcher(token="test-token-123").fetch(
            Series.USD, "2024-01-01", "2024-01-31"
        )
        assert [o.date for o in result.observations] == ["2024-01-02", "2024-01-03"]
        assert [o.value for o in result.observations] == [897.68, 901.13]

    def test_utf16_bom_response_parsed(self, fake_get):
        """UTF-16 BOM response body is parsed correctly."""
        fake_get.response_body = make_response(encoding="utf-16")
        result = Fetcher(token="test-token-123").fetch(
            Series.USD, "2024-01-01", "2024-01-31"
        )
        assert [o.date for o in result.observations] == ["2024-01-02", "2024-01-03"]
        assert [o.value for o in result.observations] == [897.68, 901.13]


# ─── SeriesResult construction ─────────────────────────────────────────


class TestFetchResult:
    """Fetch returns a proper SeriesResult."""

    def test_returns_series_result(self, fake_get):
        """fetch() returns a SeriesResult instance."""
        result = Fetcher(token="test-token-123").fetch(
            Series.USD, "2024-01-01", "2024-01-31"
        )
        assert isinstance(result, SeriesResult)

    def test_series_member_preserved(self, fake_get, sample_series):
        """result.series is the Series enum member passed in."""
        result = Fetcher(token="test-token-123").fetch(
            sample_series, "2024-01-01", "2024-01-31"
        )
        assert result.series is sample_series

    def test_observations_are_observation_objects(self, fake_get):
        """result.observations contains Observation instances."""
        result = Fetcher(token="test-token-123").fetch(
            Series.USD, "2024-01-01", "2024-01-31"
        )
        assert result.observations
        assert all(isinstance(o, Observation) for o in result.observations)
        first = result.observations[0]
        assert first.date == "2024-01-02"
        assert first.value == 897.68

    def test_source_is_api(self, fake_get):
        """result.source == 'api'."""
        result = Fetcher(token="test-token-123").fetch(
            Series.USD, "2024-01-01", "2024-01-31"
        )
        assert result.source == "api"

    def test_fetched_at_is_datetime(self, fake_get):
        """result.fetched_at is a datetime."""
        result = Fetcher(token="test-token-123").fetch(
            Series.USD, "2024-01-01", "2024-01-31"
        )
        assert isinstance(result.fetched_at, datetime)

    def test_metadata_present(self, fake_get):
        """result.metadata is a non-empty dict."""
        result = Fetcher(token="test-token-123").fetch(
            Series.USD, "2024-01-01", "2024-01-31"
        )
        assert isinstance(result.metadata, dict)
        assert result.metadata
        assert result.metadata["series_id"] == DEFAULT_SERIES
        assert result.metadata["descripEsp"]
        assert result.metadata["descripIng"]

    def test_accepts_raw_code_string(self, fake_get):
        """fetch('F073.TCO.PRE.Z.D', ...) works without a Series enum."""
        result = Fetcher(token="test-token-123").fetch(
            DEFAULT_SERIES, "2024-01-01", "2024-01-31"
        )
        assert result.series == Series.USD
        assert len(result.observations) == 2


# ─── Input validation ──────────────────────────────────────────────────


class TestFetchValidation:
    """Input validation."""

    def test_bad_desde_raises_value_error(self, fake_get):
        """desde='not-a-date' raises ValueError."""
        with pytest.raises(ValueError):
            Fetcher(token="test-token-123").fetch(
                Series.USD, "not-a-date", "2024-01-31"
            )
        # Validation must fail BEFORE any network call.
        assert fake_get.urls == []

    def test_bad_hasta_raises_value_error(self, fake_get):
        """hasta='garbage' raises ValueError."""
        with pytest.raises(ValueError):
            Fetcher(token="test-token-123").fetch(
                Series.USD, "2024-01-01", "garbage"
            )
        assert fake_get.urls == []


# ─── Error handling ────────────────────────────────────────────────────


class TestFetchErrors:
    """Error handling."""

    def test_api_error_codigo_raises_bcch_api_error(self, fake_get):
        """Codigo != 0 in response → BcchApiError."""
        fake_get.response_body = make_response(codigo=-1, descripcion="Serie no encontrada")
        with pytest.raises(BcchApiError) as excinfo:
            Fetcher(token="test-token-123").fetch(
                Series.USD, "2024-01-01", "2024-01-31"
            )
        # The API's description is preserved in the wrapped error.
        assert "Serie no encontrada" in str(excinfo.value)

    def test_network_error_wrapped(self, monkeypatch):
        """requests.get raising ConnectionError → BcchApiError."""
        def boom(url, **kwargs):
            raise requests.ConnectionError("connection refused")

        monkeypatch.setattr("requests.get", boom)
        with pytest.raises(BcchApiError):
            Fetcher(token="test-token-123").fetch(
                Series.USD, "2024-01-01", "2024-01-31"
            )

    def test_http_500_raises_bcch_api_error(self, monkeypatch):
        """Non-200 HTTP status → BcchApiError."""
        def five_hundred(url, **kwargs):
            resp = requests.Response()
            resp.status_code = 500
            resp._content = b""
            return resp

        monkeypatch.setattr("requests.get", five_hundred)
        with pytest.raises(BcchApiError):
            Fetcher(token="test-token-123").fetch(
                Series.USD, "2024-01-01", "2024-01-31"
            )


# ─── Token resolution ──────────────────────────────────────────────────


class TestTokenSource:
    """Token resolution."""

    def test_default_reads_env_var(self, monkeypatch):
        """No token arg → reads BCCH_TOKEN from env."""
        monkeypatch.setenv("BCCH_TOKEN", "env-token-999")
        urls = []

        def fake(url, **kwargs):
            urls.append(url)
            resp = requests.Response()
            resp.status_code = 200
            resp._content = make_response()
            return resp

        monkeypatch.setattr("requests.get", fake)
        Fetcher().fetch(Series.USD, "2024-01-01", "2024-01-31")
        assert "token=env-token-999" in urls[0]

    def test_explicit_token_wins(self, monkeypatch):
        """Explicit token arg overrides env var."""
        monkeypatch.setenv("BCCH_TOKEN", "env-token-999")
        urls = []

        def fake(url, **kwargs):
            urls.append(url)
            resp = requests.Response()
            resp.status_code = 200
            resp._content = make_response()
            return resp

        monkeypatch.setattr("requests.get", fake)
        Fetcher(token="explicit-token-123").fetch(
            Series.USD, "2024-01-01", "2024-01-31"
        )
        assert "token=explicit-token-123" in urls[0]
        assert "env-token-999" not in urls[0]
