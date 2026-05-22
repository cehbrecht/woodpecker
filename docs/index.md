# Woodpecker

Woodpecker is a lightweight, code-driven fix catalog for climate datasets. It
helps detect known dataset issues, apply small repair steps, and compose those
steps into reusable fix plans.

## Start Here

Use a discovered fix plan when you want Woodpecker to choose an ordered workflow
by id:

```python
import woodpecker

plan = woodpecker.plan.get("cmip6.core_units")
findings = woodpecker.plan.check(dataset, plan)

if findings:
    woodpecker.plan.fix(dataset, plan, dry_run=False)
```

Use direct fix selection when you already know the exact fix id:

```python
findings = woodpecker.check(
    dataset,
    fixes="woodpecker.normalize_tas_units_to_kelvin",
)
```

From the command line, list discovered plans and run one by id:

```bash
woodpecker list-plans
woodpecker check ./data --plan-id cmip6.core_units
```

## What To Read

- [Discovered Fix Plans](plans.md): how Woodpecker finds bundled, user, system,
  and explicit plan documents.
- [Plugins](plugins.md): bundled plugin status, prefixes, fixes, and plans.
- [Examples](examples.md): runnable notebooks built from deterministic
  synthetic datasets.
- [Fixes Catalog](FIXES.md): generated reference for available fixes.
- [Fix Plans](FIX_PLANS.md): generated reference for discovered plans.

For the short project introduction, use the [README](OVERVIEW.md). For
architecture and contributor details, use [CONTRIBUTING](CONTRIBUTING_GUIDE.md).
