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
woodpecker fix --plan plan.json
```

Notes:
- In write mode, JSON output exits with status 1 if any persistence operation fails.
- `--force-apply` bypasses `matches()` prefiltering and requires explicit fix selection (`--select` or plan-provided identifiers).

## Core Concepts

### Fix

A fix is an executable rule that checks and optionally repairs a dataset issue.
Fixes are registered in the `FixRegistry` and discovered at runtime, including
through plugin entry points.

## Adding or Updating Fixes

Fix author contract (minimal):
- metadata: `prefix`, `suffix`, `name`, `description`, `categories`, `priority`, `dataset`
- methods: `matches(dataset)`, `check(dataset) -> list[str]`, `apply(dataset, dry_run=True) -> bool`

Performance guidance:
- keep `matches()` fast and deterministic (metadata-only checks where possible)
- put expensive validation logic in `check()` and expensive mutation logic in `apply()`

Use existing fixes as examples and keep behavior deterministic.

### Fix Identifiers

Every fix and plan has a stable, scoped identifier:

- `prefix`: owning namespace, for example `cmip6_decadal`, `atlas`, `woodpecker`
- `suffix`: snake_case identifier unique within that prefix
- id: `<prefix>.<suffix>`

Examples:

- `cmip6_decadal.time_metadata`
- `atlas.encoding_cleanup`
- `woodpecker.normalize_tas_units_to_kelvin`

Ids are stored in plans, used on the CLI, and resolved through the identifier
resolver. Use full ids (`prefix.suffix`) in plans and examples.

Aliases are additional suffix names. They resolve to the same id and do not
change the prefix.

Identifier defaults are derived automatically:

- `prefix` defaults to the plugin/package namespace (core fixes use `woodpecker`)
- `suffix` defaults to a snake_case value derived from the fix class name

Both values can be set explicitly on the fix class to override these defaults.

Fix classes declare identifiers as class attributes:

```python
class TimeMetadataFix(Fix):
  prefix = "cmip6_decadal"
  suffix = "time_metadata"
```

The registry validates these and derives:

```python
id = "cmip6_decadal.time_metadata"
```

## Fix Plan Files

Woodpecker uses one schema for both plan files and plan stores:

- `FixPlanDocument`: top-level container with `plans: [...]`.
- `FixPlan`: plan entry with `id`, `description`, optional `match`, ordered `steps`, optional `links`.
- `FixRef`: each step entry (`id`, optional `options`, optional `links`).

Common `FixPlan` fields:

- `id`: plan identifier, for example `atlas.basic`.
- `description`: optional human-readable description.
- `match.attrs`: key/value attribute matcher for dataset metadata.
- `match.path_patterns`: optional fnmatch-style path patterns.
- `steps`: ordered list of fix refs. Each item can be a string id or object with `id` and `options`.
- `links`: optional list of `{rel, href, title?}` references (errata/issues/docs).

Minimal `FixPlanDocument` example:

```json
{
  "plans": [
    {
      "id": "atlas.basic",
      "description": "ATLAS plan",
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
      "description": "Default ESA CCI zarr plan",
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

Single-plan shorthand is also supported by the loader: a top-level object
with `steps` is treated as a one-plan document.

CLI override rule:

- Explicit CLI options (for example `--select`, `--dataset`, `--category`) take precedence over plan-derived defaults.

Load and run from file:

```bash
woodpecker check --plan plan.json
woodpecker fix --plan plan.json --dry-run
```

## Fix Plan Stores

A fix plan store is a lookup layer that returns matching `FixPlan`s for a
dataset. Plans can be retrieved by id or alias.

Current backends:

- JSON
- DuckDB

Plans are accessed through the CLI:

- `--store`: backend type (`json` or `duckdb`, default: `json`)
- `--plan`: store location
- `--plan-id`: optionally select a specific plan by id

Examples:

```bash
woodpecker check --store json --plan plans.json
woodpecker check --store duckdb --plan plans.duckdb
woodpecker fix --plan plans.json --plan-id atlas.encoding_cleanup_suite
woodpecker list-plans --store duckdb --plan plans.duckdb --format json
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
dependencies = ["woodpecker>=0.2.0"]

[project.entry-points."woodpecker.plugins"]
example = "woodpecker_example_plugin"
```

Minimal plugin fix:

```python
from woodpecker.fixes.registry import Fix, register_fix

@register_fix
class ExternalDemoFix(Fix):
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

findings = woodpecker.check(ds, identifiers=["atlas.encoding_cleanup"])
assert findings.fix_ids

result = woodpecker.fix(ds, identifiers=["atlas.encoding_cleanup"], write=True)
assert result.changed >= 0

# Fix plan helpers
findings_plan = woodpecker.check_plan("plan.json", inputs=["./data"])
result_plan = woodpecker.fix_plan("plan.json", inputs=ds, write=True)

# Path input works as well
findings_from_paths = woodpecker.check(["./data"], identifiers=["atlas.encoding_cleanup"])
```

## Tests And Synthetic Data

Prefer public API integration tests for end-to-end behavior. They should read
like executable examples and use synthetic climate datasets where possible.

Useful references:

- `tests/integration/README.md`: integration test intent and style.
- `woodpecker/testing/README.md`: synthetic climate dataset factories.
- `tests/test_testing_factory.py`: expected shape and determinism of fixtures.

Keep technical details close to the module that owns them. The root README
should stay as a thin project overview.
