# Woodpecker

[![CI](https://github.com/macpingu/woodpecker/actions/workflows/ci.yml/badge.svg)](https://github.com/macpingu/woodpecker/actions/workflows/ci.yml)
[![Docs](https://github.com/macpingu/woodpecker/actions/workflows/docs.yml/badge.svg)](https://github.com/macpingu/woodpecker/actions/workflows/docs.yml)

Woodpecker is a small, code-based catalog of dataset fixes for climate processing.
Each fix has a stable code (for example `CMIP6D_0001`) so tools and services can reference it directly.

Contributor and developer docs live in `CONTRIBUTING.md`.

## Quickstart

Conda setup:

```bash
conda env create -f environment.yml
conda activate woodpecker
make dev
make list-fixes
```

Optional DuckDB support (for `DuckDBFixPlanStore`):

```bash
pip install -e ".[full]"
```

## Usage

Flow: `discover fixes -> check findings -> apply selected fixes`.

Core commands:

```bash
woodpecker list-fixes
woodpecker check . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001 --dry-run
woodpecker fix . --select CMIP6D_0001
```

List stored fix plans:

```bash
woodpecker list-plans --plan-store json --plan-store-path plans.json
woodpecker list-plans --plan-store duckdb --plan-store-path plans.duckdb --format json
```

Fix plan option:

- `--plan` loads fix selection and options from a JSON/YAML fix plan file.

Force-apply option:

- `--force-apply` skips `matches()` prefiltering before `apply()` to run faster.
- Safety rule: `--force-apply` requires explicit fix selection (`--select` or plan codes).

More advanced fix plan patterns are in `CONTRIBUTING.md`.

## Plugin Fixes (Entry Points)

Woodpecker can discover external fix plugins via Python entry points.
Entry point group: `woodpecker.plugins`.

Each plugin entry point can target either:

- a module import path (import side effects register fixes), or
- a callable loader function (called once at startup).

Minimal example plugin package:

`pyproject.toml`:

```toml
[project]
name = "woodpecker-example-plugin"
version = "0.1.0"
dependencies = ["woodpecker>=0.1.0"]

[project.entry-points."woodpecker.plugins"]
example = "woodpecker_example_plugin"
# or callable loader:
# example = "woodpecker_example_plugin:load"
```

`woodpecker_example_plugin/__init__.py`:

```python
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
```

Concrete reference package in this repo:

- `plugins/woodpecker-cmip7-plugin` (CMIP7-style external fixes)

CMIP7 fixes are plugin-provided (not built into core).

Install the CMIP7 plugin example before using `CMIP7_000*` codes:

```bash
pip install -e plugins/woodpecker-cmip7-plugin
```

## Example

```bash
touch cmip6_case.nc
woodpecker check . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001 --dry-run
woodpecker fix . --select CMIP6D_0001
```

## Fix Plan Example

`plan.json`:

```json
{
	"version": 1,
	"comment": "Fix plan notes: see fixes overview at https://macpingu.github.io/woodpecker/fixes.html",
	"dataset": "cmip7",
	"datasets": {
		"*esa_cci_a*.nc": {
			"comment": "ESA CCI file group A",
			"steps": [
				{
					"code": "CMIP7_0003",
					"comment": "CMIP7_0003: configurable reformat bridge",
					"options": {
						"variable_map": {"prw": "tcwv"},
						"dim_map": {"bnds": "nv"},
						"realm": "atmos",
						"branded_variable": "prw_tavg-u-hxy-u"
					}
				}
			]
		},
		"*esa_cci_b*.nc": {
			"comment": "ESA CCI file group B",
			"steps": [
				{
					"code": "CMIP7_0003",
					"comment": "CMIP7_0003 with variable_map + realm",
					"options": {
						"variable_map": {"prw": "tcwv"},
						"realm": "atmos"
					}
				}
			]
		},
		"*esa_cci_c*.nc": {
			"comment": "ESA CCI file group C",
			"steps": [
				{
					"code": "CMIP7_0003",
					"comment": "CMIP7_0003 with branded variable metadata",
					"options": {
						"variable_map": {"prw": "tcwv"},
						"branded_variable": "prw_tavg-u-hxy-u"
					}
				}
			]
		}
	},
	"output_format": "netcdf"
}
```

Run it:

```bash
woodpecker fix --plan plan.json
woodpecker fix --plan plan.json --force-apply
```

Same idea in YAML:

```yaml
version: 1
comment: "Fix plan notes: see fixes overview at https://macpingu.github.io/woodpecker/fixes.html"
dataset: cmip7
datasets:
	"*esa_cci_a*.nc":
		comment: "ESA CCI file group A"
		steps:
			- code: CMIP7_0003
				comment: "CMIP7_0003: configurable reformat bridge"
				options:
					variable_map:
						prw: tcwv
					dim_map:
						bnds: nv
					realm: atmos
					branded_variable: prw_tavg-u-hxy-u
output_format: netcdf
```

## Provenance

Woodpecker writes a PROV-JSON provenance file by default when you run `fix`.
Default output file: `woodpecker.prov.json`.

Examples:

```bash
# default provenance file
woodpecker fix . --select CMIP6D_0001

# custom provenance output path
woodpecker fix . --select CMIP6D_0001 --provenance-path run_01.prov.json

# disable provenance output
woodpecker fix . --select CMIP6D_0001 --no-provenance
```

Example `woodpecker.prov.json` (shortened):

```json
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
	},
	"entity": {
		"entity-input-0": {
			"prov:type": "prov:Entity",
			"reference": "./cmip6_case.nc",
			"target_reference": "./cmip6_case.nc"
		}
	},
	"agent": {
		"agent-woodpecker": {
			"prov:type": "prov:SoftwareAgent",
			"name": "woodpecker"
		}
	},
	"wasAssociatedWith": {
		"_:id1": {
			"prov:activity": "activity-woodpecker-run-123",
			"prov:agent": "agent-woodpecker"
		}
	},
	"used": {
		"_:id2": {
			"prov:activity": "activity-woodpecker-run-123",
			"prov:entity": "entity-input-0"
		}
	}
}
```

Embedded provenance metadata (NetCDF output):

```bash
woodpecker fix . --select CMIP6D_0001 --embed-provenance-metadata --output-format netcdf
```

This writes a global attribute named `woodpecker_provenance` to the output dataset.

Example attribute value (JSON string):

```text
{"applied_codes": ["CMIP6D_0001"], "generated_at": "2026-04-11T10:22:33.123456+00:00", "run_id": "woodpecker-woodpecker", "source": "./cmip6_case.nc"}
```

## GitHub Pages

This repository includes a workflow that builds and deploys the MkDocs site to GitHub Pages.
After enabling Pages in repo settings, fix codes are available as direct links (for example `.../fixes.html#CMIP6D_0001`).
