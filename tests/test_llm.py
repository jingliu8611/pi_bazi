"""Tests for src/pi_bazi/llm.py

Real API calls are never made here. The google.genai.Client is replaced
with a lightweight mock via the _inner injection point.
"""

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from google.genai.errors import ClientError, ServerError

from pi_bazi.llm import DEFAULT_MODEL, GeminiClient, LLMRateLimitError, LLMUnavailableError
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


# ---------------------------------------------------------------------------
# generate() — SDK error wrapping
# ---------------------------------------------------------------------------


def make_mock_inner_raising(exc: Exception) -> MagicMock:
    """Return a mock inner client whose generate_content raises the given exception."""
    mock_inner = MagicMock()
    mock_inner.models.generate_content.side_effect = exc
    return mock_inner


def test_generate_wraps_429_as_rate_limit_error():
    exc = ClientError(429, {"message": "Too Many Requests", "status": "RESOURCE_EXHAUSTED"})
    client = GeminiClient(_inner=make_mock_inner_raising(exc))
    with pytest.raises(LLMRateLimitError, match="rate limit"):
        client.generate(sample_prompt())


def test_generate_rate_limit_error_preserves_cause():
    exc = ClientError(429, {"message": "Too Many Requests", "status": "RESOURCE_EXHAUSTED"})
    client = GeminiClient(_inner=make_mock_inner_raising(exc))
    with pytest.raises(LLMRateLimitError) as exc_info:
        client.generate(sample_prompt())
    assert exc_info.value.__cause__ is exc


def test_generate_wraps_other_client_error_as_unavailable():
    exc = ClientError(400, {"message": "Bad Request", "status": "INVALID_ARGUMENT"})
    client = GeminiClient(_inner=make_mock_inner_raising(exc))
    with pytest.raises(LLMUnavailableError, match="400"):
        client.generate(sample_prompt())


def test_generate_wraps_server_error_as_unavailable():
    exc = ServerError(503, {"message": "Service Unavailable", "status": "UNAVAILABLE"})
    client = GeminiClient(_inner=make_mock_inner_raising(exc))
    with pytest.raises(LLMUnavailableError, match="503"):
        client.generate(sample_prompt())


def test_generate_server_error_preserves_cause():
    exc = ServerError(503, {"message": "Service Unavailable", "status": "UNAVAILABLE"})
    client = GeminiClient(_inner=make_mock_inner_raising(exc))
    with pytest.raises(LLMUnavailableError) as exc_info:
        client.generate(sample_prompt())
    assert exc_info.value.__cause__ is exc


def test_generate_wraps_os_error_as_unavailable():
    exc = OSError("Connection refused")
    client = GeminiClient(_inner=make_mock_inner_raising(exc))
    with pytest.raises(LLMUnavailableError, match="Network error"):
        client.generate(sample_prompt())


def test_generate_wraps_timeout_as_unavailable():
    # TimeoutError is a subclass of OSError in Python 3
    exc = TimeoutError("timed out")
    client = GeminiClient(_inner=make_mock_inner_raising(exc))
    with pytest.raises(LLMUnavailableError, match="Network error"):
        client.generate(sample_prompt())


def test_llm_rate_limit_error_is_subclass_of_llm_error_and_runtime_error():
    from pi_bazi.llm import LLMError
    err = LLMRateLimitError("test")
    assert isinstance(err, LLMError)
    assert isinstance(err, RuntimeError)


def test_llm_unavailable_error_is_subclass_of_llm_error_and_runtime_error():
    from pi_bazi.llm import LLMError
    err = LLMUnavailableError("test")
    assert isinstance(err, LLMError)
    assert isinstance(err, RuntimeError)
