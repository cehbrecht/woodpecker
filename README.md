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
  Used to describe how a dataset should be fixed.

- **FixPlanStore** (optional)  
  A lookup layer that returns matching `FixPlan`s for a dataset.  
  Can be backed by JSON files or DuckDB.

Implementation note:
- A design-stub placeholder for a future Elasticsearch-backed store is in `woodpecker/stores/elasticsearch_store.py` (not wired into CLI/runtime yet).

### Unified model

There is only one FixPlan schema.

All plans are accessed through a FixPlanStore:

- `--store` selects the backend (default: `json`)
- `--plan` provides the location interpreted by that backend

For JSON, plan files and plan stores use the same document format:

    {
      "plans": [ ... ]
    }

There is no schema difference between a plan-file entry and a store entry; only how they are accessed differs.

## Quickstart

Conda setup:

    conda env create -f environment.yml
    conda activate woodpecker
    make dev
    make list-fixes

Optional DuckDB support (for `DuckDBFixPlanStore`):

    pip install -e ".[full]"

## Usage

Typical flow:

    discover fixes → check datasets → apply selected fixes

Core commands:

    woodpecker list-fixes
    woodpecker check . --select CMIP6D_0001
    woodpecker fix . --select CMIP6D_0001 --dry-run
    woodpecker fix . --select CMIP6D_0001

### Fix plan usage

- `--store` selects the FixPlanStore backend (default: `json`)
- `--plan` provides the location used by that backend (JSON file, DuckDB file, etc.)
- `--plan-id` optionally selects a specific FixPlan

Examples:

    # default JSON backend
    woodpecker check --plan plans.json

    # explicit backend
    woodpecker check --store json --plan plans.json
    woodpecker check --store duckdb --plan plans.duckdb

    # select a specific plan
    woodpecker fix --plan plans.json --plan-id cmip6-default

### Direct mode (no plans)

You can still run fixes directly without a plan source:

    woodpecker check . --select CMIP6D_0001
    woodpecker fix . --select CMIP6D_0001

### Force-apply

- `--force-apply` skips `matches()` prefiltering before `apply()` to run faster
- Safety rule: requires explicit fix selection (`--select` or plan codes)

### List stored plans

    woodpecker list-plans --store json --plan plans.json
    woodpecker list-plans --store duckdb --plan plans.duckdb --format json

FixPlanStores provide an optional way to look up FixPlans automatically based on dataset metadata or file paths.

More advanced patterns are in `CONTRIBUTING.md`.

## Plugin Fixes (Entry Points)

Woodpecker can discover external fixes via Python entry points.  
Entry point group: `woodpecker.plugins`.

Each plugin entry point can target either:

- a module import path (import side effects register fixes), or
- a callable loader function (called once at startup).

Minimal example plugin package:

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

    def load():
        return None

Concrete reference package in this repo:

- `plugins/woodpecker-cmip7-plugin` (CMIP7-style external fixes)

Install before using `CMIP7_000*` codes:

    pip install -e plugins/woodpecker-cmip7-plugin

Catalog source labels:

- `core` = built-in fixes
- `plugin:<package>` = external plugin fixes

## Examples

Example plans and a sample JSON plan store live in `examples/fix-plans`.

Start here:

- `examples/README.md`

Quick run:

    woodpecker check --plan examples/fix-plans/atlas.json
    woodpecker fix --plan examples/fix-plans/atlas.json --dry-run
    woodpecker list-plans --store json --plan examples/fix-plans/atlas.json

## Provenance

Woodpecker writes a PROV-JSON provenance file by default when you run `fix`.  
Default output file: `woodpecker.prov.json`.

Examples:

    # default
    woodpecker fix . --select CMIP6D_0001

    # custom path
    woodpecker fix . --select CMIP6D_0001 --provenance-path run_01.prov.json

    # disable
    woodpecker fix . --select CMIP6D_0001 --no-provenance

Example (shortened):

    {
      "prefix": { ... },
      "activity": { ... }
    }

Embedded provenance metadata:

    woodpecker fix . --select CMIP6D_0001 --embed-provenance-metadata --output-format netcdf

## GitHub Pages

This repository includes a workflow that builds and deploys the MkDocs site to GitHub Pages.  
After enabling Pages, fix codes are available as direct links.