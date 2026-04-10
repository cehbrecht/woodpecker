# Woodpecker

[![CI](https://github.com/macpingu/woodpecker/actions/workflows/ci.yml/badge.svg)](https://github.com/macpingu/woodpecker/actions/workflows/ci.yml)
[![Docs](https://github.com/macpingu/woodpecker/actions/workflows/docs.yml/badge.svg)](https://github.com/macpingu/woodpecker/actions/workflows/docs.yml)

Woodpecker is a small, code-based catalog of dataset fixes for climate workflows.
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

## Usage

Flow: `discover fixes -> check findings -> apply selected fixes`.

Core commands:

```bash
woodpecker list-fixes
woodpecker check . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001 --dry-run
woodpecker fix . --select CMIP6D_0001
```

Workflow option:

- `--workflow` loads fix selection and options from a JSON workflow file.

Force-apply option:

- `--force-apply` skips pre-check execution before applying fixes to run faster.
- Safety rule: `--force-apply` requires explicit fix selection (`--select` or workflow codes).

More advanced workflow patterns are in `CONTRIBUTING.md`.

## Example

```bash
touch cmip6_case.nc
woodpecker check . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001 --dry-run
woodpecker fix . --select CMIP6D_0001
```

## Workflow Example

`workflow.json`:

```json
{
	"version": 1,
	"dataset": "cmip7",
	"datasets": {
		"*esa_cci_a*.nc": {
			"steps": [
				{
					"code": "CMIP7_0003",
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
			"steps": [
				{
					"code": "CMIP7_0003",
					"options": {
						"variable_map": {"prw": "tcwv"},
						"realm": "atmos"
					}
				}
			]
		},
		"*esa_cci_c*.nc": {
			"steps": [
				{
					"code": "CMIP7_0003",
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
woodpecker fix --workflow workflow.json
woodpecker fix --workflow workflow.json --force-apply
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
