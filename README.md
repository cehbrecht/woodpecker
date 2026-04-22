# Woodpecker

[![CI](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml)
[![Docs](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml)
[![License](https://img.shields.io/github/license/cehbrecht/woodpecker)](https://github.com/cehbrecht/woodpecker/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://github.com/cehbrecht/woodpecker/blob/main/pyproject.toml)

Woodpecker is a lightweight, code-based catalog of common dataset fixes for climate processing.

Dataset-specific fix families are provided as external plugins.

Example: a dataset may use Celsius instead of Kelvin, contain inconsistent
dimension names, or need metadata normalization. Woodpecker can detect and
apply known fixes consistently.

Contributor and developer docs live in `CONTRIBUTING.md`.

---

## Why Woodpecker?

* Reuse known dataset fixes across workflows
* Keep fix logic versioned and testable in code
* Apply fixes consistently in automated pipelines
* Extend with project-specific plugins

---

## Core Concepts

### Fix

An executable rule that checks and optionally repairs a dataset issue.

Fixes are registered in the `FixRegistry` and discovered at runtime via
Python entry points.

### Fix Identifiers

Every fix and plan has a stable, scoped identifier:

* **`namespace_prefix`** — owning namespace, e.g. `cmip6_decadal`, `atlas`, `woodpecker`
* **`local_id`** — snake_case identifier unique within that namespace
* **canonical id** — `<namespace_prefix>.<local_id>`

Examples:

* `cmip6_decadal.time_metadata`
* `atlas.encoding_cleanup`
* `woodpecker.normalize_units`

Canonical ids are stored in plans, used on the CLI, and resolved through the
`IdentifierResolver`. Short local ids can also be used when unambiguous.

Fix classes declare identifiers as class attributes:

```python
class TimeMetadataFix(Fix):
    namespace_prefix = "cmip6_decadal"
    local_id = "time_metadata"
```

The registry validates these and derives:

```python
canonical_id = "cmip6_decadal.time_metadata"
```

### FixPlan

A declarative list of fix references (`id` + optional `options`) applied in order
to a matching dataset.

Plans can match datasets using metadata and file path patterns. Plans may also
declare a namespace so unqualified fix ids resolve automatically.

```json
{
  "id": "atlas.encoding_cleanup_suite",
  "namespace": "atlas",
  "match": {
    "path_patterns": ["*atlas*.nc"]
  },
  "fixes": [
    {
      "id": "encoding_cleanup",
      "options": {
        "mode": "strict"
      }
    },
    {
      "id": "project_id_normalization"
    }
  ]
}
```

### FixPlanStore

A lookup layer that returns matching `FixPlan`s for a dataset.

Plans can be retrieved by canonical id, local id, or alias.

Current backends:

* JSON (default)
* DuckDB

Plans are accessed through a store on the CLI:

* `--store` — backend type (`json` or `duckdb`, default: `json`)
* `--plan` — store location (file path)
* `--plan-id` — optionally select a specific plan by id

---

## Quickstart

```bash
conda env create -f environment.yml
conda activate woodpecker
make dev
make list-fixes
```

Optional DuckDB support:

```bash
pip install -e ".[full]"
```

---

## Usage

```text
discover fixes → check datasets → apply selected fixes
```

### Direct fix selection

```bash
woodpecker list-fixes
woodpecker check . --select cmip6_decadal.time_metadata
woodpecker fix . --select cmip6_decadal.time_metadata --dry-run
woodpecker fix . --select cmip6_decadal.time_metadata
```

### Using a FixPlanStore

```bash
# default JSON backend
woodpecker check --plan plans.json
woodpecker fix --plan plans.json --dry-run

# explicit backend
woodpecker check --store duckdb --plan plans.duckdb

# select a specific plan by id
woodpecker fix --plan plans.json --plan-id atlas.encoding_cleanup_suite
```

### List stored plans

```bash
woodpecker list-plans --store json --plan plans.json
woodpecker list-plans --store duckdb --plan plans.duckdb --format json
```

### Force-apply

`--force-apply` skips `matches()` prefiltering before `apply()`.

Useful when fix selection is already explicit via `--select` or a plan.

---

## Plugins

Core Woodpecker provides fixes that apply across datasets.

Dataset-specific fixes live in plugins discovered via the
`woodpecker.plugins` entry point group.

### Bundled plugins

The repository ships local plugins under `plugins/`:

| Plugin package                    | Namespace prefix |
| --------------------------------- | ---------------- |
| `woodpecker-atlas-plugin`         | `atlas`          |
| `woodpecker-cmip6-plugin`         | `cmip6`          |
| `woodpecker-cmip6-decadal-plugin` | `cmip6_decadal`  |
| `woodpecker-cmip7-plugin`         | `cmip7`          |

Install them:

```bash
make install-plugins
make dev
```

### Writing a plugin

`pyproject.toml`

```toml
[project]
name = "woodpecker-example-plugin"
version = "0.1.0"
dependencies = ["woodpecker>=0.2.0"]

[project.entry-points."woodpecker.plugins"]
example = "woodpecker_example_plugin"
```

`woodpecker_example_plugin/__init__.py`

```python
from woodpecker.fixes.registry import Fix, register_fix

@register_fix
class ExternalDemoFix(Fix):
    namespace_prefix = "example"
    local_id = "demo"
    name = "External demo fix"
    description = "A minimal plugin-provided fix."
    categories = ["metadata"]
    priority = 50
    dataset = None

    def check(self, dataset):
        return []

    def apply(self, dataset, dry_run=True):
        return False
```

Derived canonical id:

```text
example.demo
```

---

## Examples

Example plan documents live in `examples/fix-plans/`.

```bash
woodpecker check --plan examples/fix-plans/atlas.json
woodpecker fix --plan examples/fix-plans/atlas.json --dry-run
woodpecker list-plans --plan examples/fix-plans/atlas.json
```

---

## Provenance

Woodpecker writes a PROV-JSON provenance file by default when running `fix`.

```bash
woodpecker fix . --select cmip6_decadal.time_metadata
woodpecker fix . --select cmip6_decadal.time_metadata --provenance-path run_01.prov.json
woodpecker fix . --select cmip6_decadal.time_metadata --no-provenance
woodpecker fix . --select cmip6_decadal.time_metadata --embed-provenance-metadata --output-format netcdf
```

Provenance records can evolve further to include plugin/version metadata.

---

## GitHub Pages

Docs are built and deployed automatically on pushes touching:

* `woodpecker/`
* `docs/`
* `scripts/`
