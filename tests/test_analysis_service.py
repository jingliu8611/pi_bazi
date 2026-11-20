"""Tests for src/pi_bazi/analysis_service.py

The LLM client is always injected via _client= so no real API calls are made.
"""

from unittest.mock import MagicMock

import pytest

from pi_bazi.analysis_service import run_analysis


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_mock_client(response: str = "这是八字分析结果。") -> MagicMock:
    mock = MagicMock()
    mock.generate.return_value = response
    return mock


VALID = dict(year="甲子", month="丙寅", day="戊午", hour="庚申", gender="男")


# ---------------------------------------------------------------------------
# run_analysis()
# ---------------------------------------------------------------------------


def test_run_analysis_returns_string():
    result = run_analysis(**VALID, _client=make_mock_client("分析完毕"))
    assert result == "分析完毕"


def test_run_analysis_calls_client_generate():
    mock_client = make_mock_client()
    run_analysis(**VALID, _client=mock_client)
    mock_client.generate.assert_called_once()


def test_run_analysis_invalid_pillar_raises():
    with pytest.raises(ValueError):
        run_analysis(year="甲丑", month="丙寅", day="戊午", hour="庚申", gender="男",
                     _client=make_mock_client())


def test_run_analysis_invalid_gender_raises():
    with pytest.raises(ValueError):
        run_analysis(**{**VALID, "gender": "unknown"}, _client=make_mock_client())


def test_run_analysis_female_gender():
    result = run_analysis(
        year="甲子", month="丙寅", day="戊午", hour="庚申", gender="女",
        _client=make_mock_client("女命分析"),
    )
    assert result == "女命分析"


def test_run_analysis_chinese_gender_aliases():
    for g in ("男", "female"):
        result = run_analysis(**{**VALID, "gender": g}, _client=make_mock_client("ok"))
        assert result == "ok"
