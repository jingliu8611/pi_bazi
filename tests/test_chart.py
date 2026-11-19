"""Tests for src/pi_bazi/chart.py"""

import pytest

from pi_bazi.chart import (
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    VALID_PILLARS,
    BaziChart,
    Pillar,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_heavenly_stems_count():
    assert len(HEAVENLY_STEMS) == 10


def test_earthly_branches_count():
    assert len(EARTHLY_BRANCHES) == 12


def test_valid_pillars_count():
    # The 60 Jiazi cycle always has exactly 60 combinations
    assert len(VALID_PILLARS) == 60


# ---------------------------------------------------------------------------
# Pillar — valid construction
# ---------------------------------------------------------------------------


def test_pillar_valid():
    p = Pillar(stem="甲", branch="子")
    assert p.stem == "甲"
    assert p.branch == "子"


def test_pillar_from_str_valid():
    p = Pillar.from_str("甲子")
    assert p.stem == "甲"
    assert p.branch == "子"


def test_pillar_str():
    assert str(Pillar.from_str("丙寅")) == "丙寅"


def test_pillar_frozen():
    p = Pillar.from_str("甲子")
    with pytest.raises(Exception):
        p.stem = "乙"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Pillar — invalid construction
# ---------------------------------------------------------------------------


def test_pillar_invalid_stem():
    with pytest.raises(ValueError, match="Invalid Heavenly Stem"):
        Pillar(stem="X", branch="子")


def test_pillar_invalid_branch():
    with pytest.raises(ValueError, match="Invalid Earthly Branch"):
        Pillar(stem="甲", branch="X")


def test_pillar_invalid_parity_combination():
    # 甲 is index 0 (even), 丑 is index 1 (odd) — invalid pairing
    with pytest.raises(ValueError, match="Invalid pillar combination"):
        Pillar(stem="甲", branch="丑")


def test_pillar_from_str_wrong_length():
    with pytest.raises(ValueError, match="exactly 2 characters"):
        Pillar.from_str("甲")


def test_pillar_from_str_too_long():
    with pytest.raises(ValueError, match="exactly 2 characters"):
        Pillar.from_str("甲子子")


# ---------------------------------------------------------------------------
# BaziChart — valid construction
# ---------------------------------------------------------------------------


def test_bazi_chart_valid():
    chart = BaziChart(
        year=Pillar.from_str("甲子"),
        month=Pillar.from_str("丙寅"),
        day=Pillar.from_str("戊午"),
        hour=Pillar.from_str("庚申"),
        gender="male",
    )
    assert chart.gender == "male"
    assert str(chart.year) == "甲子"


def test_bazi_chart_from_strings_male():
    chart = BaziChart.from_strings("甲子", "丙寅", "戊午", "庚申", "male")
    assert chart.gender == "male"


def test_bazi_chart_from_strings_female():
    chart = BaziChart.from_strings("甲子", "丙寅", "戊午", "庚申", "female")
    assert chart.gender == "female"


def test_bazi_chart_from_strings_gender_chinese_male():
    chart = BaziChart.from_strings("甲子", "丙寅", "戊午", "庚申", "男")
    assert chart.gender == "male"


def test_bazi_chart_from_strings_gender_chinese_female():
    chart = BaziChart.from_strings("甲子", "丙寅", "戊午", "庚申", "女")
    assert chart.gender == "female"


def test_bazi_chart_str():
    chart = BaziChart.from_strings("甲子", "丙寅", "戊午", "庚申", "男")
    output = str(chart)
    assert "甲子" in output
    assert "丙寅" in output
    assert "戊午" in output
    assert "庚申" in output
    assert "男" in output


# ---------------------------------------------------------------------------
# BaziChart — invalid construction
# ---------------------------------------------------------------------------


def test_bazi_chart_invalid_gender_string():
    with pytest.raises(ValueError, match="Invalid gender"):
        BaziChart.from_strings("甲子", "丙寅", "戊午", "庚申", "unknown")


def test_bazi_chart_invalid_gender_direct():
    with pytest.raises(ValueError, match="Invalid gender"):
        BaziChart(
            year=Pillar.from_str("甲子"),
            month=Pillar.from_str("丙寅"),
            day=Pillar.from_str("戊午"),
            hour=Pillar.from_str("庚申"),
            gender="other",
        )


def test_bazi_chart_invalid_pillar_propagates():
    with pytest.raises(ValueError):
        BaziChart.from_strings("甲丑", "丙寅", "戊午", "庚申", "male")
