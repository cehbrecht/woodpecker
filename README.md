# Woodpecker

Woodpecker is a small, **code-driven catalog of dataset fixes** for climate data workflows (CDS/WPS, ESMValTool, etc.).
Fixes are identified by **stable short codes** (e.g. `CMIP6D01`) so external services (like an ESGF errata UI) can link to them.

## What’s in this starter

- `woodpecker.fixes.registry.FixRegistry`: in-memory registry (simple today, extensible tomorrow)
- `woodpecker` CLI:
  - `woodpecker list-fixes`
  - `woodpecker list-fixes --format md|json`
- Documentation generation:
  - `docs/FIXES.md` (Markdown catalog)
  - `docs/FIXES.json` (machine-readable)
  - `docs/fixes.html` (small interactive page with anchors, ideal for linking `#CMIP6D01`)
- MkDocs site (Material theme) + GitHub Pages workflow

## Quickstart

```bash
pip install -e .
woodpecker list-fixes
```

Generate/update docs:

```bash
pip install -e ".[docs]"
python scripts/generate_fix_catalog.py
python scripts/generate_fix_webpage.py
mkdocs serve
```

## Future-proofing (without complexity today)

Woodpecker intentionally stays simple and “human-countable”, but the design leaves room to grow:

- **Pydantic (optional)**: If fixes become numerous or contributed by multiple projects, Pydantic models can
  validate fields, enforce code patterns, and simplify JSON serialization. See `woodpecker/fixes/fix_template.py`.
- **Pluggy (optional)**: If you want third-party packages to register fixes via entry points (like pytest plugins),
  the registry API can be backed by pluggy later with minimal changes to CLI/docs.
- **Scaling docs/UI**: `FIXES.json` is a stable export format that can later feed search indexes or richer UIs.

## GitHub Pages

This repo includes a workflow that builds and deploys the MkDocs site to GitHub Pages on pushes that touch fixes/docs/scripts.
After enabling GitHub Pages (Settings → Pages), your fix codes become clickable URLs (e.g. `.../fixes.html#CMIP6D01`),
which an errata service can reference.
