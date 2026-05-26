# CLI

The `woodpecker` command lets you inspect registered fixes and plans, check
datasets, and apply selected fixes from a terminal workflow.

Use `--format json` on most commands when you need machine-readable output.

## Inspect Available Fixes

List all registered fixes:

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

Use the [Generated Fixes Reference](FIXES.md) or
[Interactive Fix Browser](fixes.html) when you want to browse the same
registered ids in the documentation.

## Inspect Available Plans

List discovered core and plugin plans:

```bash
woodpecker list-plans
```

List plans from a specific store:

```bash
woodpecker list-plans --store catalog
woodpecker list-plans --store json --plan plans.json
woodpecker list-plans --store duckdb --plan plans.duckdb
woodpecker list-plans --store auto
```

`catalog` discovers plan documents from package resources, user and system
configuration directories, environment paths, and optional extra paths passed
with `--plan`.

Use the [Generated Fix Plans Reference](FIX_PLANS.md) for the generated table of
currently discovered plans.

## Check Datasets

Check one path or directory:

```bash
woodpecker check ./data --plan-id cmip6.core_units
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
are found.

## Apply Fixes

Preview changes first:

```bash
woodpecker fix ./data --plan-id cmip6.core_units --dry-run
```

Apply a discovered plan:

```bash
woodpecker fix ./data --plan-id cmip6.core_units
```

Apply selected fix ids directly:

```bash
woodpecker fix ./data --select cmip6_decadal.time_metadata --dry-run
woodpecker fix ./data --select cmip6_decadal.time_metadata
```

`fix` writes W3C PROV-JSON provenance by default:

```bash
woodpecker fix ./data --plan-id cmip6.core_units \
  --provenance-path woodpecker.prov.json
```

Disable provenance output when it is not needed:

```bash
woodpecker fix ./data --plan-id cmip6.core_units --no-provenance
```

## Plan Stores

Plan-backed commands accept these store backends:

| Store | Use |
| ----- | --- |
| `catalog` | Discovered package, user, system, environment, and explicit plan paths. |
| `json` | Local JSON or YAML plan document. |
| `duckdb` | DuckDB-backed plan catalog. |
| `auto` | Read-only one-step plans generated from registered fixes. |

Examples:

```bash
woodpecker check ./data --store catalog --plan-id atlas.basic
woodpecker check ./data --store json --plan plans.json --plan-id atlas.basic
woodpecker check ./data --store duckdb --plan plans.duckdb --plan-id atlas.basic
woodpecker check ./data --store auto \
  --plan-id woodpecker.normalize_tas_units_to_kelvin
```

When no explicit `--plan` is provided, `woodpecker check ./data --plan-id ...`
uses the discovered catalog.

## Load Plans Into A Store

Load plans from one store into a writable JSON or DuckDB store:

```bash
woodpecker load-plans --store json --plan plans.json \
  --from-store catalog --plan-id cmip6.core_units
```

Load all plans from a JSON document into DuckDB:

```bash
woodpecker load-plans --store duckdb --plan plans.duckdb \
  --from-store json --from-plan plans.json
```

## I/O Backends

Check optional runtime backend availability:

```bash
woodpecker io-status
woodpecker io-status --format json
```

Use strict I/O when a fallback should be treated as an error:

```bash
woodpecker check ./data --plan-id cmip6.core_units --strict-io
woodpecker fix ./data --plan-id cmip6.core_units --strict-io --dry-run
```

## Write Controls

Preview writes:

```bash
woodpecker fix ./data --plan-id cmip6.core_units --dry-run
```

Bypass `matches()` prefiltering only when you have explicitly selected the
fixes or plan you want to run:

```bash
woodpecker fix ./data --select cmip6_decadal.time_metadata --force-apply
```

Choose an output format when writing:

```bash
woodpecker fix ./data --plan-id cmip6.core_units --output-format netcdf
woodpecker fix ./data --plan-id cmip6.core_units --output-format zarr
```

`--output-format auto` is the default.
