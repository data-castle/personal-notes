# Contributing

Thank you for your interest in contributing to Personal Notes!

## Development Setup

### Prerequisites

- Python 3.13+
- Git
- [UV](https://docs.astral.sh/uv/) package manager

### Setup

```bash
git clone https://github.com/YOUR-USERNAME/personal-notes.git
cd personal-notes
uv sync --all-groups
```

### Install Pre-commit Hooks (Optional)

```bash
uv run pre-commit install
```

Note: Pre-commit hooks only run on manual commits, not when using `uv run sync`.

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest src/tests/test_sync.py
```

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Format code
uv run ruff format

# Check for issues
uv run ruff check

# Fix auto-fixable issues
uv run ruff check --fix
```

## Pull Request Process

1. Create a branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `uv run pytest`
4. Format code: `uv run ruff format`
5. Commit: `git commit -m "Description"`
6. Push: `git push origin feature/your-feature`
7. Open a Pull Request

## Code Guidelines

- Use type hints
- Keep functions small and focused
- Write tests for new features
- Update documentation as needed
- Follow existing code patterns

## Project Structure

```
src/
├── core.py          # Shared utilities (CliResult, file I/O)
├── new_note.py      # Note creation logic
├── sync.py          # Git sync logic
└── tests/
    ├── conftest.py           # Shared test fixtures
    ├── test_new_note.py      # Note creation tests
    ├── test_sync.py          # Sync tests
    └── test_integration.py   # End-to-end tests
```

## Testing Guidelines

- Use pytest fixtures from `conftest.py`
- Test both success and error cases
- Use descriptive test names
- Keep tests focused on one thing

## Questions?

Open an issue for questions or suggestions.
