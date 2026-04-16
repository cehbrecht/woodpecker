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

## Notes

- Plan files (`cmip6.json`, `esa_cci.json`) use `FixPlanDocument` with `plans: [...]`.
- Each entry in `plans` uses the same `FixPlan` schema as store payloads (`id`, `description`, `match`, `fixes`).
- CLI arguments still override values derived from plan files or store entries.