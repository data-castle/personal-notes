# Contributing to Personal Notes

Thank you for your interest in contributing to the Personal Notes project! This document provides guidelines for contributing to the template repository.

## Development Setup

### Prerequisites

- Python 3.13 or higher
- Git
- UV (Python package manager)

### Getting Started

1. Fork and clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/personal-notes.git
cd personal-notes
```

2. Install dependencies:

```bash
uv sync --all-groups
```

3. Install pre-commit hooks (optional but recommended):

```bash
uv run --group lint pre-commit install
```

## Development Workflow

### Making Changes

1. Create a new branch for your feature or fix:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes to the code

3. Run linting and formatting:

```bash
uv run --group lint ruff check src/
uv run --group lint ruff format src/
```

4. If you've added tests, run them:

```bash
uv run --group dev pytest tests/ -v
```

5. Commit your changes:

```bash
git add .
git commit -m "Description of your changes"
```

6. Push to your fork:

```bash
git push origin feature/your-feature-name
```

7. Open a Pull Request on GitHub

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Keep functions focused and small
- Write descriptive commit messages

### Running Formatters

Format code automatically:

```bash
uv run --group lint ruff format
```

Check for linting issues:

```bash
uv run --group lint ruff check
```

Fix auto-fixable linting issues:

```bash
uv run --group lint ruff check --fix
```

## Testing

### Writing Tests

- Place tests in the `tests/` directory
- Use pytest for testing
- Aim for good test coverage
- Test edge cases and error conditions

### Running Tests

Run all tests:

```bash
uv run --group dev pytest
```

## Pull Request Guidelines

1. **Title**: Use a clear, descriptive title
2. **Description**: Explain what changes you made and why
3. **Tests**: Add or update tests as needed
4. **Documentation**: Update README or docs if needed
5. **Breaking Changes**: Clearly note any breaking changes
