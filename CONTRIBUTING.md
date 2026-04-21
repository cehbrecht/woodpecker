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
woodpecker check . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001 --dry-run
woodpecker fix . --select CMIP6D_0001 --force-apply
woodpecker fix --plan plan.json
```

Notes:
- In write mode, JSON output exits with status 1 if any persistence operation fails.
- `--force-apply` bypasses `matches()` prefiltering and requires explicit fix selection (`--select` or plan-provided codes).

## Adding or Updating Fixes

Fix author contract (minimal):
- metadata: `code`, `name`, `description`, `categories`, `priority`, `dataset`
- methods: `matches(dataset)`, `check(dataset) -> list[str]`, `apply(dataset, dry_run=True) -> bool`
- reference template: `woodpecker/fixes/fix_template.py`

Performance guidance:
- keep `matches()` fast and deterministic (metadata-only checks where possible)
- put expensive validation logic in `check()` and expensive mutation logic in `apply()`

Use existing fixes as examples and keep behavior deterministic.

## Fix Plan Files

Woodpecker uses one schema for both plan files and plan stores:

- `FixPlanDocument`: top-level container with `plans: [...]`.
- `FixPlan`: plan entry with `id`, optional `namespace`, `description`, optional `match`, ordered `fixes`, optional `links`.
- `FixRef`: each step entry (`fix`, optional `options`, optional `links`).

Common `FixPlan` fields:

- `id`: optional plan identifier.
- `namespace`: optional local-ID namespace prefix.
- `description`: optional human-readable description.
- `match.attrs`: key/value attribute matcher for dataset metadata.
- `match.path_patterns`: optional fnmatch-style path patterns.
- `fixes`: ordered list of fix refs. Each item can be a string or object with `fix` and `options`.
- `links`: optional list of `{rel, href, title?}` references (errata/issues/docs).

Minimal `FixPlanDocument` example:

```json
{
  "plans": [
    {
      "id": "atlas-basic",
      "namespace": "ATLAS",
      "description": "ATLAS plan",
      "match": {
        "path_patterns": ["*atlas*.nc"]
      },
      "fixes": [
        "0001",
        {"fix": "COMMON.0002"}
      ]
    },
    {
      "id": "esa-cci-zarr",
      "namespace": "CMIP7",
      "description": "Default ESA CCI zarr plan",
      "match": {
        "path_patterns": ["*ESACCI-WATERVAPOUR-*.zarr"]
      },
      "fixes": [
        "0003",
        {"fix": "COMMON.0002"}
      ]
    }
  ]
}
```

Single-plan shorthand is also supported by the loader: a top-level object
with `fixes` is treated as a one-plan document.

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

findings = woodpecker.check(ds, codes=["ATLAS_0001"])
stats = woodpecker.fix(ds, codes=["ATLAS_0001"], write=True)

# Fix plan helpers
findings_plan = woodpecker.check_plan("plan.json", inputs=["./data"])
stats_plan = woodpecker.fix_plan("plan.json", inputs=ds, write=True)

# Path input works as well
findings_from_paths = woodpecker.check(["./data"], codes=["ATLAS_0001"])
```
