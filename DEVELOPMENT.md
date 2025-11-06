# Development Guide

This guide covers how to set up and work on django-eventtools using modern Python tooling.

## Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer

## Quick Start

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup

```bash
git clone https://github.com/gregplaysguitar/django-eventtools.git
cd django-eventtools

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest tests/tests.py::EventToolsTestCase::test_single_event

# Run with coverage
pytest --cov=eventtools --cov-report=html
```

### Code Quality

```bash
# Run linter (ruff)
ruff check eventtools tests

# Auto-fix linting issues
ruff check --fix eventtools tests

# Format code
ruff format eventtools tests

# Type checking (mypy)
mypy eventtools
```

### Working with uv

```bash
# Install the package in editable mode
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"

# Install with test dependencies only
uv pip install -e ".[test]"

# Add a new dependency
# Edit pyproject.toml, then:
uv pip install -e ".[dev]"

# Update all dependencies
uv pip install --upgrade -e ".[dev]"
```

## Project Structure

```
django-eventtools/
├── eventtools/          # Main package
│   ├── __init__.py
│   ├── models.py        # Core models and logic
│   ├── py.typed         # PEP 561 type marker
│   └── _version.py      # Version info
├── tests/               # Test suite
│   ├── __init__.py
│   ├── models.py        # Test models
│   ├── test_settings.py # Django test settings
│   └── tests.py         # Test cases
├── pyproject.toml       # Modern Python project config
├── mypy.ini            # Type checking config
├── .python-version     # Python version for this project
└── README.md           # User documentation
```

## Common Tasks

### Adding a New Feature

1. Create a new branch
2. Write tests first (TDD)
3. Implement the feature
4. Run tests: `pytest`
5. Check types: `mypy eventtools`
6. Lint code: `ruff check --fix eventtools`
7. Commit and push

### Running Tests for Multiple Django Versions

```bash
# Using tox (if installed)
tox

# Or test specific environment
tox -e py312-django50
```

### Building the Package

```bash
# Install build tools
uv pip install build

# Build distributions
python -m build

# Check the dist/ directory
ls -lh dist/
```

### Publishing to PyPI

```bash
# Install twine
uv pip install twine

# Build first
python -m build

# Upload to PyPI
twine upload dist/*
```

## Troubleshooting

### Tests Failing

If tests fail with import errors:
```bash
# Make sure you're in the virtual environment
source .venv/bin/activate

# Reinstall in editable mode
uv pip install -e ".[dev]"
```

### Type Checking Issues

If mypy fails with Django-related errors:
```bash
# Make sure django-stubs is installed
uv pip install django-stubs
```

### Dependency Conflicts

```bash
# Remove virtual environment and start fresh
rm -rf .venv
uv venv
uv pip install -e ".[dev]"
```

## Code Style

This project follows:
- **PEP 8** for code style (enforced by ruff)
- **PEP 484** for type hints
- **Black-compatible** formatting (88 character line length)
- **Import sorting** with isort rules in ruff

## Performance Testing

```bash
# Run tests with profiling
pytest --profile

# Or use pytest-benchmark if needed
uv pip install pytest-benchmark
```

## Documentation

When adding new features:
1. Update docstrings (Google style)
2. Update README.md
3. Add examples if applicable
4. Update CHANGELOG.md

## Getting Help

- Open an issue on GitHub
- Check existing issues for similar problems
- Review the test suite for usage examples
