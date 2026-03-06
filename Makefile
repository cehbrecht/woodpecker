.PHONY: help install install-uv dev dev-uv format lint lint-fix check test docs docs-serve list-fixes

CHECK_PATH ?= .
PYTHON ?= $(shell python -c 'import sys; print(sys.executable)')

help:
	@echo "Common targets (run after conda env is activated):"
	@echo "  make install    - install package in editable mode"
	@echo "  make install-uv - install package in editable mode via uv"
	@echo "  make dev        - install package + docs + dev + io + zarr extras"
	@echo "  make dev-uv     - dev install via uv (same extras as make dev)"
	@echo "  make format     - run Ruff formatter"
	@echo "  make lint       - run Ruff lint checks"
	@echo "  make lint-fix   - auto-fix Ruff lint issues"
	@echo "  make check      - run fix checks (default path: .)"
	@echo "  make test       - run pytest test suite"
	@echo "  make docs       - generate docs artifacts and build site"
	@echo "  make docs-serve - generate docs artifacts and serve MkDocs"
	@echo "  make list-fixes - show registered fixes"

install:
	pip install -e .

install-uv:
	uv pip install --python "$(PYTHON)" -e .

dev:
	pip install -e ".[docs,dev,io,zarr]"

dev-uv:
	uv pip install --python "$(PYTHON)" -e ".[docs,dev,io,zarr]"

format:
	ruff format .

lint:
	ruff check .

lint-fix:
	ruff check . --fix

check:
	woodpecker check $(CHECK_PATH)

test:
	pytest -v

docs:
	python scripts/generate_fix_catalog.py
	python scripts/generate_fix_webpage.py
	NO_MKDOCS_2_WARNING=1 mkdocs build --strict

docs-serve:
	python scripts/generate_fix_catalog.py
	python scripts/generate_fix_webpage.py
	NO_MKDOCS_2_WARNING=1 mkdocs serve

list-fixes:
	woodpecker list-fixes