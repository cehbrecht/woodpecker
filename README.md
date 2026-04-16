# Woodpecker

[![CI](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml)
[![Docs](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml)
[![License](https://img.shields.io/github/license/cehbrecht/woodpecker)](https://github.com/cehbrecht/woodpecker/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://github.com/cehbrecht/woodpecker/blob/main/pyproject.toml)

Woodpecker is a lightweight, code-based catalog of dataset fixes for climate processing.

Each fix has a stable code (for example `CMIP6D_0001`) so tools and services can reference it directly.

Contributor and developer docs live in `CONTRIBUTING.md`.

## Core Concepts

Woodpecker is built around three simple concepts:

- **Fix**  
  An executable rule that checks and optionally fixes a dataset.  
  Each fix has a stable code (for example `CMIP6D_0001`).

- **FixPlan**  
  A declarative list of fixes (with optional parameters) applied in order.

- **FixPlanStore**  
  A lookup layer that returns matching `FixPlan`s for a dataset.

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
    woodpecker fix --plan plans.json --plan-id cmip6-default

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

Each plugin entry point can target either:

- a module import path, or
- a callable loader function

Minimal example:

`pyproject.toml`:

    [project]
    name = "woodpecker-example-plugin"
    version = "0.1.0"
    dependencies = ["woodpecker>=0.1.0"]

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

Example plans and a sample JSON plan store live in `examples/fix-plans`.

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