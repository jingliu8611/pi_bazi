"""Tests for src/pi_bazi/cli.py

main() is tested by passing an argv list directly, avoiding sys.argv patching.
The LLM client is patched at pi_bazi.analysis_service.GeminiClient so no real
API calls are made.
"""

from unittest.mock import MagicMock, patch

import pytest

from pi_bazi.cli import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_mock_client(response: str = "这是八字分析结果。") -> MagicMock:
    mock = MagicMock()
    mock.generate.return_value = response
    return mock


# ---------------------------------------------------------------------------
# main() — non-interactive via --flags
# ---------------------------------------------------------------------------


def test_main_runs_with_all_flags(capsys):
    with patch("pi_bazi.analysis_service.GeminiClient") as MockClient:
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
    with patch("pi_bazi.analysis_service.GeminiClient") as MockClient:
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
    with patch("pi_bazi.analysis_service.GeminiClient") as MockClient:
        MockClient.return_value.generate.side_effect = RuntimeError("API error")
        with pytest.raises(SystemExit) as exc_info:
            main([
                "--year", "甲子", "--month", "丙寅",
                "--day", "戊午", "--hour", "庚申", "--gender", "男",
            ])
    assert exc_info.value.code == 1
    assert "分析失败" in capsys.readouterr().err
