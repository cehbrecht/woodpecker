# Woodpecker

Woodpecker is a small, **code-driven catalog of dataset fixes** for climate data workflows (CDS/WPS, ESMValTool, etc.).
Fixes are identified by **stable short codes** (e.g. `CMIP6D01`) so external services (like an ESGF errata UI) can link to them.

## What’s in this starter

- `woodpecker.fixes.registry.FixRegistry`: in-memory registry (simple today, extensible tomorrow)
- `woodpecker` CLI:
  - `woodpecker list-fixes`
  - `woodpecker list-fixes --format md|json`
  - `woodpecker check <path>`
  - `woodpecker fix <path> --write`
- Documentation generation:
  - `docs/FIXES.md` (Markdown catalog)
  - `docs/FIXES.json` (machine-readable)
  - `docs/fixes.html` (small interactive page with anchors, ideal for linking `#CMIP6D01`)
- MkDocs site (Material theme) + GitHub Pages workflow

## Quickstart

Conda environment (recommended):

```bash
conda env create -f environment.yml
conda activate woodpecker
make install
make list-fixes
```

Main requirements are tracked in `pyproject.toml`. Use `make` targets after creating/activating the conda environment (the Makefile intentionally does not manage conda itself).

Common tasks:

```bash
make install     # editable install
make dev         # editable install + docs + pytest extras
make check       # run checks (defaults to current directory)
make test        # run pytest test suite
make docs        # generate docs artifacts + strict mkdocs build
make docs-serve  # generate docs artifacts + run mkdocs serve
```

Lint-style workflow (Ruff-like):

```bash
woodpecker check /path/to/netcdf/or/folder
woodpecker check . --select CMIP6D01
woodpecker fix . --select CMIP6D01        # dry-run by default
woodpecker fix . --select CMIP6D01 --write
```

Fixes are Python classes with a stable code ID and description, and implement `matches()`, `check()`, and optional `apply()`.

Pip-only setup (no conda):

```bash
pip install -e .
woodpecker list-fixes
```

Generate/update docs:

```bash
make docs-serve
```

## Future-proofing (without complexity today)

Woodpecker intentionally stays simple and “human-countable”, but the design leaves room to grow:

- **Pydantic models**: Pydantic is part of core dependencies and can be used for stronger fix schema validation.
  See `woodpecker/fixes/fix_template.py`.
- **Pluggy (optional)**: If you want third-party packages to register fixes via entry points (like pytest plugins),
  the registry API can be backed by pluggy later with minimal changes to CLI/docs.
- **Scaling docs/UI**: `FIXES.json` is a stable export format that can later feed search indexes or richer UIs.

## GitHub Pages

This repo includes a workflow that builds and deploys the MkDocs site to GitHub Pages on pushes that touch fixes/docs/scripts.
After enabling GitHub Pages (Settings → Pages), your fix codes become clickable URLs (e.g. `.../fixes.html#CMIP6D01`),
which an errata service can reference.
