# CLI

The `woodpecker` command lets you inspect registered fix functions and recipes,
check datasets, and apply selected fixes from a terminal workflow.

Use `--format json` on most commands when you need machine-readable output.

## Inspect Available Fixes

List all registered fix functions:

```bash
woodpecker list-fixes
```

Filter by dataset or category:

```bash
woodpecker list-fixes --dataset CMIP6-decadal
woodpecker list-fixes --category metadata
woodpecker list-fixes --category metadata --category structure
```

Output formats:

```bash
woodpecker list-fixes --format text
woodpecker list-fixes --format json
woodpecker list-fixes --format md
```

Fix listings include labels so users can distinguish metadata-only cleanup from
operations that transform values, coordinates, or structure. Severity is
represented through ordinary labels whose categories are `risk-low`,
`risk-medium`, or `risk-high`; for example `risk.safe.metadata_only`. JSON
output includes `labels`, `label_titles`, and `label_metadata` for the same
label ids. Labels are not used for recipe selection, priority, or automation
decisions.

Use the [Generated Fixes Reference](FIXES.md) or
[Interactive Fix Browser](fixes.html) when you want to browse the same
registered ids in the documentation.

## Inspect Available Recipes

List discovered core and plugin recipes:

```bash
woodpecker list-recipes
```

List recipes from a specific store:

```bash
woodpecker list-recipes --store catalog
woodpecker list-recipes --store json --recipe recipes.json
woodpecker list-recipes --store duckdb --recipe recipes.duckdb
woodpecker list-recipes --store auto
```

`catalog` discovers recipe documents from package resources, user and system
configuration directories, environment paths, and optional extra paths passed
with `--recipe`.

Use the [Generated Recipes Reference](recipe-reference.md) for the generated table of
currently discovered recipes.

## Check Datasets

Check one path or directory:

```bash
woodpecker check ./data --recipe-id cmip6.core_units
```

Run selected fix ids directly:

```bash
woodpecker check ./data --select woodpecker.normalize_tas_units_to_kelvin
woodpecker check ./data --select cmip6_decadal.time_metadata
```

Repeat `--select` to run more than one fix:

```bash
woodpecker check ./data \
  --select woodpecker.normalize_tas_units_to_kelvin \
  --select woodpecker.ensure_latitude_is_increasing
```

Filter selected fixes by dataset or category:

```bash
woodpecker check ./data --dataset CMIP6-decadal
woodpecker check ./data --category metadata
```

`check` exits with status `1` when findings are reported and `0` when no issues
are found. Text findings show the selected fix severity label. JSON findings
include the complete label metadata.

## Apply Fixes

Preview changes first:

```bash
woodpecker fix ./data --recipe-id cmip6.core_units --dry-run
```

Dry-run output includes a preview section with the input path, selected fix id,
fix name, severity label, and whether that fix would change the dataset. Use
`--format json` to consume the same preview entries programmatically.

Apply a discovered recipe:

```bash
woodpecker fix ./data --recipe-id cmip6.core_units
```

Apply selected fix ids directly:

```bash
woodpecker fix ./data --select cmip6_decadal.time_metadata --dry-run
woodpecker fix ./data --select cmip6_decadal.time_metadata
```

`fix` writes W3C PROV-JSON provenance by default:

```bash
woodpecker fix ./data --recipe-id cmip6.core_units \
  --provenance-path woodpecker.prov.json
```

Disable provenance output when it is not needed:

```bash
woodpecker fix ./data --recipe-id cmip6.core_units --no-provenance
```

## Recipe Stores

Recipe-backed commands accept these store backends:

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

When no explicit `--recipe` is provided, `woodpecker check ./data --recipe-id ...`
uses the discovered catalog.

## Load Recipes Into A Store

Load recipes from one store into a writable JSON or DuckDB store:

```bash
woodpecker load-recipes --store json --recipe recipes.json \
  --from-store catalog --recipe-id cmip6.core_units
```

Load all recipes from a JSON document into DuckDB:

```bash
woodpecker load-recipes --store duckdb --recipe recipes.duckdb \
  --from-store json --from-recipe recipes.json
```

## I/O Backends

Check optional runtime backend availability:

```bash
woodpecker io-status
woodpecker io-status --format json
```

Use strict I/O when a fallback should be treated as an error:

```bash
woodpecker check ./data --recipe-id cmip6.core_units --strict-io
woodpecker fix ./data --recipe-id cmip6.core_units --strict-io --dry-run
```

## Write Controls

Preview writes:

```bash
woodpecker fix ./data --recipe-id cmip6.core_units --dry-run
```

Bypass `matches()` prefiltering only when you have explicitly selected the
fixes or recipe you want to run:

```bash
woodpecker fix ./data --select cmip6_decadal.time_metadata --force-apply
```

Choose an output format when writing:

```bash
woodpecker fix ./data --recipe-id cmip6.core_units --output-format netcdf
woodpecker fix ./data --recipe-id cmip6.core_units --output-format zarr
```

`--output-format auto` is the default.
