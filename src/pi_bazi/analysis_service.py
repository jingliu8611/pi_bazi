"""
Shared analysis pipeline for the Bazi analysis assistant.

This module is the single entry point for running a full analysis. Both the
CLI (cli.py) and the future web UI (web.py) import from here. Keeping the
pipeline here ensures neither interface layer imports from the other, and both
get identical behaviour.

Pipeline:
    validate input → load book → build prompt → call LLM → return text
"""

from pi_bazi.book import load_book
from pi_bazi.chart import BaziChart
from pi_bazi.llm import GeminiClient
from pi_bazi.prompt import build_prompt


def run_analysis(
    year: str,
    month: str,
    day: str,
    hour: str,
    gender: str,
    *,
    _client: GeminiClient | None = None,
) -> str:
    """
    Run the full Bazi analysis pipeline and return the LLM response text.

    Args:
        year, month, day, hour: Pillar strings, e.g. '甲子'.
        gender: '男', '女', 'male', or 'female'.
        _client: Optional pre-built GeminiClient (used in tests to avoid
                 real API calls).

    Returns:
        The analysis as a plain string.

    Raises:
        ValueError:   If any pillar or gender input is invalid.
        RuntimeError: If the LLM returns an empty response.
    """
    chart = BaziChart.from_strings(year, month, day, hour, gender)
    book = load_book()
    prompt = build_prompt(chart, book)
    client = _client or GeminiClient()
    return client.generate(prompt)
