# Fix Plan Examples

This folder contains compact, runnable examples so the top-level README stays short.

The examples follow the same core concepts: executable `Fix` rules, ordered `FixPlan` definitions, and optional `FixPlanStore` lookup backends.

## Files

- `fix-plans/atlas.json`: concrete plan-file example for ATLAS-style inputs.
- `fix-plans/esa_cci.json`: selector-based plan-file example for ESA CCI / CMIP7-style inputs.

## Run Using Plan Files

```bash
woodpecker check --plan examples/fix-plans/atlas.json
woodpecker fix --plan examples/fix-plans/atlas.json --dry-run

woodpecker check --plan examples/fix-plans/esa_cci.json
woodpecker fix --plan examples/fix-plans/esa_cci.json --force-apply
```

`--store` defaults to `json`, so `--plan` alone is shorthand for:

```bash
woodpecker check --store json --plan examples/fix-plans/atlas.json
```

## Run Via JSON Plan Store

List available plans:

```bash
woodpecker list-plans --store json --plan examples/fix-plans/atlas.json
```

Use store lookup (auto-match by dataset attrs/path patterns):

```bash
woodpecker check . --store json --plan examples/fix-plans/atlas.json
```

Select a specific stored plan:

```bash
woodpecker fix . --store json --plan examples/fix-plans/atlas.json --plan-id atlas-basic --dry-run
```

## Run Via DuckDB Plan Store

DuckDB stores the same `FixPlan` entries as JSON, but in database form.

List available plans:

```bash
woodpecker list-plans --store duckdb --plan examples/fix-plans/store.duckdb
```

Use store lookup:

```bash
woodpecker check . --store duckdb --plan examples/fix-plans/store.duckdb
```

Select a specific stored plan:

```bash
woodpecker fix . --store duckdb --plan examples/fix-plans/store.duckdb --plan-id atlas-basic --dry-run
```

## Populate DuckDB Store

Install DuckDB support first:

```bash
pip install -e ".[full]"
```

Option A: from a `FixPlanDocument` file (`plans: [...]`):

```bash
woodpecker load-plans \
	--store duckdb \
	--plan examples/fix-plans/store.duckdb \
	--from-plan examples/fix-plans/atlas.json
```

Option B: copy existing plans from JSON store:

```bash
woodpecker load-plans \
	--store duckdb \
	--plan examples/fix-plans/store.duckdb \
	--from-store json \
	--from-plan examples/fix-plans/atlas.json

# Optional: only copy one plan id
woodpecker load-plans \
	--store duckdb \
	--plan examples/fix-plans/store.duckdb \
	--from-store json \
	--from-plan examples/fix-plans/atlas.json \
	--plan-id atlas-basic
```

## Notes

- The similarity between a plan document entry and a store entry is intentional.
- Both use the same `FixPlan` fields: `id`, `description`, `match`, `fixes`.
- The practical difference is source/backend interpretation:
	- JSON store: local file path passed to `--plan`
	- DuckDB store: database file path passed to `--plan`
- Plan files (`atlas.json`, `esa_cci.json`) are `FixPlanDocument`s with `plans: [...]`.
- Each entry in `plans` uses the same `FixPlan` schema (`id`, `description`, `match`, `fixes`).
- `FixPlanStore` backends (JSON, DuckDB) store and return the same `FixPlan` objects.
- There is only one `FixPlan` schema used across files and stores.
- CLI arguments still override values derived from plan files or store entries.