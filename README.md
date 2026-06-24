# Woodpecker

**Small, precise fixes for climate data.**

[![CI](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml)
[![Docs](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml)
[![Online Docs](https://img.shields.io/badge/docs-online-blue)](https://cehbrecht.github.io/woodpecker/)
[![License](https://img.shields.io/github/license/cehbrecht/woodpecker)](https://github.com/cehbrecht/woodpecker/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://github.com/cehbrecht/woodpecker/blob/main/pyproject.toml)

Woodpecker checks and applies known climate-data fixes through a small Python
API, CLI, and recipe system. Use it when a dataset needs a documented repair
before it enters a larger processing workflow.

```mermaid
flowchart LR
    D["Dataset"] --> C["check"]
    C --> F["findings"]
    F --> R["recipe or fix"]
    R --> P["dry-run preview"]
    P --> A["apply"]
```

## Quick Start

```bash
conda env create -f environment.yml
conda activate woodpecker
make dev
woodpecker list-recipes
```

Run a discovered recipe:

```python
import woodpecker

recipe = woodpecker.recipe.get("cmip6.core_units")
findings = woodpecker.recipe.check(dataset, recipe)

if findings:
    woodpecker.recipe.fix(dataset, recipe, dry_run=True).preview
    woodpecker.recipe.fix(dataset, recipe, dry_run=False)
```

From the command line:

```bash
woodpecker check ./data --recipe-id cmip6.core_units
woodpecker fix ./data --recipe-id cmip6.core_units --dry-run
```

## Docs

- [Full docs](https://cehbrecht.github.io/woodpecker/)
- [Concepts](https://cehbrecht.github.io/woodpecker/concepts/)
- [Recipes](https://cehbrecht.github.io/woodpecker/recipes/)
- [CLI](https://cehbrecht.github.io/woodpecker/cli/)
- [Contributing](https://cehbrecht.github.io/woodpecker/CONTRIBUTING_GUIDE/)

## Project Map

- `woodpecker/`: core API, CLI, recipes, fixes, stores, and results.
- `plugins/`: bundled dataset-family plugins.
- `docs/`: MkDocs pages and generated references.
- `tests/`: unit and integration tests.
- `scripts/`: docs and catalog generators.

## Development

```bash
make format
make lint
make test
make docs
```

Woodpecker is licensed under the terms in [LICENSE](LICENSE).
