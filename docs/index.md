# Woodpecker Documentation

Woodpecker checks and applies known climate-data fixes through recipes, direct
fix selection, a Python API, and a CLI.

```mermaid
flowchart LR
    D["Dataset"] --> C["check"]
    C --> F["findings"]
    F --> R["recipe or fix"]
    R --> P["dry-run preview"]
    P --> A["apply"]
```

## Start Here

- [Overview](OVERVIEW.md): what Woodpecker is for and how the pieces fit.
- [Concepts](concepts.md): fixes, recipes, plugins, catalogs, stores, and ids.
- [Recipes](recipes.md): run shared workflows by recipe id.
- [CLI](cli.md): list, check, fix, dry-run, and format results.
- [Plugins](plugins.md): bundled dataset-family fixes and recipes.

## Happy Path

```bash
woodpecker list-recipes
woodpecker check ./data --recipe-id cmip6.core_units
woodpecker fix ./data --recipe-id cmip6.core_units --dry-run
```

## Common Tasks

| Task | Page |
| ---- | ---- |
| Run a known workflow | [Recipes](recipes.md) |
| Choose a fix id directly | [Fix Reference](FIXES.md) |
| Search recipe metadata | [Recipe Reference](recipe-reference.md) |
| Try notebook examples | [Examples](examples.md) |
| Contribute fixes or recipes | [Contributing Guide](CONTRIBUTING_GUIDE.md) |
| Work on the docs site | [Docs Development](docs-development.md) |

## Reference

- [Fix Reference](FIXES.md)
- [Recipe Reference](recipe-reference.md)
- [Interactive Fix Browser](fixes.html)
