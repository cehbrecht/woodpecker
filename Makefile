.PHONY: help install dev check test docs docs-serve list-fixes

CHECK_PATH ?= .

help:
	@echo "Common targets (run after conda env is activated):"
	@echo "  make install    - install package in editable mode"
	@echo "  make dev        - install package + docs extras"
	@echo "  make check      - run fix checks (default path: .)"
	@echo "  make test       - run pytest test suite"
	@echo "  make docs       - generate docs artifacts and build site"
	@echo "  make docs-serve - generate docs artifacts and serve MkDocs"
	@echo "  make list-fixes - show registered fixes"

install:
	pip install -e .

dev:
	pip install -e ".[docs]"

check:
	woodpecker check $(CHECK_PATH)

test:
	pytest -q

docs:
	python scripts/generate_fix_catalog.py
	python scripts/generate_fix_webpage.py
	mkdocs build --strict

docs-serve:
	python scripts/generate_fix_catalog.py
	python scripts/generate_fix_webpage.py
	mkdocs serve

list-fixes:
	woodpecker list-fixes