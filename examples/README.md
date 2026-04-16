# Fix Plan Examples

This folder contains compact, runnable examples so the top-level README stays short.

## Files

- `fix-plans/cmip6.json`: plan-file example for CMIP6-style inputs.
- `fix-plans/esa_cci.json`: selector-based plan-file example for ESA CCI / CMIP7-style inputs.
- `fix-plans/store.json`: JSON `FixPlanStore` sample containing two stored plans.

## Run Plan Files

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
python - <<'PY'
from woodpecker.plans.io import load_fix_plan_document
from woodpecker.stores import DuckDBFixPlanStore

doc = load_fix_plan_document("examples/fix-plans/cmip6.json")
store = DuckDBFixPlanStore("examples/fix-plans/store.duckdb")

for plan in doc.plans:
	store.save_plan(plan)
PY
```

Option B: copy existing plans from JSON store:

```bash
python - <<'PY'
from woodpecker.stores import DuckDBFixPlanStore, JsonFixPlanStore

source = JsonFixPlanStore("examples/fix-plans/store.json")
target = DuckDBFixPlanStore("examples/fix-plans/store.duckdb")

for plan in source.list_plans():
	target.save_plan(plan)
PY
```

## Notes

- Plan files (`cmip6.json`, `esa_cci.json`) use `FixPlanDocument` with `plans: [...]`.
- Each entry in `plans` uses the same `FixPlan` schema as store payloads (`id`, `description`, `match`, `fixes`).
- CLI arguments still override values derived from plan files or store entries.