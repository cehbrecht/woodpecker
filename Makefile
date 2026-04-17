.PHONY: help install install-uv install-plugins install-plugins-uv dev dev-uv format lint lint-fix check test docs docs-serve list-fixes

CHECK_PATH ?= .
PYTHON ?= $(shell python -c 'import sys; print(sys.executable)')
PLUGIN_PATHS := plugins/woodpecker-atlas-plugin \
	plugins/woodpecker-cmip6-plugin \
	plugins/woodpecker-cmip6-decadal-plugin \
	plugins/woodpecker-cmip7-plugin
PLUGIN_INSTALL_ARGS := $(foreach p,$(PLUGIN_PATHS),-e $(p))

help:
	@echo "Common targets (run after conda env is activated):"
	@echo "  make install    - install package in editable mode"
	@echo "  make install-uv - install package in editable mode via uv"
	@echo "  make install-plugins    - install current local plugin packages"
	@echo "  make install-plugins-uv - install local plugin packages via uv"
	@echo "  make dev        - install package + docs + dev + full extras + plugins"
	@echo "  make dev-uv     - dev install via uv (same extras/plugins as make dev)"
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

install-plugins:
	pip install $(PLUGIN_INSTALL_ARGS)

install-plugins-uv:
	uv pip install --python "$(PYTHON)" $(PLUGIN_INSTALL_ARGS)

dev: install-plugins
	pip install -e ".[docs,dev,full]"

dev-uv: install-plugins-uv
	uv pip install --python "$(PYTHON)" -e ".[docs,dev,full]"

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