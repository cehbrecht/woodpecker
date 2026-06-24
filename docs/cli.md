# CLI

Use `woodpecker` to list fixes and recipes, check datasets, preview repairs,
and apply selected fixes from the terminal.

Use `--format json` when another tool needs machine-readable output.

## Common Commands

| Task | Command |
| ---- | ------- |
| List fixes | `woodpecker list-fixes` |
| List recipes | `woodpecker list-recipes` |
| Check with a recipe | `woodpecker check ./data --recipe-id cmip6.core_units` |
| Preview a repair | `woodpecker fix ./data --recipe-id cmip6.core_units --dry-run` |
| Apply a repair | `woodpecker fix ./data --recipe-id cmip6.core_units` |
| Check one fix id | `woodpecker check ./data --select woodpecker.normalize_tas_units_to_kelvin` |

`check` exits with status `1` when findings are reported and `0` when no issues
are found.

## List Fixes

```bash
woodpecker list-fixes
woodpecker list-fixes --dataset CMIP6-decadal
woodpecker list-fixes --category metadata
woodpecker list-fixes --format json
```

Fix listings include labels. Severity labels use categories such as `risk-low`,
`risk-medium`, and `risk-high`. JSON output includes `labels`, `label_titles`,
and `label_metadata`.

Labels help users understand fixes. They do not affect recipe selection,
priority, or automation.

Use [Fix Reference](FIXES.md) or [Interactive Fix Browser](fixes.html) to browse
the same registered ids.

## List Recipes

```bash
woodpecker list-recipes
woodpecker list-recipes --store catalog
woodpecker list-recipes --store json --recipe recipes.json
woodpecker list-recipes --store duckdb --recipe recipes.duckdb
woodpecker list-recipes --store auto
```

`catalog` discovers recipes from package resources, user and system config
directories, environment paths, and extra paths passed with `--recipe`.

Use [Recipe Reference](recipe-reference.md) for the generated recipe table.

## Check

```bash
woodpecker check ./data --recipe-id cmip6.core_units
woodpecker check ./data --select cmip6_decadal.time_metadata
woodpecker check ./data --dataset CMIP6-decadal
woodpecker check ./data --category metadata
```

Repeat `--select` to run more than one fix:

```bash
woodpecker check ./data \
  --select woodpecker.normalize_tas_units_to_kelvin \
  --select woodpecker.ensure_latitude_is_increasing
```

Text findings show the selected fix severity label. JSON findings include the
complete label metadata.

## Fix

```bash
woodpecker fix ./data --recipe-id cmip6.core_units --dry-run
woodpecker fix ./data --recipe-id cmip6.core_units
woodpecker fix ./data --select cmip6_decadal.time_metadata --dry-run
woodpecker fix ./data --select cmip6_decadal.time_metadata
```

Dry-run output shows the input path, selected fix id, fix name, severity label,
and whether the fix would change the dataset. Use `--format json` for the same
preview data as structured output.

## Recipe Stores

Recipe-backed commands accept:

| Store | Use |
| ----- | --- |
| `catalog` | Discovered package, user, system, environment, and explicit recipe paths. |
| `json` | Local JSON or YAML recipe document. |
| `duckdb` | DuckDB-backed recipe catalog. |
| `auto` | Read-only one-step recipes generated from registered fix functions. |

Examples:

```bash
woodpecker check ./data --store catalog --recipe-id atlas.basic
woodpecker check ./data --store json --recipe recipes.json --recipe-id atlas.basic
woodpecker check ./data --store duckdb --recipe recipes.duckdb --recipe-id atlas.basic
woodpecker check ./data --store auto \
  --recipe-id woodpecker.normalize_tas_units_to_kelvin
```

When no explicit `--recipe` is provided, `--recipe-id` uses the discovered
catalog.

## Load Recipes

```bash
woodpecker load-recipes --store json --recipe recipes.json \
  --from-store catalog --recipe-id cmip6.core_units

woodpecker load-recipes --store duckdb --recipe recipes.duckdb \
  --from-store json --from-recipe recipes.json
```

## Safety And Output

| Need | Option |
| ---- | ------ |
| Preview writes | `--dry-run` |
| Disable provenance | `--no-provenance` |
| Write provenance elsewhere | `--provenance-path woodpecker.prov.json` |
| Treat I/O fallback as an error | `--strict-io` |
| Choose NetCDF output | `--output-format netcdf` |
| Choose Zarr output | `--output-format zarr` |

`fix` writes W3C PROV-JSON provenance by default.

Use `--force-apply` only with explicit fix or recipe selection:

```bash
woodpecker fix ./data --select cmip6_decadal.time_metadata --force-apply
```

Check optional I/O backend availability:

```bash
woodpecker io-status
woodpecker io-status --format json
```
