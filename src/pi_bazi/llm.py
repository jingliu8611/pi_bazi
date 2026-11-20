"""
Gemini LLM client for the Bazi analysis assistant.

Wraps google-genai in a thin, swappable client. The API key is loaded from
the GEMINI_API_KEY environment variable (via .env). The model defaults to
gemini-2.0-flash (Gemini free tier).

Design notes:
- The inner google.genai.Client is injectable via _inner for unit testing
  without making real API calls.
- If the response is blocked by safety filters, response.text will be None;
  a clear RuntimeError is raised in that case.
- SDK-specific errors (rate limit, server error, network failure) are caught
  in generate() and re-raised as LLMRateLimitError or LLMUnavailableError so
  callers (CLI, web) can handle them without importing google-genai types.
- To swap providers later (e.g. Claude), replace this module with a new
  implementation that accepts and returns the same types.
"""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from pi_bazi.prompt import PromptParts

DEFAULT_MODEL = "gemini-3.5-flash-lite"


# ---------------------------------------------------------------------------
# Typed exceptions
# ---------------------------------------------------------------------------


class LLMError(RuntimeError):
    """Base class for all LLM-related errors raised by this module."""


class LLMRateLimitError(LLMError):
    """Raised when the API returns HTTP 429 (Too Many Requests / quota exceeded)."""


class LLMUnavailableError(LLMError):
    """Raised when the API is unreachable or returns a 5xx / unexpected 4xx error."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class GeminiClient:
    """
    A thin wrapper around the google-genai SDK.

    Args:
        model:   Gemini model name. Defaults to gemini-3.5-flash-lite.
        api_key: Gemini API key. If not provided, falls back to the
                 GEMINI_API_KEY environment variable (loaded from .env).
        _inner:  Optional pre-built google.genai.Client, used in tests to
                 avoid real API calls.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        _inner: genai.Client | None = None,
    ) -> None:
        load_dotenv()
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key and _inner is None:
            raise ValueError(
                "No Gemini API key found. "
                "Set GEMINI_API_KEY in your .env file or pass api_key= explicitly."
            )
        self.model = model
        self._inner: genai.Client = _inner or genai.Client(api_key=key)

    def generate(self, prompt: PromptParts) -> str:
        """
        Send a prompt to Gemini and return the response text.

        Args:
            prompt: A PromptParts with system_instruction and user_message.

        Returns:
            The model's response as a plain string.

        Raises:
            LLMRateLimitError:   HTTP 429 — quota or rate limit exceeded.
            LLMUnavailableError: HTTP 5xx, other 4xx, or network/timeout error.
            RuntimeError:        Empty response (safety filter or model refusal).
        """
        try:
            response = self._inner.models.generate_content(
                model=self.model,
                contents=prompt.user_message,
                config=types.GenerateContentConfig(
                    system_instruction=prompt.system_instruction,
                ),
            )
        except ClientError as exc:
            if exc.code == 429:
                raise LLMRateLimitError(
                    "Gemini API rate limit exceeded. Please wait a moment and try again."
                ) from exc
            raise LLMUnavailableError(
                f"Gemini API request failed (HTTP {exc.code}): {exc.message}"
            ) from exc
        except ServerError as exc:
            raise LLMUnavailableError(
                f"Gemini API server error (HTTP {exc.code}). Please try again later."
            ) from exc
        except OSError as exc:
            raise LLMUnavailableError(
                f"Network error while contacting Gemini API: {exc}"
            ) from exc

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response. "
                "The request may have been blocked by safety filters."
            )

        return response.text
