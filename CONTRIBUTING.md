# Contributing to Woodpecker

Thanks for contributing.

## Development Setup

Recommended:

```bash
conda env create -f environment.yml
conda activate woodpecker
make dev
```

Optional uv workflow:

```bash
conda env create -f environment.yml
conda activate woodpecker
make dev-uv
```

Pip-only setup:

```bash
pip install -e .
```

Optional extras:

```bash
pip install -e ".[full]"     # runtime optional backends (NetCDF/Zarr/DuckDB)
pip install -e ".[docs]"     # docs build toolchain (mkdocs/material/jinja2)
pip install -e ".[dev,full]" # common local test setup with optional backends
```

## Common Development Commands

```bash
make format      # run Ruff formatter
make lint        # run Ruff lint checks
make lint-fix    # auto-fix Ruff lint issues
make test        # run pytest test suite
make docs        # generate docs artifacts + strict mkdocs build
make docs-serve  # generate docs artifacts + run mkdocs serve
```

## Useful CLI Checks

```bash
woodpecker io-status
woodpecker check . --select cmip6_decadal.time_metadata
woodpecker fix . --select cmip6_decadal.time_metadata
woodpecker fix . --select cmip6_decadal.time_metadata --dry-run
woodpecker fix . --select cmip6_decadal.time_metadata --force-apply
woodpecker check . --select woodpecker.normalize_tas_units_to_kelvin --strict-io
woodpecker fix . --select woodpecker.normalize_tas_units_to_kelvin --strict-io
woodpecker fix --recipe recipe.json
```

Notes:
- In write mode, JSON output exits with status 1 if any persistence operation fails.
- `--force-apply` bypasses `matches()` prefiltering and requires explicit fix selection (`--select` or recipe-provided identifiers).
- `--strict-io` changes input loading to fail fast instead of warning and falling back when a backend is unavailable or a read fails.

## Core Concepts

### Fix Function

A fix function is an executable rule that checks and optionally repairs a
dataset issue. Fix functions are registered in the `FixFunctionRegistry` and discovered
at runtime, including through plugin entry points.

### Design Overview

Woodpecker separates executable fix functions from user-facing fixes and fix
recipes.

- A **fix function** is implementation code and can be selected directly via API/CLI.
- A **fix** is a fix function plus optional runtime options.
- A **recipe** is a user workflow with ordered steps, options, matching rules, and links.
- A **recipe document** serializes one or more recipes in JSON or YAML.
- A **recipe store** is a query backend for recipes (list/load/save/get-by-id/match).
- `RecipeLoader` coordinates recipe documents from explicit paths,
  `WOODPECKER_RECIPE_PATH`, user config directories, system directories,
  core package resources, and installed plugin `recipes/` resources.
- `AutoRecipeStore` is the read-only store that exposes registered fix functions as implicit one-step recipes.
- A **recipe catalog** aggregates one or more recipe sources behind one surface.

The current `RecipeCatalog` prototype can list recipes, find matching recipes,
resolve ids and aliases, and deduplicate by recipe id using source order.

Default plugin prefix behavior:

- plugin fix function prefixes are derived from package name by removing `woodpecker_`
  and `_plugin` when applicable.

Identifier spaces are intentionally separate:

- fix lookup uses `fix_id`
- recipe lookup uses `recipe_id`

Use these labels consistently in APIs and docs to avoid ambiguity.

Recipe matching is extensible and currently AND-based across available rule types:

- `attrs`: exact metadata key/value constraints
- `dataset_id_patterns`: wildcard patterns matched against dataset identity metadata
- `path_patterns`: wildcard patterns matched against input path

Discovery direction:

- Prefer explicit recipes for user workflows because they carry matching,
  options, links, and step ordering.
- Auto-store one-step recipes from registered fix functions remain useful for lightweight
  discovery and early development.
- Plugins may ship only fix functions; if they later ship recipes, those recipes should be
  placed in the package `recipes/` resource directory and reference plugin fixes
  by normal `prefix.suffix` ids.

## Adding or Updating Fix Functions

Fix function author contract (minimal):
- metadata: `prefix`, `suffix`, `name`, `description`, `categories`, `dataset`
- methods: `matches(dataset)`, `check(dataset) -> list[str]`, `apply(dataset, dry_run=True) -> bool`

`priority` is optional. Use a non-negative integer when the fix function should
participate in default discovery ordering. The default is `-1`, meaning
unprioritized; unprioritized fix functions sort after explicitly prioritized
fix functions.

Performance guidance:
- keep `matches()` fast and deterministic (metadata-only checks where possible)
- put expensive validation logic in `check()` and expensive mutation logic in `apply()`

Use existing fixes as examples and keep behavior deterministic.

### Fix Function Identifiers

Every fix function and recipe has a stable, scoped identifier:

- `prefix`: owning namespace, for example `cmip6_decadal`, `atlas`, `woodpecker`
- `suffix`: snake_case identifier unique within that prefix
- id: `<prefix>.<suffix>`

Examples:

- `cmip6_decadal.time_metadata`
- `atlas.encoding_cleanup`
- `woodpecker.normalize_tas_units_to_kelvin`

Ids are stored in recipes, used on the CLI, and resolved through the identifier
resolver. Use full ids (`prefix.suffix`) in recipes and examples.

Aliases are additional suffix names. They resolve to the same id and do not
change the prefix.

Identifier defaults are derived automatically:

- `prefix` defaults to the plugin/package namespace (core fixes use `woodpecker`)
- `suffix` defaults to a snake_case value derived from the fix class name

Both values can be set explicitly on the fix function class to override these defaults.

Fix function classes declare identifiers as class attributes:

```python
class TimeMetadata(FixFunction):
    prefix = "cmip6_decadal"
    suffix = "time_metadata"
```

The registry validates these and derives:

```python
id = "cmip6_decadal.time_metadata"
```

## Recipe Files

Woodpecker uses one schema for both recipe files and recipe stores:

- `RecipeDocument`: top-level container with `recipes: [...]`.
- `Recipe`: recipe entry with `id`, `description`, optional `match`, ordered `steps`, optional `links`.
- `FixRef`: each step entry (`id`, optional `options`, optional `links`).

Common `Recipe` fields:

- `id`: recipe identifier, for example `atlas.basic`.
- `description`: optional human-readable description.
- `match.attrs`: key/value attribute matcher for dataset metadata.
- `match.path_patterns`: optional fnmatch-style path patterns.
- `steps`: ordered list of fix refs. Each item can be a string id or object with `id` and `options`.
- `links`: optional list of `{rel, href, title?}` references (errata/issues/docs).

Minimal `RecipeDocument` example:

```json
{
  "recipes": [
    {
      "id": "atlas.basic",
      "description": "ATLAS recipe",
      "match": {
        "path_patterns": ["*atlas*.nc"]
      },
      "steps": [
        "atlas.encoding_cleanup",
        {"id": "woodpecker.ensure_latitude_is_increasing"}
      ]
    },
    {
      "id": "cmip7.esa_cci_zarr",
      "description": "Default ESA CCI zarr recipe",
      "match": {
        "path_patterns": ["*ESACCI-WATERVAPOUR-*.zarr"]
      },
      "steps": [
        "cmip7.configurable_reformat_bridge",
        {"id": "woodpecker.ensure_latitude_is_increasing"}
      ]
    }
  ]
}
```

Python authoring helpers can generate the same document schema:

```python
from woodpecker.recipes import fix, recipe

atlas_basic = (
    recipe("atlas.basic", fix("atlas.encoding_cleanup"))
    .match(path_patterns=["*atlas*.nc"])
)

atlas_basic.to_yaml("atlas_basic_recipe.yaml")
```

Single-recipe shorthand is also supported by the loader: a top-level object
with `steps` is treated as a one-recipe document.

CLI override rule:

- Explicit CLI options (for example `--select`, `--dataset`, `--category`) take precedence over recipe-derived defaults.

Load and run from file:

```bash
woodpecker check --recipe recipe.json
woodpecker fix --recipe recipe.json --dry-run
```

## Recipe Stores

A recipe store is a lookup layer that returns matching `Recipe`s for a dataset.
Recipes can be retrieved by id or alias.

Current backends:

- Catalog (`RecipeLoader` discovery, read-only)
- JSON
- DuckDB
- Auto (`AutoRecipeStore`, read-only)

Recipes are accessed through the CLI:

- `--store`: backend type (`catalog`, `json`, `duckdb`, or `auto`; default: `json` for check/fix)
- `--recipe`: store location or an extra catalog file/directory
- `--recipe-id`: optionally select a specific recipe by id

When `--store catalog` or `--store auto` is used, `--recipe` is not required.
`woodpecker check . --recipe-id ...` also uses the discovered catalog when no
explicit `--recipe` is provided.

Examples:

```bash
woodpecker check --store json --recipe recipes.json
woodpecker check --recipe-id cmip6.core_units
woodpecker list-recipes
woodpecker check --store duckdb --recipe recipes.duckdb
woodpecker check --store auto --recipe-id woodpecker.normalize_tas_units_to_kelvin
woodpecker fix --recipe recipes.json --recipe-id atlas.encoding_cleanup_suite
woodpecker list-recipes --store duckdb --recipe recipes.duckdb --format json
```

## Plugins

Core Woodpecker provides fixes that apply across datasets. Dataset-specific
fixes live in plugins discovered via the `woodpecker.plugins` entry point group.

Bundled plugin packages live under `plugins/`:

| Plugin package                    | Namespace prefix |
| --------------------------------- | ---------------- |
| `woodpecker-atlas-plugin`         | `atlas`          |
| `woodpecker-cmip6-plugin`         | `cmip6`          |
| `woodpecker-cmip6-decadal-plugin` | `cmip6_decadal`  |
| `woodpecker-cmip7-plugin`         | `cmip7`          |
| `woodpecker-xmip-plugin`          | `xmip`           |

Install bundled plugins during development:

```bash
make install-plugins
make dev
```

Minimal plugin entry point:

```toml
[project]
name = "woodpecker-example-plugin"
version = "0.1.0"
dependencies = ["woodpecker>=0.4,<0.5"]

[project.entry-points."woodpecker.plugins"]
example = "woodpecker_example_plugin"
```

Minimal plugin fix function:

```python
from woodpecker.fixes.registry import FixFunction, register_fix_function

@register_fix_function
class ExternalDemo(FixFunction):
    prefix = "example"
    suffix = "demo"
    name = "External demo fix"
    description = "A minimal plugin-provided fix."
    categories = ["metadata"]
    priority = 50
    dataset = None

    def check(self, dataset):
        return []

    def apply(self, dataset, dry_run=True):
        return False
```

Derived canonical id:

```text
example.demo
```

## Python API (for contributors)

```python
import xarray as xr
import woodpecker

ds = xr.Dataset(attrs={"source_name": "atlas_bad.nc"})

findings = woodpecker.check(ds, fixes="atlas.encoding_cleanup")
assert findings.fix_ids

result = woodpecker.fix(ds, fixes="atlas.encoding_cleanup", dry_run=False)
assert result.changed >= 0

# Optional fail-fast I/O behavior
strict_findings = woodpecker.check(ds, fixes="atlas.encoding_cleanup", strict_io=True)
strict_result = woodpecker.fix(ds, fixes="atlas.encoding_cleanup", dry_run=False, strict_io=True)

# Recipe helpers
findings_recipe = woodpecker.recipe.check(["./data"], "recipe.json")
result_recipe = woodpecker.recipe.fix(ds, "recipe.json", dry_run=False)

# Path input works as well
findings_from_paths = woodpecker.check(
    ["./data"],
    fixes="atlas.encoding_cleanup",
)
```

## Tests And Synthetic Data

Prefer public API integration tests for end-to-end behavior. They should read
like executable examples and use synthetic climate datasets where possible.

Interim plugin-testing policy (current state):

- Keep cross-plugin integration tests in core under `tests/integration` until
  plugin interfaces and recipe contracts are stable.
- Keep plugin-local unit tests in each plugin package under
  `plugins/*/tests`.
- Revisit moving integration coverage into plugin repositories when plugin
  APIs are versioned, compatibility guarantees are documented, and CI can run
  shared contract suites across repositories.

Useful references:

- `tests/integration/README.md`: integration test intent and style.
- `woodpecker/testing/README.md`: synthetic climate dataset factories.
- `tests/test_testing_factory.py`: expected shape and determinism of fixtures.

Keep technical details close to the module that owns them. The root README
should stay as a thin project overview.
