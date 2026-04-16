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

Plan files (`--plan`) and plan stores use the same `FixPlan` schema.  
Plan files are simply containers of one or more plans.
There is no schema difference between a plan-file entry and a store entry; only the loading/storage path differs.

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

Fix plan usage:

- `--store` selects the FixPlanStore backend (default: `json`).
- `--plan` provides the location interpreted by that backend (JSON file, DuckDB file, etc.).
- Plan files and stores use the same underlying FixPlan schema.

Force-apply option:

- `--force-apply` skips `matches()` prefiltering before `apply()` to run faster.
- Safety rule: `--force-apply` requires explicit fix selection (`--select` or plan codes).

List stored fix plans:

    woodpecker list-plans --store json --plan plans.json
    woodpecker list-plans --store duckdb --plan plans.duckdb --format json

Fix plan stores provide an optional way to look up FixPlans automatically based on dataset metadata or file paths.

More advanced fix plan patterns are in `CONTRIBUTING.md`.

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
    # or callable loader:
    # example = "woodpecker_example_plugin:load"

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
        # Optional callable entry point target.
        return None

Concrete reference package in this repo:

- `plugins/woodpecker-cmip7-plugin` (CMIP7-style external fixes)

CMIP7 fixes are plugin-provided (not built into core).

Install the CMIP7 plugin example before using `CMIP7_000*` codes:

    pip install -e plugins/woodpecker-cmip7-plugin

Catalog source labels:

- `core` means the fix is provided by the built-in `woodpecker.fixes` package.
- `plugin:<package>` means the fix was discovered from an external plugin package.

## Examples

Example plans and a sample JSON plan store live in `examples/fix-plans`.

Start here:

- `examples/README.md`

Quick run:

    woodpecker check --plan examples/fix-plans/atlas.json
    woodpecker fix --plan examples/fix-plans/atlas.json --dry-run
    woodpecker list-plans --store json --plan examples/fix-plans/atlas.json

Plan files and stores use the same FixPlan schema; the difference is only how plans are stored and retrieved.

## Provenance

Woodpecker writes a PROV-JSON provenance file by default when you run `fix`.  
Default output file: `woodpecker.prov.json`.

Examples:

    # default provenance file
    woodpecker fix . --select CMIP6D_0001

    # custom provenance output path
    woodpecker fix . --select CMIP6D_0001 --provenance-path run_01.prov.json

    # disable provenance output
    woodpecker fix . --select CMIP6D_0001 --no-provenance

Example `woodpecker.prov.json` (shortened):

    {
      "prefix": {
        "default": "urn:woodpecker:",
        "woodpecker": "https://github.com/macpingu/woodpecker#"
      },
      "activity": {
        "activity-woodpecker-run-123": {
          "prov:type": "woodpecker:FixRun",
          "mode": "write",
          "output_format": "netcdf",
          "selected_codes": "[\"CMIP6D_0001\"]",
          "stats": "{\"attempted\": 1, \"changed\": 1}"
        }
      }
    }

Embedded provenance metadata (NetCDF output):

    woodpecker fix . --select CMIP6D_0001 --embed-provenance-metadata --output-format netcdf

This writes a global attribute named `woodpecker_provenance` to the output dataset.

Example attribute value (JSON string):

    {"applied_codes": ["CMIP6D_0001"], "generated_at": "...", "run_id": "...", "source": "..."}

## GitHub Pages

This repository includes a workflow that builds and deploys the MkDocs site to GitHub Pages.  
After enabling Pages in repo settings, fix codes are available as direct links (for example `.../fixes.html#CMIP6D_0001`).