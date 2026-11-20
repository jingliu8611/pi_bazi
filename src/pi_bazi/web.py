"""
Flask web UI for the Bazi analysis assistant.

Binds to 127.0.0.1 (local only — not intended as a public server).

Start with:
    pi-bazi-web
    pi-bazi-web --port 8080
    pi-bazi-web --debug

Routes:
    GET  /          — render the empty input form
    POST /analyze   — validate, run analysis, render result or error

Error mapping:
    ValueError          → 400  (invalid pillar / gender input)
    LLMRateLimitError   → 429  (API quota exceeded)
    LLMUnavailableError → 503  (server or network error)
    Exception           → 500  (unexpected failure)
"""

import argparse

import markdown
import nh3
from flask import Flask, render_template, request

from pi_bazi.analysis_service import run_analysis
from pi_bazi.llm import LLMRateLimitError, LLMUnavailableError

app = Flask(__name__)

# ---------------------------------------------------------------------------
# HTML sanitisation config
# Tags and attributes that the markdown library can produce.
# Everything else (e.g. <script>, event handlers) is stripped by nh3.
# ---------------------------------------------------------------------------

_ALLOWED_TAGS: set[str] = {
    "p", "br", "hr",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "blockquote", "pre", "code",
    "strong", "em", "del", "s",
    "a",
    "table", "thead", "tbody", "tr", "th", "td",
}

_ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    "a":  {"href", "title"},
    "th": {"align"},
    "td": {"align"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_result(text: str) -> str:
    """Convert LLM markdown output to sanitized HTML safe for direct template insertion."""
    raw_html = markdown.markdown(text, extensions=["tables"])
    return nh3.clean(raw_html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRIBUTES)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    year   = request.form.get("year",   "").strip()
    month  = request.form.get("month",  "").strip()
    day    = request.form.get("day",    "").strip()
    hour   = request.form.get("hour",   "").strip()
    gender = request.form.get("gender", "").strip()

    # Passed back to the template so the form repopulates on error.
    form_values = dict(year=year, month=month, day=day, hour=hour, gender=gender)

    try:
        result_text = run_analysis(year, month, day, hour, gender)
    except ValueError as exc:
        return render_template(
            "index.html", error=str(exc), **form_values
        ), 400
    except LLMRateLimitError as exc:
        return render_template(
            "index.html",
            error=f"请求频率超限，请稍后再试。({exc})",
            **form_values,
        ), 429
    except LLMUnavailableError as exc:
        return render_template(
            "index.html",
            error=f"API 服务暂时不可用，请稍后再试。({exc})",
            **form_values,
        ), 503
    except Exception as exc:  # noqa: BLE001
        return render_template(
            "index.html",
            error=f"分析失败，请稍后再试。({exc})",
            **form_values,
        ), 500

    result_html = _render_result(result_text)
    return render_template("index.html", result=result_html, **form_values)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for the pi-bazi-web console script."""
    parser = argparse.ArgumentParser(
        prog="pi-bazi-web",
        description="八字命理分析助手 — Web UI (127.0.0.1 only)",
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="Port to listen on (default: 5000)"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable Flask debug mode (development only)"
    )
    args = parser.parse_args()

    print(f"Starting Bazi web UI at http://127.0.0.1:{args.port}/")
    app.run(host="127.0.0.1", port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
