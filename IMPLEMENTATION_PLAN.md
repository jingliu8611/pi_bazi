# Implementation Plan: Pi Bazi Analysis Assistant

## Current State

- Project scaffold is in place: `src/pi_bazi/`, `tests/`, `books/`, `pyproject.toml`
- Di Tian Sui source text is available (1,053 lines, ~30–50K tokens)
- Dependencies already declared: `google-genai`, `python-dotenv`, `pytest`, `ruff`
- `src/pi_bazi/__init__.py` is empty — no logic implemented yet

---

## LLM Strategy: Gemini Free Tier with Full-Book Context

The Di Tian Sui text is small enough (~30–50K tokens) to fit comfortably within
Gemini's 1M-token context window. Rather than building a custom parser and
keyword-based retrieval system, the entire book will be included in every request
as a system-level knowledge source.

**Explicit context caching is not available on Gemini's free tier.** The full book
text will be sent with each request. Gemini 2.0 Flash may apply implicit/automatic
caching internally, but this is not guaranteed or controllable.

This approach:
- Gives the LLM full context of the source book, avoiding missed references
- Eliminates the need for a custom chapter parser and retrieval module
- Keeps the implementation simple and easy to maintain
- Can be revisited (e.g. upgrade to paid tier for explicit caching, or switch to
  Claude prompt caching) if cost or latency becomes a concern

---

## Phase 1 — Core Data Structures & Validation

**Files:** `src/pi_bazi/chart.py`, `tests/test_chart.py`

- Define constants: 10 Heavenly Stems (天干), 12 Earthly Branches (地支)
- Define a `BaziChart` dataclass: year/month/day/hour pillars + gender
- Implement input parsing and validation (reject invalid stems/branches)
- Write unit tests for valid and invalid inputs

---

## Phase 2 — Book Loader

**Files:** `src/pi_bazi/book.py`, `tests/test_book.py`

- Load `books/ditiansui_jingtu_liuji.txt` from a configurable path
- Return the full text as a single string, ready to be injected into the prompt
- Write a basic test to verify the file loads and is non-empty

> **Note:** No chapter parsing or retrieval logic needed. The full text is passed
> directly to the LLM as context.

---

## Phase 3 — Prompt Builder

**Files:** `src/pi_bazi/prompt.py`, `tests/test_prompt.py`

- Build a structured prompt combining:
  - A system instruction grounding the LLM in the source book
  - The full Di Tian Sui text as reference material
  - The user's Bazi chart (four pillars + gender)
  - Clear instruction to distinguish source-grounded claims from AI interpretation
- Keep prompt templates clean and easy to iterate on

---

## Phase 4 — LLM Integration (Gemini Free Tier)

**Files:** `src/pi_bazi/llm.py`

- Wrap `google-genai` calls in a thin client using the free-tier Gemini model
  (e.g. `gemini-3.5-flash`)
- Load API key from `.env` via `python-dotenv`
- Send the constructed prompt, return response text
- Keep the LLM client interface simple so it can be swapped later (e.g. paid
  Gemini tier with explicit caching, or Claude with prompt caching)

---

## Phase 5 — CLI Entry Point

**Files:** `src/pi_bazi/cli.py`, update `pyproject.toml`

- Simple interactive CLI: prompt user for four pillars and gender
- Run the full pipeline: validate → load book → build prompt → call LLM → display result
- Register as a `pi-bazi` console script in `pyproject.toml`

---

## Phased Delivery Order

| Phase | Priority   | Deliverable                          |
|-------|------------|--------------------------------------|
| 1     | ✅ First   | Chart data model + validation        |
| 2     | ✅ First   | Book loader (full text)              |
| 3     | 🔜 Second  | Prompt builder                       |
| 4     | 🔜 Second  | Gemini free-tier LLM integration     |
| 5     | 🔜 Third   | CLI entry point                      |
| 6     | 🔜 Fourth  | Web GUI (Flask)                      |

---

## Phase 6 — Web GUI Extension

**Files:** `src/pi_bazi/analysis_service.py`, `src/pi_bazi/web.py`, `src/pi_bazi/templates/index.html`, `pyproject.toml`, `tests/test_web.py`

- **Refactoring (Shared Analysis Service):**
  - `cli.py` already contains a `run_analysis()` function that encapsulates the
    full pipeline. **Move** `run_analysis()` from `cli.py` into the new
    `src/pi_bazi/analysis_service.py`.
  - Update `cli.py` to import it: `from pi_bazi.analysis_service import run_analysis`.
  - Update `cli.py::main()` to call `run_analysis()` rather than re-implementing
    the pipeline inline (currently `main()` duplicates the validate → load book →
    build prompt → call LLM sequence).
  - Update `tests/test_cli.py` to import `run_analysis` from
    `pi_bazi.analysis_service` (or keep a re-export in `cli.py` if backward
    compatibility is preferred).
  - This ensures `web.py` imports from `analysis_service` and never needs to
    import from `cli.py` (which would drag in `argparse` and other CLI concerns).
- **Dependencies:** Add `flask`, `markdown`, and `nh3` as optional `[web]` extras
  in `pyproject.toml`. Do **not** add them as core dependencies — they are only
  needed when running the web UI, not the CLI.
  ```toml
  [project.optional-dependencies]
  web = ["flask>=3.0", "markdown>=3.6", "nh3>=0.2"]
  dev = ["pytest>=8.0", "ruff>=0.8", "pi-bazi[web]"]
  ```
  > **Note:** Use `nh3` instead of `bleach`. `bleach` is deprecated — its own
  > README directs users to migrate to `nh3`, a lightweight Rust-backed HTML
  > sanitizer. Install the web variant with `pip install -e ".[web]"`.
- **LLM Error Wrapping:**
  - Extend `llm.py` to catch SDK-specific exceptions (rate limit, quota exceeded,
    network timeout) and re-raise them as typed Python exceptions, e.g.
    `LLMRateLimitError`, `LLMUnavailableError`.
  - `web.py` maps these to HTTP 429 / 503 responses.
  - `cli.py` catches them and prints a human-readable error message.
  - This keeps error-handling logic in one place rather than duplicating SDK
    exception handling in both the web and CLI layers.
- **Web Server:**
  - Create `src/pi_bazi/web.py` as a minimal Flask application binding to
    `127.0.0.1`. This is a local-only tool; no production WSGI server is needed.
  - Register the web entry point in `pyproject.toml`:
    ```toml
    pi-bazi-web = "pi_bazi.web:main"
    ```
  - Handle `LLMRateLimitError` → 429, `LLMUnavailableError` → 503, and
    `ValueError` (bad input) → 400.
- **Frontend:**
  - Create `src/pi_bazi/templates/index.html` with a simple form to collect inputs.
  - Implement a basic loading indicator and disable the "Analyze" button during
    submission to prevent duplicate submissions.
  - Render LLM output on the server: convert with `markdown.markdown()`, then
    sanitize with `nh3.clean()` before inserting into the HTML response.
  - Ensure form values persist across failures.
- **Testing:**
  - Add unit tests for `analysis_service.py` (covering the moved `run_analysis()`).
  - Add integration tests for Flask routes with mocked LLM API calls.
  - Verify HTTP error codes are returned correctly for each error type.
- **Constraints:** Keep frontend simple (plain HTML/JS, no build system) and do
  not change core analysis logic.

