# Woodpecker

[![CI](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml)
[![Docs](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml)
[![Online Docs](https://img.shields.io/badge/docs-online-blue)](https://cehbrecht.github.io/woodpecker/)
[![nbviewer](https://img.shields.io/badge/notebooks-nbviewer-orange)](https://nbviewer.org/github/cehbrecht/woodpecker/tree/main/docs/notebooks/)
[![License](https://img.shields.io/github/license/cehbrecht/woodpecker)](https://github.com/cehbrecht/woodpecker/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://github.com/cehbrecht/woodpecker/blob/main/pyproject.toml)

Woodpecker is a lightweight, code-based catalog of common dataset fixes for
climate processing.

It helps detect and apply known repairs consistently across automated climate
data workflows. A dataset may use Celsius instead of Kelvin, contain
inconsistent dimension names, need metadata normalization, or require a
dataset-family-specific cleanup. Woodpecker keeps that fix logic versioned,
testable, and reusable.

Dataset-specific fix families are provided as plugins.

## Purpose

Woodpecker is meant to make dataset cleanup boring and repeatable:

- reuse known climate dataset fixes across workflows,
- keep fix logic versioned and testable,
- apply fixes consistently in automated pipelines,
- extend behavior with project-specific plugins.

## Design

Woodpecker is intentionally small:

- fixes are executable Python rules,
- fixes have stable identifiers such as `woodpecker.ensure_latitude_is_increasing`,
- fix plans describe ordered fix workflows,
- `FixPlanLoader` coordinates discovered plan documents from core, plugins,
  user/system locations, and explicit paths,
- fix-plan stores query plan definitions from JSON/YAML, DuckDB, or auto sources,
- `AutoFixPlanStore` provides read-only, auto-generated one-step plans from registered fixes,
- `FixPlanCatalog` aggregates one or more plan sources behind one lookup surface,
- plugins provide dataset-specific fixes for families such as Atlas, CMIP6, and
  CMIP6-decadal.

Vocabulary:

- **Fix**: an executable rule that checks for one known dataset issue and can
  optionally repair it.
- **FixPlan**: an ordered list of fixes, with optional matching rules and fix
  options, for a dataset family or workflow.
- **FixPlanStore**: a lookup layer that finds matching plans from a source such
  as JSON or DuckDB.
- **FixPlanLoader**: a discovery layer that collects plan documents from
  explicit paths, `WOODPECKER_FIX_PLAN_PATH`, user config directories, system
  directories, core package resources, and installed plugin `plans/` resources.
- **AutoFixPlanStore**: a read-only store that exposes registered fixes as
  implicit one-step plans.
- **FixPlanCatalog**: an aggregate view over one or more plan sources that can
  list plans, resolve ids/aliases, and find matching plans.

Identifier idea (short version):

- every fix and plan has an id in the form `prefix.suffix`
- use full ids (`prefix.suffix`) in plans and examples
- aliases are extra names for the suffix and resolve to the same id
- defaults are automatic: prefix from package/plugin namespace, suffix from class name
- both prefix and suffix can be overridden explicitly

See `CONTRIBUTING.md` for full identifier rules and authoring details.

## Public Python API

Use `woodpecker.check()` and `woodpecker.fix()` when selecting executable fixes
directly:

```python
import woodpecker
from woodpecker.testing import make_cmip6

dataset = make_cmip6(overrides={"units": "degC"})

findings = woodpecker.check(
    dataset,
    fixes="woodpecker.normalize_tas_units_to_kelvin",
)

if findings:
    result = woodpecker.fix(
        dataset,
        fixes=findings.fix_ids,
        dry_run=False,
    )
    assert result
```

Use `woodpecker.plan.check()` and `woodpecker.plan.fix()` when selecting fixes
from a fix plan:

```python
import woodpecker

findings = woodpecker.plan.check(dataset, "plans.yaml")

if findings:
    preview = woodpecker.plan.fix(dataset, "plans.yaml")
    result = woodpecker.plan.fix(dataset, "plans.yaml", dry_run=False)
    assert result
```

Fix plans can also be discovered without hard-coding a path:

```python
findings = woodpecker.plan.check(dataset, None, plan_id="cmip6.core_units")
findings = woodpecker.plan.check(dataset, woodpecker.plan.catalog("xmip.cmip6_preprocessing"))
```

Plan authoring models are available from `woodpecker.fix_plans`:

```python
from woodpecker.fix_plans import DatasetMatcher, FixPlan, FixPlanLoader, FixRef
```

## Quick Start

```bash
conda env create -f environment.yml
conda activate woodpecker
make dev
make list-fixes
```

Optional runtime backends for NetCDF, Zarr, and DuckDB:

```bash
pip install -e ".[full]"
```

Install bundled plugins during development:

```bash
make install-plugins
make dev
```

## CLI Usage

```text
discover fixes -> check datasets -> apply selected fixes
```

Direct fix selection:

```bash
woodpecker list-fixes
woodpecker check . --select cmip6_decadal.time_metadata
woodpecker check . --store auto --plan-id woodpecker.normalize_tas_units_to_kelvin
woodpecker fix . --select cmip6_decadal.time_metadata --dry-run
woodpecker fix . --select cmip6_decadal.time_metadata
```

## Built-In And Bundled Fixes

Core Woodpecker provides fixes that apply across dataset families.

The repository also ships local plugins under `plugins/`:

| Plugin package                    | Prefix |
| --------------------------------- | ---------------- |
| `woodpecker-atlas-plugin`         | `atlas`          |
| `woodpecker-cmip6-plugin`         | `cmip6`          |
| `woodpecker-cmip6-decadal-plugin` | `cmip6_decadal`  |
| `woodpecker-cmip7-plugin`         | `cmip7`          |
| `woodpecker-xmip-plugin`          | `xmip`           |

## Synthetic Test Data

`woodpecker.testing` provides small deterministic synthetic climate datasets for
tests, examples, docs, and CI:

- `make_cmip6()`
- `make_cmip6_decadal()`
- `make_cmip7()`
- `make_atlas()`
- `make_cordex()`

See `woodpecker/testing/README.md` for usage details.

## Notebooks

The `docs/notebooks/` directory contains notebooks that demonstrate the public API
with synthetic datasets, built-in core fixes, and bundled plugin fixes:

- rendered in the online docs: <https://cehbrecht.github.io/woodpecker/>
- listed on the examples page:
  <https://cehbrecht.github.io/woodpecker/examples/>
- viewable as raw notebooks on nbviewer:
  <https://nbviewer.org/github/cehbrecht/woodpecker/tree/main/docs/notebooks/>

```bash
jupyter notebook notebooks/cmip6_core_api_example.ipynb
jupyter notebook notebooks/cmip6_core_fix_plan_example.ipynb
jupyter notebook notebooks/atlas_fix_plan_example.ipynb
jupyter notebook notebooks/esa_cci_fix_plan_example.ipynb
jupyter notebook notebooks/xmip_plugin_demo.ipynb
```

The fix-plan documents used by the plan notebooks are discovered from core and
plugin package resources and are covered by integration tests.

## Development

Contributor and developer details live in `CONTRIBUTING.md`.

Useful starting points:

- `CONTRIBUTING.md` for setup, fix authoring, plans, plugins, and test guidance.
- `tests/integration/README.md` for end-to-end public API integration tests.
- `woodpecker/testing/README.md` for synthetic climate fixture usage.
- `docs/notebooks/` for notebook-based public API examples.

## Provenance

Woodpecker writes PROV-JSON provenance for fix runs where configured by the CLI
or runner.
