# Woodpecker

**Small, precise fixes for climate data.**

[![CI](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/ci.yml)
[![Docs](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml/badge.svg)](https://github.com/cehbrecht/woodpecker/actions/workflows/docs.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://github.com/cehbrecht/woodpecker/blob/main/pyproject.toml)
[![License](https://img.shields.io/github/license/cehbrecht/woodpecker)](https://github.com/cehbrecht/woodpecker/blob/main/LICENSE)

Like the bird caring for a forest by finding hidden bugs, Woodpecker cares for
climate data by finding known data bugs and applying focused fixes.

It brings repair scripts, workarounds, plugins, and fix plans under one simple
API for checking, applying, composing, and discovering climate data fixes.

## Common Paths

**Check a dataset**  
Run known fixes directly when you already know the fix id. Start with the
[Fixes Catalog](FIXES.md).

**Learn the model**  
Read the core vocabulary for fixes, plans, stores, catalogs, plugins, and ids.
Start with [Concepts](concepts.md).

**Run a discovered plan**  
Load an ordered workflow from core, plugin, user, or system plan sources. Start
with [Discovered Fix Plans](plans.md).

**Browse plugins**  
See bundled dataset-family plugins, prefixes, fixes, and plan coverage. Start
with [Plugins](plugins.md).

**Explore examples**  
Open executed notebooks built from deterministic synthetic climate datasets.
Start with [Examples](examples.md).

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

- [Concepts](concepts.md): the core vocabulary for fixes, plans, stores,
  catalogs, plugins, and identifiers.
- [Discovered Fix Plans](plans.md): how Woodpecker finds bundled, user, system,
  and explicit plan documents.
- [Plugins](plugins.md): bundled plugin status, prefixes, fixes, and plans.
- [Examples](examples.md): runnable notebooks built from deterministic
  synthetic datasets.
- [Fixes Catalog](FIXES.md): generated reference for available fixes.
- [Fix Plans](FIX_PLANS.md): generated reference for discovered plans.

The xMIP plugin is currently a demo plugin that translates xMIP-style CMIP6
preprocessing into small, inspectable Woodpecker fixes.

For the longer project overview, read [Overview](OVERVIEW.md). For
architecture and contributor details, read the
[Contributing Guide](CONTRIBUTING_GUIDE.md).
