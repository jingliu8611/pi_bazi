"""
Book loader for Bazi classical knowledge sources.

Loads the full text of a classical Bazi book to be used as LLM context.
No chapter parsing or retrieval is performed — the entire text is passed
to the LLM on each request.
"""

from dataclasses import dataclass
from pathlib import Path

# Default path to the bundled Di Tian Sui source text.
# Resolves relative to this file: src/pi_bazi/book.py -> project root -> books/
_PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_BOOK_PATH: Path = _PROJECT_ROOT / "books" / "ditiansui_jingtu_liuji.txt"


@dataclass(frozen=True)
class BookSource:
    """A loaded classical Bazi knowledge source."""

    title: str       # First non-empty line of the file, used as the book title
    path: Path       # Absolute path to the source file
    text: str        # Full text content

    @property
    def char_count(self) -> int:
        """Total number of characters in the text."""
        return len(self.text)

    @property
    def line_count(self) -> int:
        """Total number of lines in the text."""
        return len(self.text.splitlines())


def load_book(path: Path | str = DEFAULT_BOOK_PATH) -> BookSource:
    """
    Load a classical Bazi knowledge source from a UTF-8 text file.

    Args:
        path: Path to the book text file. Defaults to Di Tian Sui.

    Returns:
        A BookSource containing the full text, ready to inject into a prompt.

    Raises:
        FileNotFoundError: If the file does not exist at the given path.
        ValueError: If the file exists but contains no readable content.
    """
    path = Path(path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Book file not found: {path}")

    text = path.read_text(encoding="utf-8")

    if not text.strip():
        raise ValueError(f"Book file is empty: {path}")

    title = next(
        (line.strip() for line in text.splitlines() if line.strip()),
        "Unknown",
    )

    return BookSource(title=title, path=path, text=text)
