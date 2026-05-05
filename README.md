# Woodpecker

[![CI](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml)
[![Docs](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml)
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
- plan stores look up plans for datasets,
- plugins provide dataset-specific fixes for families such as Atlas, CMIP6, and
  CMIP6-decadal.

The public Python API returns structured result objects:

```python
import woodpecker
from woodpecker.testing import make_cmip6

dataset = make_cmip6(overrides={"units": "degC"})

findings = woodpecker.check(
    dataset,
    identifiers=["woodpecker.normalize_tas_units_to_kelvin"],
)

if findings.has_findings:
    result = woodpecker.fix(
        dataset,
        identifiers=findings.fix_ids,
        write=True,
    )
    assert result.has_changes
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
woodpecker fix . --select cmip6_decadal.time_metadata --dry-run
woodpecker fix . --select cmip6_decadal.time_metadata
```

Using a plan file:

```bash
woodpecker check --plan examples/fix-plans/atlas.json
woodpecker fix --plan examples/fix-plans/atlas.json --dry-run
woodpecker list-plans --plan examples/fix-plans/atlas.json
```

## Built-In And Bundled Fixes

Core Woodpecker provides fixes that apply across dataset families.

The repository also ships local plugins under `plugins/`:

| Plugin package                    | Namespace prefix |
| --------------------------------- | ---------------- |
| `woodpecker-atlas-plugin`         | `atlas`          |
| `woodpecker-cmip6-plugin`         | `cmip6`          |
| `woodpecker-cmip6-decadal-plugin` | `cmip6_decadal`  |
| `woodpecker-cmip7-plugin`         | `cmip7`          |

## Synthetic Test Data

`woodpecker.testing` provides small deterministic synthetic climate datasets for
tests, examples, docs, and CI:

- `make_cmip6()`
- `make_cmip6_decadal()`
- `make_atlas()`
- `make_cordex()`

See `woodpecker/testing/README.md` for usage details.

## Development

Contributor and developer details live in `CONTRIBUTING.md`.

Useful starting points:

- `CONTRIBUTING.md` for setup, fix authoring, plans, plugins, and test guidance.
- `tests/integration/README.md` for end-to-end public API integration tests.
- `woodpecker/testing/README.md` for synthetic climate fixture usage.
- `examples/fix-plans/` for example plan documents.

## Provenance

Woodpecker writes PROV-JSON provenance for fix runs where configured by the CLI
or runner.
