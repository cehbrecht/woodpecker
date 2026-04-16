# Fix Plan Examples

This folder contains compact, runnable examples so the top-level README stays short.

## Files

- `fix-plans/cmip6.json`: plan-file example for CMIP6-style inputs.
- `fix-plans/esa_cci.json`: selector-based plan-file example for ESA CCI / CMIP7-style inputs.
- `fix-plans/store.json`: JSON-based `FixPlanStore` sample containing two `FixPlan` entries.

## Run Using Plan Files

```bash
woodpecker check --plan examples/fix-plans/cmip6.json
woodpecker fix --plan examples/fix-plans/cmip6.json --dry-run

woodpecker check --plan examples/fix-plans/esa_cci.json
woodpecker fix --plan examples/fix-plans/esa_cci.json --force-apply
```

## Run Via JSON Plan Store

List available plans:

```bash
woodpecker list-plans --plan-store json --plan-store-path examples/fix-plans/store.json
```

Use store lookup (auto-match by dataset attrs/path patterns):

```bash
woodpecker check . --plan-store json --plan-store-path examples/fix-plans/store.json
```

Select a specific stored plan:

```bash
woodpecker fix . --plan-store json --plan-store-path examples/fix-plans/store.json --plan-id cmip6-default --dry-run
```

## Run Via DuckDB Plan Store

DuckDB stores the same `FixPlan` entries as JSON, but in database form.

List available plans:

```bash
woodpecker list-plans --plan-store duckdb --plan-store-path examples/fix-plans/store.duckdb
```

Use store lookup:

```bash
woodpecker check . --plan-store duckdb --plan-store-path examples/fix-plans/store.duckdb
```

Select a specific stored plan:

```bash
woodpecker fix . --plan-store duckdb --plan-store-path examples/fix-plans/store.duckdb --plan-id cmip6-default --dry-run
```

## Populate DuckDB Store

Install DuckDB support first:

```bash
pip install -e ".[full]"
```

Option A: from a `FixPlanDocument` file (`plans: [...]`):

```bash
woodpecker load-plans \
	--plan-store duckdb \
	--plan-store-path examples/fix-plans/store.duckdb \
	--from-plan examples/fix-plans/cmip6.json
```

Option B: copy existing plans from JSON store:

```bash
woodpecker load-plans \
	--plan-store duckdb \
	--plan-store-path examples/fix-plans/store.duckdb \
	--from-store json \
	--from-store-path examples/fix-plans/store.json

# Optional: only copy one plan id
woodpecker load-plans \
	--plan-store duckdb \
	--plan-store-path examples/fix-plans/store.duckdb \
	--from-store json \
	--from-store-path examples/fix-plans/store.json \
	--plan-id cmip6-default
```

## Notes

- Plan files (`cmip6.json`, `esa_cci.json`) are `FixPlanDocument`s with `plans: [...]`.
- Each entry in `plans` uses the same `FixPlan` schema (`id`, `description`, `match`, `fixes`).
- `FixPlanStore` backends (JSON, DuckDB) store and return the same `FixPlan` objects.
- There is only one `FixPlan` schema used across files and stores.
- CLI arguments still override values derived from plan files or store entries.