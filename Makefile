.PHONY: install test lint fmt clean help

help:
	@echo "agent-lens — make targets"
	@echo "  install   Editable install with dev extras (pip install -e '.[dev]')"
	@echo "  test      Run the pytest suite"
	@echo "  lint      Lint with ruff (check only)"
	@echo "  fmt       Auto-fix lint issues + format with ruff"
	@echo "  clean     Remove build/test caches"

install:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

fmt:
	ruff check --fix .
	ruff format .

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
