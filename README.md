# Woodpecker

[![CI](https://github.com/macpingu/woodpecker/actions/workflows/ci.yml/badge.svg)](https://github.com/macpingu/woodpecker/actions/workflows/ci.yml)
[![Docs](https://github.com/macpingu/woodpecker/actions/workflows/docs.yml/badge.svg)](https://github.com/macpingu/woodpecker/actions/workflows/docs.yml)

**Woodpeckers** “fix” trees by pecking out small problem spots — exactly like this tool applies targeted fixes to datasets.

Woodpecker is a small, **code-driven catalog of dataset fixes** for climate data workflows (CDS/WPS, CMIP pipelines, etc.).
Each fix has a **stable short code** (e.g. `CMIP6D_0001`) so external services (like an ESGF errata UI) can reference it directly.

The design is inspired by Ruff: fast, rule-based checks with optional targeted auto-fixes.

## What This Demo Includes

- `woodpecker.fixes.registry.FixRegistry`: in-memory registry (simple today, extensible tomorrow)
- Built-in fix families grouped by domain subpackage (`common`, `cmip6_decadal`, `cmip7`, `atlas`, ...)
- `woodpecker` CLI:
  - `woodpecker list-fixes`
  - `woodpecker list-fixes --format md|json`
  - `woodpecker check <path>`
  - `woodpecker fix <path>`
- Documentation generation:
  - `docs/FIXES.md` (Markdown catalog)
  - `docs/FIXES.json` (machine-readable)
  - `docs/fixes.html` (small interactive page with anchors, ideal for linking `#CMIP6D_0001`)
- MkDocs site (Material theme) + GitHub Pages workflow

## Quickstart

Conda environment (recommended):

```bash
conda env create -f environment.yml
conda activate woodpecker
make install
make list-fixes
```

Main requirements are tracked in `pyproject.toml`. Use `make` after creating/activating the conda environment (the Makefile intentionally does not manage conda itself).

Conda + uv workflow (optional, faster installer):

```bash
conda env create -f environment.yml
conda activate woodpecker
make install-uv
make dev-uv
```

Default `make install`/`make dev` still use `pip`.

Pip-only setup (no conda):

```bash
pip install -e .
woodpecker list-fixes
```

Optional I/O extras (recommended when you need file backends):

```bash
pip install -e ".[io]"       # NetCDF backends (netCDF4/h5netcdf/scipy)
pip install -e ".[zarr]"     # Zarr backend support
pip install -e ".[io,zarr]"  # both
```

Note for contributors: backend integration tests (NetCDF/Zarr round-trips) run
when corresponding backends are installed, and are skipped in minimal environments.

If an unavailable backend is requested (for example Zarr without `.[zarr]`),
Woodpecker fails safely with a warning and reports persistence failure in fix stats.

## Usage

How it works (current demo): `discover fixes -> check findings -> apply selected fixes`.

Woodpecker stays a thin layer: fix families can carry different requirements, while workflows provide a shared way to select and run fix sets.

Common tasks:

```bash
make install     # editable install
make install-uv  # editable install via uv
make dev         # editable install + docs + dev + io + zarr extras
make dev-uv      # same as make dev via uv
make format      # run Ruff formatter
make lint        # run Ruff lint checks
make lint-fix    # auto-fix Ruff lint issues
make check       # run checks (defaults to current directory)
make test        # run pytest test suite
make docs        # generate docs artifacts + strict mkdocs build
make docs-serve  # generate docs artifacts + run mkdocs serve
```

Lint-style workflow (Ruff-like):

```bash
woodpecker io-status
woodpecker io-status --format json
woodpecker check /path/to/netcdf/or/folder
woodpecker check . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001 --dry-run
woodpecker fix . --select CMIP6D_0001 --output-format zarr
woodpecker check --workflow workflow.json
woodpecker fix --workflow workflow.json
```

Write mode reports both fix changes and persistence status (`persisted` vs `failed to persist`) in text and JSON output.
When `--format json` is used in write mode (default), Woodpecker exits with status `1` if any persistence operation fails.

Selected fix codes are validated strictly: unknown `--select` codes fail fast with a clear error (same behavior in the Python API).

Workflow file (building block):

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

CLI options override workflow defaults when both are provided.
Use `fixes` to pass per-fix options while keeping Woodpecker itself generic.

Selector + ordered steps variant:

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

This lets workflows choose a fix sequence per dataset pattern while still reusing common Python fix implementations.

ESA CCI as workflow usage of CMIP7 fixes:

```json
{
  "dataset": "CMIP7",
  "datasets": {
    "*ESA_CCI*.nc": {
      "steps": [
        {"code": "COMMON_0001"},
        {"code": "CMIP7_0001"},
        {"code": "CMIP7_0002"},
        {"code": "COMMON_0002"},
        {"code": "COMMON_0003"}
      ]
    }
  }
}
```

See the ready-to-use example at `workflows/examples/esa_cci_to_cmip7.json`.

Library API (paths + xarray objects):

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

Fix author contract (minimal):
- metadata: `code`, `name`, `description`, `categories`, `priority`, `dataset`
- methods: `matches(dataset)`, `check(dataset) -> list[str]`, `apply(dataset, dry_run=True) -> bool`
- reference template: `woodpecker/fixes/fix_template.py`

Input adapters (path/folder/xarray/zarr) are responsible for turning sources
into xarray objects before running fixes.

## Example

```bash
touch cmip6_case.nc
woodpecker check . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001 --dry-run
# dummy fix marks datasets in-memory/on write path (no filename renaming in this phase)
```

## Design Direction

Woodpecker intentionally stays simple and “human-countable”, but the design leaves room to grow:

- **Pydantic models**: Pydantic is part of core dependencies and can be used for stronger fix schema validation.
  See `woodpecker/fixes/fix_template.py`.
- **Pluggy (optional)**: If you want third-party packages to register fixes via entry points (like pytest plugins),
  the registry API can be backed by pluggy later with minimal changes to CLI/docs.
- **Scaling docs/UI**: `FIXES.json` is a stable export format that can later feed search indexes or richer UIs.

## What This Demo Covers

- file-level demo logic is intentionally lightweight (no heavy real-world NetCDF transforms yet)
- checks/fixes focus on deterministic, explainable behavior for design discussions
- includes prototype-inspired `COMMON_0001` fix (tas/temp Celsius -> Kelvin) and CMIP7-specific wrappers (`CMIP7_0001`, `CMIP7_0002`)

## Next Steps

- add real NetCDF variable/attribute transformations per fix code
- extend reporting (per-file summary, grouped findings, machine-readable outputs)

## GitHub Pages

This repo includes a workflow that builds and deploys the MkDocs site to GitHub Pages on pushes that touch fixes/docs/scripts.
After enabling GitHub Pages (Settings → Pages), your fix codes become clickable URLs (e.g. `.../fixes.html#CMIP6D_0001`),
which an errata service can reference.
