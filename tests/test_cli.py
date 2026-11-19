"""Tests for src/pi_bazi/cli.py

The LLM client is always injected via _client= so no real API calls are made.
main() is tested by passing an argv list directly, avoiding sys.argv patching.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pi_bazi.cli import main, run_analysis


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


# ---------------------------------------------------------------------------
# main() — non-interactive via --flags
# ---------------------------------------------------------------------------


def test_main_runs_with_all_flags(capsys):
    with patch("pi_bazi.cli.GeminiClient") as MockClient:
        MockClient.return_value = make_mock_client("分析结果来了")
        main([
            "--year", "甲子",
            "--month", "丙寅",
            "--day", "戊午",
            "--hour", "庚申",
            "--gender", "男",
        ])

    out = capsys.readouterr().out
    assert "分析结果来了" in out
    assert "命盘" in out


def test_main_prints_separator(capsys):
    with patch("pi_bazi.cli.GeminiClient") as MockClient:
        MockClient.return_value = make_mock_client("结果")
        main([
            "--year", "甲子", "--month", "丙寅",
            "--day", "戊午", "--hour", "庚申", "--gender", "女",
        ])

    out = capsys.readouterr().out
    assert "=" * 10 in out


def test_main_exits_on_invalid_pillar(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main([
            "--year", "甲丑",   # invalid combination
            "--month", "丙寅", "--day", "戊午",
            "--hour", "庚申", "--gender", "男",
        ])
    assert exc_info.value.code == 1
    assert "输入有误" in capsys.readouterr().err


def test_main_exits_on_invalid_gender(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main([
            "--year", "甲子", "--month", "丙寅",
            "--day", "戊午", "--hour", "庚申",
            "--gender", "unknown",
        ])
    assert exc_info.value.code == 1


def test_main_exits_on_llm_error(capsys):
    with patch("pi_bazi.cli.GeminiClient") as MockClient:
        MockClient.return_value.generate.side_effect = RuntimeError("API error")
        with pytest.raises(SystemExit) as exc_info:
            main([
                "--year", "甲子", "--month", "丙寅",
                "--day", "戊午", "--hour", "庚申", "--gender", "男",
            ])
    assert exc_info.value.code == 1
    assert "分析失败" in capsys.readouterr().err
