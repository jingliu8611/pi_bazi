"""Tests for src/pi_bazi/book.py"""

import pytest

from pi_bazi.book import DEFAULT_BOOK_PATH, BookSource, load_book


# ---------------------------------------------------------------------------
# Default book (Di Tian Sui)
# ---------------------------------------------------------------------------


def test_default_book_path_exists():
    assert DEFAULT_BOOK_PATH.exists(), f"Expected book file at {DEFAULT_BOOK_PATH}"


def test_load_book_returns_book_source():
    book = load_book()
    assert isinstance(book, BookSource)


def test_load_book_title():
    book = load_book()
    assert book.title == "滴天髓"


def test_load_book_text_non_empty():
    book = load_book()
    assert len(book.text.strip()) > 0


def test_load_book_line_count():
    book = load_book()
    # The file has over 1000 lines
    assert book.line_count > 1000


def test_load_book_char_count():
    book = load_book()
    # Expect at least 10,000 characters of classical Chinese text
    assert book.char_count > 10_000


def test_load_book_contains_key_sections():
    book = load_book()
    assert "通神论" in book.text
    assert "六亲论" in book.text


def test_load_book_contains_classical_text():
    # Spot-check a known verse from 天干 chapter
    book = load_book()
    assert "甲木参天" in book.text


def test_load_book_path_is_resolved():
    book = load_book()
    assert book.path.is_absolute()


def test_load_book_accepts_string_path():
    book = load_book(str(DEFAULT_BOOK_PATH))
    assert book.title == "滴天髓"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_load_book_file_not_found():
    with pytest.raises(FileNotFoundError, match="Book file not found"):
        load_book("/nonexistent/path/book.txt")


def test_load_book_empty_file(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("   \n  \n", encoding="utf-8")
    with pytest.raises(ValueError, match="Book file is empty"):
        load_book(empty_file)
