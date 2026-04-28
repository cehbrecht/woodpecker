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

## Adding or Updating Fixes

Fix author contract (minimal):
- metadata: `local_id`, `name`, `description`, `categories`, `priority`, `dataset`
- methods: `matches(dataset)`, `check(dataset) -> list[str]`, `apply(dataset, dry_run=True) -> bool`

Performance guidance:
- keep `matches()` fast and deterministic (metadata-only checks where possible)
- put expensive validation logic in `check()` and expensive mutation logic in `apply()`

Use existing fixes as examples and keep behavior deterministic.

## Fix Plan Files

Woodpecker uses one schema for both plan files and plan stores:

- `FixPlanDocument`: top-level container with `plans: [...]`.
- `FixPlan`: plan entry with canonical `id`, `description`, optional `match`, ordered `steps`, optional `links`.
- `FixRef`: each step entry (`id`, optional `options`, optional `links`).

Common `FixPlan` fields:

- `id`: canonical plan identifier, for example `atlas.basic`.
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
        "encoding_cleanup",
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
        "configurable_reformat_bridge",
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

## Python API (for contributors)

```python
import xarray as xr
import woodpecker

ds = xr.Dataset(attrs={"source_name": "atlas_bad.nc"})

findings = woodpecker.check(ds, identifiers=["atlas.encoding_cleanup"])
stats = woodpecker.fix(ds, identifiers=["atlas.encoding_cleanup"], write=True)

# Fix plan helpers
findings_plan = woodpecker.check_plan("plan.json", inputs=["./data"])
stats_plan = woodpecker.fix_plan("plan.json", inputs=ds, write=True)

# Path input works as well
findings_from_paths = woodpecker.check(["./data"], identifiers=["atlas.encoding_cleanup"])
```
