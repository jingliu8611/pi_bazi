"""Tests for src/pi_bazi/web.py

The analysis service is always mocked so no real API or book-loading calls
are made. Flask's built-in test client is used throughout.
"""

from unittest.mock import patch

import pytest

from pi_bazi.llm import LLMRateLimitError, LLMUnavailableError
from pi_bazi.web import _render_result, app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


VALID_FORM = dict(year="甲子", month="丙寅", day="戊午", hour="庚申", gender="男")
MOCK_RESULT = "## 分析结果\n\n这是**八字**分析结果。\n\n> 据《滴天髓》"


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


def test_index_returns_200(client):
    assert client.get("/").status_code == 200


def test_index_contains_form(client):
    text = client.get("/").data.decode()
    assert "<form" in text


def test_index_contains_all_field_names(client):
    text = client.get("/").data.decode()
    for name in ("year", "month", "day", "hour", "gender"):
        assert f'name="{name}"' in text


def test_index_has_no_result_or_error_on_first_load(client):
    text = client.get("/").data.decode()
    # CSS defines these classes, but the divs themselves must not be rendered
    assert '<div class="result-box"' not in text
    assert '<div class="error-box"'  not in text


# ---------------------------------------------------------------------------
# POST /analyze — success
# ---------------------------------------------------------------------------


def test_analyze_valid_returns_200(client):
    with patch("pi_bazi.web.run_analysis", return_value=MOCK_RESULT):
        resp = client.post("/analyze", data=VALID_FORM)
    assert resp.status_code == 200


def test_analyze_result_section_present(client):
    with patch("pi_bazi.web.run_analysis", return_value=MOCK_RESULT):
        resp = client.post("/analyze", data=VALID_FORM)
    assert "result-box" in resp.data.decode()


def test_analyze_markdown_rendered_to_html(client):
    """**bold** in LLM output must arrive as <strong>, not raw asterisks."""
    with patch("pi_bazi.web.run_analysis", return_value=MOCK_RESULT):
        resp = client.post("/analyze", data=VALID_FORM)
    text = resp.data.decode()
    assert "<strong>" in text
    assert "**八字**" not in text


def test_analyze_no_raw_script_in_output(client):
    """Ensure nh3 strips injected script tags from LLM output."""
    malicious = "<script>alert('xss')</script>正常文字"
    with patch("pi_bazi.web.run_analysis", return_value=malicious):
        resp = client.post("/analyze", data=VALID_FORM)
    text = resp.data.decode()
    # The page always has a <script> for the loading indicator, so we check
    # that the injected payload specifically was stripped.
    assert "alert('xss')" not in text
    assert "正常文字" in text


def test_analyze_form_values_repopulated_on_success(client):
    with patch("pi_bazi.web.run_analysis", return_value=MOCK_RESULT):
        resp = client.post("/analyze", data=VALID_FORM)
    text = resp.data.decode()
    assert 'value="甲子"' in text
    assert 'value="丙寅"' in text


# ---------------------------------------------------------------------------
# POST /analyze — error responses
# ---------------------------------------------------------------------------


def test_analyze_invalid_input_returns_400(client):
    with patch("pi_bazi.web.run_analysis", side_effect=ValueError("bad pillar")):
        resp = client.post("/analyze", data=VALID_FORM)
    assert resp.status_code == 400


def test_analyze_rate_limit_returns_429(client):
    with patch("pi_bazi.web.run_analysis", side_effect=LLMRateLimitError("quota")):
        resp = client.post("/analyze", data=VALID_FORM)
    assert resp.status_code == 429


def test_analyze_unavailable_returns_503(client):
    with patch("pi_bazi.web.run_analysis", side_effect=LLMUnavailableError("down")):
        resp = client.post("/analyze", data=VALID_FORM)
    assert resp.status_code == 503


def test_analyze_unexpected_error_returns_500(client):
    with patch("pi_bazi.web.run_analysis", side_effect=RuntimeError("boom")):
        resp = client.post("/analyze", data=VALID_FORM)
    assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /analyze — error messages shown in page
# ---------------------------------------------------------------------------


def test_error_message_shown_on_400(client):
    with patch("pi_bazi.web.run_analysis", side_effect=ValueError("bad pillar")):
        resp = client.post("/analyze", data=VALID_FORM)
    assert "bad pillar" in resp.data.decode()


def test_error_message_shown_on_429(client):
    with patch("pi_bazi.web.run_analysis", side_effect=LLMRateLimitError("quota")):
        resp = client.post("/analyze", data=VALID_FORM)
    assert "频率超限" in resp.data.decode()


def test_error_message_shown_on_503(client):
    with patch("pi_bazi.web.run_analysis", side_effect=LLMUnavailableError("down")):
        resp = client.post("/analyze", data=VALID_FORM)
    assert "不可用" in resp.data.decode()


# ---------------------------------------------------------------------------
# POST /analyze — form value persistence after error
# ---------------------------------------------------------------------------


def test_form_values_persist_after_error(client):
    bad_form = {**VALID_FORM, "year": "甲丑"}
    with patch("pi_bazi.web.run_analysis", side_effect=ValueError("bad")):
        resp = client.post("/analyze", data=bad_form)
    text = resp.data.decode()
    assert "甲丑" in text   # repopulated year
    assert "丙寅" in text   # repopulated month


def test_gender_persists_as_female_after_error(client):
    import re
    female_form = {**VALID_FORM, "gender": "女"}
    with patch("pi_bazi.web.run_analysis", side_effect=ValueError("bad")):
        resp = client.post("/analyze", data=female_form)
    # Normalise whitespace so Jinja2 indentation doesn't affect the assertion.
    normalised = re.sub(r'\s+', ' ', resp.data.decode())
    assert 'value="女" checked' in normalised


# ---------------------------------------------------------------------------
# _render_result() unit tests
# ---------------------------------------------------------------------------


def test_render_result_converts_markdown_bold():
    html = _render_result("**粗体**")
    assert "<strong>粗体</strong>" in html


def test_render_result_converts_markdown_heading():
    html = _render_result("## 标题")
    assert "<h2>" in html


def test_render_result_strips_script_tags():
    html = _render_result("<script>alert(1)</script>文字")
    assert "<script>" not in html
    assert "文字" in html


def test_render_result_allows_blockquote():
    html = _render_result("> 引用原文")
    assert "<blockquote>" in html


def test_render_result_renders_table():
    md = "| 天干 | 五行 |\n|------|------|\n| 甲   | 木   |"
    html = _render_result(md)
    assert "<table>" in html
    assert "<th>" in html
