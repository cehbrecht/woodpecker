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

## GitHub Pages

This repository includes a workflow that builds and deploys the MkDocs site to GitHub Pages.
After enabling Pages in repo settings, fix codes are available as direct links (for example `.../fixes.html#CMIP6D_0001`).
