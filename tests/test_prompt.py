"""Tests for src/pi_bazi/prompt.py"""

import pytest

from pi_bazi.book import BookSource, load_book
from pi_bazi.chart import BaziChart, Pillar
from pi_bazi.prompt import PromptParts, build_prompt


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_chart() -> BaziChart:
    return BaziChart.from_strings("甲子", "丙寅", "戊午", "庚申", "male")


@pytest.fixture
def sample_chart_female() -> BaziChart:
    return BaziChart.from_strings("甲子", "丙寅", "戊午", "庚申", "female")


@pytest.fixture
def real_book() -> BookSource:
    return load_book()


@pytest.fixture
def stub_book() -> BookSource:
    """A lightweight in-memory stub book to avoid reading the file in every test."""
    return BookSource(
        title="测试典籍",
        path=__import__("pathlib").Path("/fake/path.txt"),
        text="这是测试用的典籍内容。\n甲木参天，脱胎要火。",
    )


# ---------------------------------------------------------------------------
# PromptParts structure
# ---------------------------------------------------------------------------


def test_build_prompt_returns_prompt_parts(sample_chart, stub_book):
    result = build_prompt(sample_chart, stub_book)
    assert isinstance(result, PromptParts)


def test_prompt_parts_are_strings(sample_chart, stub_book):
    result = build_prompt(sample_chart, stub_book)
    assert isinstance(result.system_instruction, str)
    assert isinstance(result.user_message, str)


def test_prompt_parts_are_non_empty(sample_chart, stub_book):
    result = build_prompt(sample_chart, stub_book)
    assert len(result.system_instruction.strip()) > 0
    assert len(result.user_message.strip()) > 0


def test_prompt_parts_frozen(sample_chart, stub_book):
    result = build_prompt(sample_chart, stub_book)
    with pytest.raises(Exception):
        result.system_instruction = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# System instruction content
# ---------------------------------------------------------------------------


def test_system_instruction_contains_book_title(sample_chart, stub_book):
    result = build_prompt(sample_chart, stub_book)
    assert stub_book.title in result.system_instruction


def test_system_instruction_contains_book_text(sample_chart, stub_book):
    result = build_prompt(sample_chart, stub_book)
    assert stub_book.text in result.system_instruction


def test_system_instruction_contains_citation_rule(sample_chart, stub_book):
    result = build_prompt(sample_chart, stub_book)
    assert "引用原文" in result.system_instruction


def test_system_instruction_contains_no_fabrication_rule(sample_chart, stub_book):
    result = build_prompt(sample_chart, stub_book)
    assert "捏造" in result.system_instruction


def test_system_instruction_contains_chinese_output_rule(sample_chart, stub_book):
    result = build_prompt(sample_chart, stub_book)
    assert "中文" in result.system_instruction


# ---------------------------------------------------------------------------
# User message content
# ---------------------------------------------------------------------------


def test_user_message_contains_all_pillars(sample_chart, stub_book):
    result = build_prompt(sample_chart, stub_book)
    assert "甲子" in result.user_message
    assert "丙寅" in result.user_message
    assert "戊午" in result.user_message
    assert "庚申" in result.user_message


def test_user_message_contains_male_gender(sample_chart, stub_book):
    result = build_prompt(sample_chart, stub_book)
    assert "男" in result.user_message


def test_user_message_contains_female_gender(sample_chart_female, stub_book):
    result = build_prompt(sample_chart_female, stub_book)
    assert "女" in result.user_message


def test_user_message_contains_book_title(sample_chart, stub_book):
    result = build_prompt(sample_chart, stub_book)
    assert stub_book.title in result.user_message


def test_user_message_contains_pillar_labels(sample_chart, stub_book):
    result = build_prompt(sample_chart, stub_book)
    assert "年柱" in result.user_message
    assert "月柱" in result.user_message
    assert "日柱" in result.user_message
    assert "时柱" in result.user_message


# ---------------------------------------------------------------------------
# Integration: real book
# ---------------------------------------------------------------------------


def test_build_prompt_with_real_book(sample_chart, real_book):
    result = build_prompt(sample_chart, real_book)
    assert "滴天髓" in result.system_instruction
    assert "甲木参天" in result.system_instruction
    assert "甲子" in result.user_message
