# Contributing to Woodpecker

Thanks for contributing.

## Development Setup

Recommended:

```bash
conda env create -f environment.yml
conda activate woodpecker
make install
```

Optional uv workflow:

```bash
conda env create -f environment.yml
conda activate woodpecker
make install-uv
```

Pip-only setup:

```bash
pip install -e .
```

Optional I/O extras:

```bash
pip install -e ".[io]"       # NetCDF backends (netCDF4/h5netcdf/scipy)
pip install -e ".[zarr]"     # Zarr backend support
pip install -e ".[io,zarr]"  # both
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
woodpecker fix --workflow workflow.json
```

Notes:
- In write mode, JSON output exits with status 1 if any persistence operation fails.
- `--force-apply` bypasses `matches()` prefiltering and requires explicit fix selection (`--select` or workflow-provided codes).

## Adding or Updating Fixes

Fix author contract (minimal):
- metadata: `code`, `name`, `description`, `categories`, `priority`, `dataset`
- methods: `matches(dataset)`, `check(dataset) -> list[str]`, `apply(dataset, dry_run=True) -> bool`
- reference template: `woodpecker/fixes/fix_template.py`

Performance guidance:
- keep `matches()` fast and deterministic (metadata-only checks where possible)
- put expensive validation logic in `check()` and expensive mutation logic in `apply()`

Use existing fixes as examples and keep behavior deterministic.

## Workflow Files

Minimal workflow example:

```json
{
  "version": 1,
  "inputs": ["./data"],
  "codes": ["CMIP6_0001", "ATLAS_0001"],
  "fixes": {
    "CMIP6_0001": {"marker_attr": "custom_marker", "marker_value": "ok"},
    "ATLAS_0001": {}
  },
  "output_format": "netcdf",
  "requires": ["io"]
}
```

Selector + ordered steps example:

```json
{
  "datasets": {
    "*cmip6*.nc": [
      {"code": "CMIP6_0001", "options": {"message": "cmip6 check path"}},
      {"code": "ATLAS_0001"}
    ]
  }
}
```

CLI options override workflow defaults when both are provided.

## Python API (for contributors)

```python
import xarray as xr
import woodpecker

ds = xr.Dataset(attrs={"source_name": "cmip6_bad.nc"})

findings = woodpecker.check(ds, codes=["CMIP6D_0001"])
stats = woodpecker.fix(ds, codes=["CMIP6D_0001"], write=True)

# Workflow helpers
findings_wf = woodpecker.check_workflow("workflow.json", inputs=["./data"])
stats_wf = woodpecker.fix_workflow("workflow.json", inputs=ds, write=True)

# Path input works as well
findings_from_paths = woodpecker.check(["./data"], codes=["CMIP6D_0001"])
```
