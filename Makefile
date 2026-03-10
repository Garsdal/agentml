.PHONY: dev test lint run format

dev:
	uv sync --all-extras

test:
	uv run pytest -v

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

run:
	uv run agentml start
