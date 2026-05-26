# Docs Development

The documentation site is built with MkDocs Material. It combines hand-written
Markdown pages, generated reference pages, a generated interactive fixes page,
and executed notebooks.

## Setup

Use the project development environment:

```bash
conda env create -f environment.yml
conda activate woodpecker
make dev
```

For docs-only dependencies:

```bash
pip install -e ".[docs]"
```

## Build The Site

Build the generated docs artifacts and run a strict MkDocs build:

```bash
make docs
```

Serve the site locally:

```bash
make docs-serve
```

Both targets regenerate references before running MkDocs.

## Generated Artifacts

These files are generated and should be updated through their scripts:

| Artifact | Generator |
| -------- | --------- |
| `docs/FIXES.md` | `scripts/generate_fix_catalog.py` |
| `docs/FIXES.json` | `scripts/generate_fix_catalog.py` |
| `docs/FIX_PLANS.md` | `scripts/generate_fix_plan_catalog.py` |
| `docs/FIX_PLANS.json` | `scripts/generate_fix_plan_catalog.py` |
| `docs/fixes.html` | `scripts/generate_fix_webpage.py` |

The interactive fixes page uses the Jinja template at
`scripts/templates/fixes.html.jinja`.

## Notebooks

Notebook examples live in `docs/notebooks/` and are rendered by
`mkdocs-jupyter` during the docs build. The notebooks use deterministic
synthetic datasets so they can run in CI and in local docs builds.

When adding or editing notebooks, prefer examples that exercise the public API
and can run without external climate data files.

## Strict Builds

The docs build runs MkDocs in strict mode:

```bash
NO_MKDOCS_2_WARNING=1 mkdocs build --strict
```

Strict mode treats warnings as failures. This is useful for catching broken
links, missing nav entries, and Markdown pages that do not resolve correctly
inside the `docs/` tree.

## Source Layout

- `mkdocs.yml`: site configuration, theme, plugins, and navigation.
- `docs/index.md`: task-oriented documentation homepage.
- `docs/OVERVIEW.md`: symlink to the root README for the project overview.
- `docs/*.md`: hand-written docs pages and generated references.
- `docs/notebooks/`: executed example notebooks.
- `scripts/`: docs generation scripts.
