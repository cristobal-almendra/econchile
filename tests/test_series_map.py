"""
Tests for econchile.series_map — BCCh series enum catalog.

Run with:
    pytest tests/test_series_map.py -v

Validates all 7 v0.1 core series members, metadata correctness,
from_code lookup, and list_all.
"""

import pytest

from econchile.series_map import Series
from econchile.types import Frequency, Representation, SeriesMeta


# ═══════════════════════════════════════════════════════════════════════════
# Series enum tests
# ═══════════════════════════════════════════════════════════════════════════

class TestSeriesEnum:
    """Series enum members and their BCCh codes."""

    def test_seven_members(self):
        """Series has exactly 7 members (v0.1 core catalog)."""
        members = list(Series)
        assert len(members) == 7

    def test_uf_code(self):
        """Series.UF.value == 'F073.UFF.PRE.Z.D'"""
        assert Series.UF.value == "F073.UFF.PRE.Z.D"

    def test_usd_code(self):
        """Series.USD.value == 'F073.TCO.PRE.Z.D'"""
        assert Series.USD.value == "F073.TCO.PRE.Z.D"

    def test_tpm_code(self):
        """Series.TPM.value == 'F022.TPM.TIN.D001.NO.Z.D'"""
        assert Series.TPM.value == "F022.TPM.TIN.D001.NO.Z.D"

    def test_ipc_var_code(self):
        """Series.IPC_VAR.value == 'F074.IPC.VAR.Z.Z.C.M'"""
        assert Series.IPC_VAR.value == "F074.IPC.VAR.Z.Z.C.M"

    def test_ipc_index_code(self):
        """Series.IPC_INDEX.value == 'F074.IPC.IND.Z.2023.C.M'"""
        assert Series.IPC_INDEX.value == "F074.IPC.IND.Z.2023.C.M"

    def test_imacec_code(self):
        """Series.IMACEC.value == 'F032.IMC.IND.Z.Z.EP18.Z.Z.0.M'"""
        assert Series.IMACEC.value == "F032.IMC.IND.Z.Z.EP18.Z.Z.0.M"

    def test_pib_code(self):
        """Series.PIB.value == 'F032.PIB.FLU.R.CLP.EP18.Z.Z.0.T'"""
        assert Series.PIB.value == "F032.PIB.FLU.R.CLP.EP18.Z.Z.0.T"

    def test_is_str_enum(self):
        """Series is a subclass of both str and Enum."""
        assert issubclass(Series, str)
        from enum import Enum
        assert issubclass(Series, Enum)


# ═══════════════════════════════════════════════════════════════════════════
# Meta tests
# ═══════════════════════════════════════════════════════════════════════════

class TestMeta:
    """Series.meta() returns correct SeriesMeta."""

    @pytest.mark.parametrize("member, freq", [
        ("UF", Frequency.DAILY),
        ("USD", Frequency.DAILY),
        ("TPM", Frequency.DAILY),
        ("IPC_VAR", Frequency.MONTHLY),
        ("IPC_INDEX", Frequency.MONTHLY),
        ("IMACEC", Frequency.MONTHLY),
        ("PIB", Frequency.QUARTERLY),
    ])
    def test_frequency(self, member, freq):
        """Each series reports correct frequency."""
        s = getattr(Series, member)
        assert s.meta().frequency == freq

    @pytest.mark.parametrize("member, rep", [
        ("UF", Representation.LEVEL),
        ("USD", Representation.LEVEL),
        ("TPM", Representation.LEVEL),
        ("IPC_VAR", Representation.MOM),
        ("IPC_INDEX", Representation.INDEX),
        ("IMACEC", Representation.INDEX),
        ("PIB", Representation.LEVEL),
    ])
    def test_representation(self, member, rep):
        """Each series reports correct representation tag."""
        s = getattr(Series, member)
        assert s.meta().representation == rep

    def test_meta_returns_series_meta(self):
        """meta() returns a SeriesMeta instance."""
        assert isinstance(Series.USD.meta(), SeriesMeta)

    def test_meta_has_spanish_title(self):
        """SeriesMeta includes a non-empty spanish_title."""
        meta = Series.UF.meta()
        assert isinstance(meta.spanish_title, str)
        assert len(meta.spanish_title) > 0


# ═══════════════════════════════════════════════════════════════════════════
# from_code tests
# ═══════════════════════════════════════════════════════════════════════════

class TestFromCode:
    """Series.from_code() lookup."""

    def test_valid_code_returns_member(self):
        """from_code with known code returns the Series member."""
        assert Series.from_code("F073.UFF.PRE.Z.D") is Series.UF
        assert Series.from_code("F073.TCO.PRE.Z.D") is Series.USD
        assert Series.from_code("F074.IPC.IND.Z.2023.C.M") is Series.IPC_INDEX

    def test_unknown_code_raises_key_error(self):
        """from_code with unknown code raises KeyError."""
        with pytest.raises(KeyError):
            Series.from_code("F000.XXX.XXX.Z.Z.Z")


# ═══════════════════════════════════════════════════════════════════════════
# list_all tests
# ═══════════════════════════════════════════════════════════════════════════

class TestListAll:
    """Series.list_all() returns all members."""

    def test_returns_seven_items(self):
        """list_all() returns exactly 7 Series members."""
        result = Series.list_all()
        assert len(result) == 7

    def test_all_members_are_series_instances(self):
        """Every item in list_all() is a Series."""
        result = Series.list_all()
        for item in result:
            assert isinstance(item, Series)