.PHONY: install-dev lint test build

install-dev:
	python -m pip install -e ".[dev]"

lint:
	python -m ruff check .

test:
	python -m pytest

build:
	python -m build
