# Repository Guidelines

## Project Structure & Module Organization

- `src/atlas_mcp/`: core MCP server implementation (`server.py`) and helper pages (`central_page.py`).
- `tests/`: pytest suite (e.g., `tests/test_server.py`, `tests/test_central_page.py`).
- `scripts/`: utilities for data lookup (see `scripts/dsid_finder/`).
- `README.md`: usage notes, transport modes, and example client calls.

## Build, Test, and Development Commands

- `uv run -m atlas_mcp.server --transport stdio`: run the MCP server in stdio mode (default for VS Code).
- `uv run -m atlas_mcp.server --transport http --port 8080`: run HTTP server at `http://localhost:8080/mcp`.
- `fastmcp dev src/atlas_mcp/server.py`: run with the fastmcp dev UI (if available).
- `uv run pytest`: run the test suite.

## Coding Style & Naming Conventions

- Python code uses 4-space indentation and snake_case for modules/functions.
- Formatting/linting: `black` + `flake8`; line length max is 99 (`.flake8`).
- Tests live in `tests/` and are named `test_*.py`.

## Testing Guidelines

- Framework: `pytest` (with optional `pytest-asyncio`, `pytest-mock`, `pytest-cov`).
- Add tests for new behavior and for bug fixes. Keep tests close to the module they cover.
- Tests for each source file are in `test_<source-filename>.py` so there is a 1:1 matching between tests and source files.
- Run `uv run pytest` before opening a PR.
- When tracking down a bug at the request of the user, please generate a test case that triggers the bug before fixing the bug.

## Commit & Pull Request Guidelines

- Commit messages follow short, imperative summaries, often with a PR/issue suffix like `(#31)`.
- PRs should include a concise description, test results, and any relevant context (e.g., required ATLAS credentials or WSL2 setup).

## Environment & Configuration Notes

- The project depends on `ami-helper`, which currently requires `/cvmfs` and Linux (often via WSL2 `atlas_al9`).
- For local data access, run `voms-proxy-init` and verify `ami-helper` works before starting the server.
