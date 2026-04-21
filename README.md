# Woodpecker

[![CI](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml)
[![Docs](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml)
[![License](https://img.shields.io/github/license/cehbrecht/woodpecker)](https://github.com/cehbrecht/woodpecker/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://github.com/cehbrecht/woodpecker/blob/main/pyproject.toml)

Woodpecker is a lightweight, code-based catalog of common dataset fixes for climate processing.

Dataset-specific fix families are provided by external plugins.

Each fix has a local ID plus a canonical ID in `<prefix>.<local_id>` form (for example `CMIP6D.0001`).
Legacy underscore IDs (for example `CMIP6D_0001`) are supported as aliases.

Contributor and developer docs live in `CONTRIBUTING.md`.

## Core Concepts

Woodpecker is built around three simple concepts:

- **Fix**  
  An executable rule that checks and optionally fixes a dataset.  
    Each fix belongs to one namespace prefix and has a stable local ID.

- **FixPlan**  
    A declarative list of plan steps (`fix` + optional `options`) applied in order.

- **FixPlanStore**  
  A lookup layer that returns matching `FixPlan`s for a dataset (currently with JSON and DuckDB backends).

Implementation note:
- A design-stub placeholder for a future Elasticsearch-backed store is in `woodpecker/stores/elasticsearch_store.py`.

### Plan access model

All plans are accessed through a `FixPlanStore`.

- `--store` selects the backend (default: `json`)
- `--plan` provides the location interpreted by that backend
- `--plan-id` optionally selects a specific `FixPlan`

For the default JSON backend, the on-disk format is:

    {
      "plans": [ ... ]
    }

Plan IDs are explicit and stable. Matching (`match.attrs`, `match.path_patterns`) is independent from IDs.

## Quickstart

Conda setup:

    conda env create -f environment.yml
    conda activate woodpecker
    make dev
    make list-fixes

Optional DuckDB support:

    pip install -e ".[full]"

## Usage

Typical flow:

    discover fixes → check datasets → apply selected fixes

Core commands:

    woodpecker list-fixes
    woodpecker check . --select CMIP6D_0001
    woodpecker fix . --select CMIP6D_0001 --dry-run
    woodpecker fix . --select CMIP6D_0001

### Using FixPlanStore

Examples:

    # default JSON backend
    woodpecker check --plan plans.json

    # explicit backend selection
    woodpecker check --store json --plan plans.json
    woodpecker check --store duckdb --plan plans.duckdb

    # select a specific plan
    woodpecker fix --plan plans.json --plan-id atlas-basic

### Direct fix selection

    woodpecker check . --select CMIP6D_0001
    woodpecker fix . --select CMIP6D_0001

### Force-apply

- `--force-apply` skips `matches()` prefiltering before `apply()` to run faster
- requires explicit fix selection (`--select` or plan codes)

### List stored plans

    woodpecker list-plans --store json --plan plans.json
    woodpecker list-plans --store duckdb --plan plans.duckdb --format json

## Plugin Fixes (Entry Points)

Woodpecker can discover external fixes via Python entry points.  
Entry point group: `woodpecker.plugins`.

Architecture note:
- Core `woodpecker` keeps common, cross-dataset fixes.
- Dataset-specific fixes are expected to live in plugins.

Each plugin entry point can target either:

- a module import path, or
- a callable loader function

### Load current local plugins

In this repository, the current plugin packages are:

- `plugins/woodpecker-atlas-plugin`
- `plugins/woodpecker-cmip6-plugin`
- `plugins/woodpecker-cmip6-decadal-plugin`
- `plugins/woodpecker-cmip7-plugin`

Install them manually (editable mode):

    pip install -e plugins/woodpecker-atlas-plugin \
      -e plugins/woodpecker-cmip6-plugin \
      -e plugins/woodpecker-cmip6-decadal-plugin \
      -e plugins/woodpecker-cmip7-plugin

Or use Make targets:

    make install-plugins

`make dev` and `make dev-uv` install these plugin packages by default.

Minimal example:

`pyproject.toml`:

    [project]
    name = "woodpecker-example-plugin"
    version = "0.2.0"
    dependencies = ["woodpecker>=0.2.0"]

    [project.entry-points."woodpecker.plugins"]
    example = "woodpecker_example_plugin"

`woodpecker_example_plugin/__init__.py`:

    from woodpecker.fixes.registry import Fix, register_fix

    @register_fix
    class EXTERNAL_0001(Fix):
        code = "EXTERNAL_0001"
        name = "External demo fix"
        description = "A minimal plugin-provided fix."
        categories = ["metadata"]
        priority = 50
        dataset = None

        def matches(self, dataset):
            return True

        def check(self, dataset):
            return []

        def apply(self, dataset, dry_run=True):
            return False

## Examples

Example plan documents live in `examples/fix-plans`.

    woodpecker check --plan examples/fix-plans/atlas.json
    woodpecker fix --plan examples/fix-plans/atlas.json --dry-run
    woodpecker list-plans --store json --plan examples/fix-plans/atlas.json

## Provenance

Woodpecker writes a PROV-JSON provenance file by default when running `fix`.

    woodpecker fix . --select CMIP6D_0001
    woodpecker fix . --select CMIP6D_0001 --provenance-path run_01.prov.json
    woodpecker fix . --select CMIP6D_0001 --no-provenance

Embedded metadata:

    woodpecker fix . --select CMIP6D_0001 --embed-provenance-metadata --output-format netcdf

## GitHub Pages

This repository includes a workflow that builds and deploys the MkDocs site to GitHub Pages.