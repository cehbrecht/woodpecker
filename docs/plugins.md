# Plugins

Woodpecker keeps dataset-family behavior in plugins. Each plugin registers fixes
under a stable namespace prefix, and plugins may also bundle discovered fix
plans in a package `plans/` directory.

| Plugin package | Prefix | Fixes | Plans | Status |
| -------------- | ------ | ----: | ----: | ------ |
| `woodpecker-atlas-plugin` | `atlas` | 2 | 1 | bundled |
| `woodpecker-cmip6-plugin` | `cmip6` | 1 | 0 | bundled |
| `woodpecker-cmip6-decadal-plugin` | `cmip6_decadal` | 15 | 1 | bundled |
| `woodpecker-cmip7-plugin` | `cmip7` | 3 | 2 | bundled |
| `woodpecker-xmip-plugin` | `xmip` | 13 | 2 | demo |

## Using Plugin Plans

Installed plugin plans are available through the same API as core plans:

```python
plan = woodpecker.plan.get("atlas.basic")
findings = woodpecker.plan.check(dataset, plan)
```

The xMIP plugin is currently a demo of an xMIP-style CMIP6 preprocessing plan
expressed as small Woodpecker fixes:

```python
plan = woodpecker.plan.get("xmip.cmip6_preprocessing")
```

Use the generated [Fixes Catalog](FIXES.md) and [Fix Plans](FIX_PLANS.md) for
the full registered reference.
