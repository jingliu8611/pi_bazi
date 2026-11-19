"""Tests for src/pi_bazi/llm.py

Real API calls are never made here. The google.genai.Client is replaced
with a lightweight mock via the _inner injection point.
"""

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pi_bazi.llm import DEFAULT_MODEL, GeminiClient
from pi_bazi.prompt import PromptParts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_mock_inner(response_text: str | None = "分析结果") -> MagicMock:
    """Return a mock google.genai.Client whose generate_content returns a
    response with the given text."""
    mock_response = SimpleNamespace(text=response_text)
    mock_inner = MagicMock()
    mock_inner.models.generate_content.return_value = mock_response
    return mock_inner


def sample_prompt() -> PromptParts:
    return PromptParts(
        system_instruction="你是八字分析助手。书籍内容：...",
        user_message="年柱：甲子 月柱：丙寅 日柱：戊午 时柱：庚申 性别：男",
    )


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


def test_client_init_with_injected_inner():
    """Should initialise without an API key when a mock inner client is injected."""
    client = GeminiClient(_inner=make_mock_inner())
    assert client.model == DEFAULT_MODEL


def test_client_init_custom_model():
    client = GeminiClient(model="gemini-1.5-flash", _inner=make_mock_inner())
    assert client.model == "gemini-1.5-flash"


def test_client_init_explicit_api_key(monkeypatch):
    """Should accept an explicit api_key without reading the environment."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # Patch genai.Client to avoid a real network check at construction time
    with patch("pi_bazi.llm.genai.Client") as mock_genai_client:
        mock_genai_client.return_value = make_mock_inner()
        client = GeminiClient(api_key="test-key-123")
        mock_genai_client.assert_called_once_with(api_key="test-key-123")
    assert client.model == DEFAULT_MODEL


def test_client_init_reads_env_variable(monkeypatch):
    """Should read GEMINI_API_KEY from the environment when no key is passed."""
    monkeypatch.setenv("GEMINI_API_KEY", "env-key-abc")
    with patch("pi_bazi.llm.genai.Client") as mock_genai_client:
        mock_genai_client.return_value = make_mock_inner()
        GeminiClient()
        mock_genai_client.assert_called_once_with(api_key="env-key-abc")


def test_client_init_raises_without_key(monkeypatch):
    """Should raise ValueError when no key is available and no _inner is given."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # Also patch load_dotenv so it doesn't pick up the real .env file
    with patch("pi_bazi.llm.load_dotenv"):
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            GeminiClient()


# ---------------------------------------------------------------------------
# generate()
# ---------------------------------------------------------------------------


def test_generate_returns_response_text():
    mock_inner = make_mock_inner("这是八字分析结果。")
    client = GeminiClient(_inner=mock_inner)
    result = client.generate(sample_prompt())
    assert result == "这是八字分析结果。"


def test_generate_passes_user_message_as_contents():
    mock_inner = make_mock_inner()
    client = GeminiClient(_inner=mock_inner)
    prompt = sample_prompt()
    client.generate(prompt)

    call_kwargs = mock_inner.models.generate_content.call_args.kwargs
    assert call_kwargs["contents"] == prompt.user_message


def test_generate_passes_system_instruction_in_config():
    mock_inner = make_mock_inner()
    client = GeminiClient(_inner=mock_inner)
    prompt = sample_prompt()
    client.generate(prompt)

    call_kwargs = mock_inner.models.generate_content.call_args.kwargs
    assert call_kwargs["config"].system_instruction == prompt.system_instruction


def test_generate_passes_correct_model():
    mock_inner = make_mock_inner()
    client = GeminiClient(model="gemini-2.0-flash", _inner=mock_inner)
    client.generate(sample_prompt())

    call_kwargs = mock_inner.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-2.0-flash"


def test_generate_raises_on_empty_response():
    mock_inner = make_mock_inner(response_text=None)
    client = GeminiClient(_inner=mock_inner)
    with pytest.raises(RuntimeError, match="empty response"):
        client.generate(sample_prompt())


def test_generate_raises_on_empty_string_response():
    mock_inner = make_mock_inner(response_text="")
    client = GeminiClient(_inner=mock_inner)
    with pytest.raises(RuntimeError, match="empty response"):
        client.generate(sample_prompt())
