"""
Command-line interface for the Bazi analysis assistant.

Usage (interactive):
    pi-bazi

Usage (non-interactive):
    pi-bazi --year 甲子 --month 丙寅 --day 戊午 --hour 庚申 --gender 男

Any argument not supplied on the command line will be prompted interactively.

Pipeline (delegated to analysis_service.run_analysis):
    validate input → load book → build prompt → call LLM → display result
"""

import argparse
import sys

from pi_bazi.analysis_service import run_analysis
from pi_bazi.chart import BaziChart


# ---------------------------------------------------------------------------
# Interactive helpers
# ---------------------------------------------------------------------------


def _ask(label: str, example: str) -> str:
    """Prompt the user for one field, showing an example."""
    return input(f"{label} (例如 {example}): ").strip()


def _collect_inputs(args: argparse.Namespace) -> tuple[str, str, str, str, str]:
    """Return (year, month, day, hour, gender), prompting for any missing values."""
    year   = args.year   or _ask("年柱", "甲子")
    month  = args.month  or _ask("月柱", "丙寅")
    day    = args.day    or _ask("日柱", "戊午")
    hour   = args.hour   or _ask("时柱", "庚申")
    gender = args.gender or _ask("性别", "男 / 女")
    return year, month, day, hour, gender


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """
    CLI entry point. Accepts an optional argv list for testing.
    """
    parser = argparse.ArgumentParser(
        prog="pi-bazi",
        description="八字命理分析助手 — 以《滴天髓》为知识依据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  pi-bazi --year 甲子 --month 丙寅 --day 戊午 --hour 庚申 --gender 男\n"
            "  pi-bazi   (interactive mode)"
        ),
    )
    parser.add_argument("--year",   help="年柱, 例如: 甲子")
    parser.add_argument("--month",  help="月柱, 例如: 丙寅")
    parser.add_argument("--day",    help="日柱, 例如: 戊午")
    parser.add_argument("--hour",   help="时柱, 例如: 庚申")
    parser.add_argument("--gender", help="性别: 男 / 女 / male / female")

    args = parser.parse_args(argv)

    # Collect — may prompt interactively
    year, month, day, hour, gender = _collect_inputs(args)

    # Validate early so the user gets immediate feedback before waiting for LLM
    try:
        chart = BaziChart.from_strings(year, month, day, hour, gender)
    except ValueError as exc:
        print(f"\n输入有误: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\n命盘: {chart}")
    print("\n正在分析，请稍候...\n")

    try:
        result = run_analysis(year, month, day, hour, gender)
    except Exception as exc:
        print(f"\n分析失败: {exc}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print(result)
    print("=" * 60)


if __name__ == "__main__":
    main()
