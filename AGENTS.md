# Project Instructions

## 1. Project Overview

Build a knowledge-grounded Bazi（八字） analysis assistant using Pi as the agent
harness and Python for deterministic application logic.

The initial knowledge source is the classical Chinese text 滴天髓
(Di Tian Sui), attributed in the local edition to 京图 and annotated by 刘基.

The system should eventually support multiple interchangeable classical
Bazi knowledge sources, such as 子平真诠.

## 2. Core Requirements

- Users provide the four pillars(四柱八字) directly and gender.
- Do NOT implement birth date conversion or automatic Bazi chart generation.
- Keep book-specific knowledge and processing logic modular.
- Ground analysis in the selected source text.
- Clearly distinguish source-based statements from AI interpretation.
- Do not invent quotations, chapter references, or claims from source books.
- When evidence is insufficient, explicitly say so.

## 3. Architecture Principles

- Keep the initial implementation simple.
- Avoid unnecessary frameworks and dependencies.
- Use Python for deterministic parsing, normalization, validation,
  text processing, and other application logic.
- Keep the knowledge source independent from the analysis engine.
- Design for future support of multiple books without overengineering now.
- Introduce RAG or vector databases only when there is a clear need.

## 4. Development Guidelines

- Use English for source code, variable names, function names,
  class names, comments, and Git commit messages.
- Use Chinese for user-facing Bazi analysis and explanations.
- Prefer clear, small, testable modules.
- Add tests for meaningful functionality.
- Do not introduce dependencies without explaining why they are needed.
- Update README.md when project setup or usage changes.
- Keep generated files and local source materials out of Git unless
  explicitly required.

## 5. Working Process

- **Greeting / Non-task inputs:** If the user simply greets you (e.g., "hello") or asks a general question without requesting a feature or code change, respond conversationally without running shell commands or inspecting the directory.
- **Directory inspection:** When inspecting the project structure, always exclude `venv/`, `.venv*`, `.git/`, `__pycache__/`, and `data/` to avoid noisy output.

Before implementing a feature:

1. Inspect the existing project structure and code.
2. Explain the proposed approach briefly.
3. Identify files that need to be created or modified.
4. Implement incrementally.
5. Run relevant tests and checks.
6. Summarize changes and any remaining limitations.

Do not make large architectural changes without discussing them first.
