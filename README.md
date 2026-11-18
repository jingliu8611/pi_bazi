# Pi Bazi

A knowledge-grounded Bazi(八字) analysis assistant based on classical Chinese Bazi literature.

## Project Goal

Build an AI assistant that analyzes Bazi charts using classical Chinese texts
as its primary knowledge source.

The initial knowledge source is *Di Tian Sui* (滴天髓).

## Scope

- Users provide the four pillars(四柱八字) directly and gender.
- No birth date conversion or automatic Bazi chart generation.
- Ground analysis in the selected classical text.
- Keep the knowledge source modular so other books can be added later.

## Knowledge Sources

- Initial source: 滴天髓
- Future candidates: 子平真诠 and other classical Bazi texts

Original source files are kept locally and are not committed to this repository.

## Project Structure

- `books/`: Local source books and source metadata
- `data/`: Processed text and retrieval data
- `src/pi_bazi/`: Application code
- `tests/`: Automated tests

## Development

Python project configuration and dependencies are managed through `pyproject.toml`.

Development dependencies:

```bash
python -m pip install -e ".[dev]"
