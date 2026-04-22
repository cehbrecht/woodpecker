# Fix Plan Examples

This folder contains runnable FixPlan examples.

All commands use the current store-based CLI model:

- `--store` selects the backend (`json` by default)
- `--plan` provides the backend location
- `--plan-id` selects one plan when needed

## Files

- `fix-plans/atlas.json`: concrete plan-file example for ATLAS-style inputs.
- `fix-plans/esa_cci.json`: selector-based plan-file example for ESA CCI / CMIP7-style inputs.

Plan IDs used in these examples:

- `atlas.atlas_basic`
- `cmip7.esa_cci_water_vapour_zarr`
- `cmip7.esa_cci_water_vapour_dotname`

## Run With JSON Backend

`json` is the default backend, so these are equivalent:

```bash
woodpecker check --plan examples/fix-plans/atlas.json
woodpecker check --store json --plan examples/fix-plans/atlas.json
```

Run with plan-derived fix selection:

```bash
woodpecker check --plan examples/fix-plans/atlas.json
woodpecker fix --plan examples/fix-plans/atlas.json --dry-run

woodpecker check --plan examples/fix-plans/esa_cci.json --plan-id cmip7.esa_cci_water_vapour_zarr
woodpecker fix --plan examples/fix-plans/esa_cci.json --plan-id cmip7.esa_cci_water_vapour_zarr --force-apply
```

List plans from a JSON file:

```bash
woodpecker list-plans --store json --plan examples/fix-plans/atlas.json
```

Lookup matching plans from the JSON file:

```bash
woodpecker check . --store json --plan examples/fix-plans/atlas.json
```

Select one plan explicitly:

```bash
woodpecker fix . --store json --plan examples/fix-plans/atlas.json --plan-id atlas.atlas_basic --dry-run
```

## Run With DuckDB Backend

List plans in DuckDB:

```bash
woodpecker list-plans --store duckdb --plan examples/fix-plans/store.duckdb
```

Lookup matching plans from DuckDB:

```bash
woodpecker check . --store duckdb --plan examples/fix-plans/store.duckdb
```

Select one plan explicitly:

```bash
woodpecker fix . --store duckdb --plan examples/fix-plans/store.duckdb --plan-id atlas.atlas_basic --dry-run
```

## Load Plans Into DuckDB

Install optional backends first:

```bash
pip install -e ".[full]"
```

Load from a JSON plan document:

```bash
woodpecker load-plans \
  --store duckdb \
  --plan examples/fix-plans/store.duckdb \
  --from-plan examples/fix-plans/atlas.json
```

Load from a JSON backend source:

```bash
woodpecker load-plans \
  --store duckdb \
  --plan examples/fix-plans/store.duckdb \
  --from-store json \
  --from-plan examples/fix-plans/atlas.json

# Optional: load one plan only
woodpecker load-plans \
  --store duckdb \
  --plan examples/fix-plans/store.duckdb \
  --from-store json \
  --from-plan examples/fix-plans/atlas.json \
  --plan-id atlas.atlas_basic
```

## Data Model

- Plan documents use `{"plans": [...]}`.
- Each plan uses the same `FixPlan` schema: `id`, `namespace`, `description`, `match`, `fixes`, optional `links`.
- Each fix step is `fix + options` (and optional `links`), not a globally identified object.
- Example plans use canonical fix IDs directly in `<prefix>.<local_id>` form.
- JSON and DuckDB backends both load and return the same `FixPlan` objects.
- CLI options such as `--select`, `--dataset`, and `--category` override plan-derived defaults.