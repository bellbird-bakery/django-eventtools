.PHONY: help install test lint format typecheck clean build all

help:
	@echo "django-eventtools development commands:"
	@echo ""
	@echo "  make install     - Install package with dev dependencies"
	@echo "  make test        - Run test suite"
	@echo "  make lint        - Run linter (ruff)"
	@echo "  make format      - Format code with ruff"
	@echo "  make typecheck   - Run type checker (mypy)"
	@echo "  make clean       - Remove build artifacts and cache files"
	@echo "  make build       - Build distribution packages"
	@echo "  make all         - Run lint, typecheck, and test"
	@echo ""

install:
	uv pip install -e ".[dev]"

test:
	uv run pytest -v

test-cov:
	uv run pytest --cov=eventtools --cov-report=html --cov-report=term

lint:
	uv run ruff check eventtools tests

lint-fix:
	uv run ruff check --fix eventtools tests

format:
	uv run ruff format eventtools tests

typecheck:
	uv run mypy eventtools

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

all: lint typecheck test
	@echo "✓ All checks passed!"
