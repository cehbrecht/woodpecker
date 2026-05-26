# Woodpecker

**Small, precise fixes for climate data.**

[![CI](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml)
[![Docs](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml)
[![Online Docs](https://img.shields.io/badge/docs-online-blue)](https://cehbrecht.github.io/woodpecker/)
[![nbviewer](https://img.shields.io/badge/notebooks-nbviewer-orange)](https://nbviewer.org/github/cehbrecht/woodpecker/tree/main/docs/notebooks/)
[![License](https://img.shields.io/github/license/cehbrecht/woodpecker)](https://github.com/cehbrecht/woodpecker/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://github.com/cehbrecht/woodpecker/blob/main/pyproject.toml)

Woodpecker is a lightweight, code-based catalog of common dataset fixes for
climate processing. It brings repair scripts, workarounds, plugins, and fix
plans under one API for checking, applying, composing, and discovering climate
data fixes.

Like a woodpecker finding bugs in a tree, Woodpecker looks for known data
issues and applies focused repairs before they spread through a workflow.

Dataset-specific fix families are provided as plugins.

## Documentation

The MkDocs site is the main documentation entry point:

- [Home](https://cehbrecht.github.io/woodpecker/)
- [Overview](https://cehbrecht.github.io/woodpecker/OVERVIEW/)
- [Concepts](https://cehbrecht.github.io/woodpecker/concepts/)
- [Discovered Fix Plans](https://cehbrecht.github.io/woodpecker/plans/)
- [CLI](https://cehbrecht.github.io/woodpecker/cli/)
- [Plugins](https://cehbrecht.github.io/woodpecker/plugins/)
- [Examples](https://cehbrecht.github.io/woodpecker/examples/)
- [Generated Fixes Reference](https://cehbrecht.github.io/woodpecker/FIXES/)
- [Generated Fix Plans Reference](https://cehbrecht.github.io/woodpecker/FIX_PLANS/)
- [Interactive Fix Browser](https://cehbrecht.github.io/woodpecker/fixes/)
- [Contributing Guide](https://cehbrecht.github.io/woodpecker/CONTRIBUTING_GUIDE/)

The source pages live in `docs/` and are wired through `mkdocs.yml`.

## Quick Start

```bash
conda env create -f environment.yml
conda activate woodpecker
make dev
woodpecker list-fixes
woodpecker list-plans
```

Run a discovered fix plan:

```python
import woodpecker

plan = woodpecker.plan.get("cmip6.core_units")
findings = woodpecker.plan.check(dataset, plan)

if findings:
    woodpecker.plan.fix(dataset, plan, dry_run=False)
```

Run a known fix directly:

```python
import woodpecker

findings = woodpecker.check(
    dataset,
    fixes="woodpecker.normalize_tas_units_to_kelvin",
)
```

From the command line:

```bash
woodpecker check ./data --plan-id cmip6.core_units
woodpecker fix ./data --select cmip6_decadal.time_metadata --dry-run
```

## Local Docs

Build the generated catalogs, interactive fixes page, notebooks, and MkDocs
site:

```bash
make docs
```

Serve the docs locally:

```bash
make docs-serve
```

The docs extras can also be installed directly:

```bash
pip install -e ".[docs]"
```

## Project Map

- `woodpecker/`: core package, public API, CLI, stores, fix plans, and fixes.
- `plugins/`: bundled dataset-family plugins for Atlas, CMIP6, CMIP6-decadal,
  CMIP7, and xMIP.
- `docs/`: MkDocs source pages, generated catalogs, generated interactive page,
  and executed notebooks.
- `tests/`: unit and integration coverage.
- `scripts/`: documentation catalog and page generators.

## Development

Contributor setup, authoring rules, plugin guidance, and testing conventions
live in the
[Contributing Guide](https://cehbrecht.github.io/woodpecker/CONTRIBUTING_GUIDE/).

Useful local commands:

```bash
make format
make lint
make test
make docs
```

## License

Woodpecker is licensed under the terms in the
[project license](https://github.com/cehbrecht/woodpecker/blob/main/LICENSE).
