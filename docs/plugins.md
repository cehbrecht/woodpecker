# Plugins

Woodpecker keeps dataset-family behavior in plugins. Plugins register fixes
under a stable namespace prefix and may bundle recipes in a package `recipes/`
directory.

| Plugin package | Prefix | Fixes | Recipes | Status |
| -------------- | ------ | ----: | ----: | ------ |
| `woodpecker-atlas-plugin` | `atlas` | 2 | 1 | bundled |
| `woodpecker-cmip6-plugin` | `cmip6` | 1 | 0 | bundled |
| `woodpecker-cmip6-decadal-plugin` | `cmip6_decadal` | 15 | 1 | bundled |
| `woodpecker-cmip7-plugin` | `cmip7` | 3 | 2 | bundled |
| `woodpecker-xmip-plugin` | `xmip` | 13 | 2 | demo |

## Using Plugin Recipes

Installed plugin recipes are available through the same API as core recipes:

```python
recipe = woodpecker.recipe.get("atlas.basic")
findings = woodpecker.recipe.check(dataset, recipe)
```

The xMIP plugin is a demo of an xMIP-style CMIP6 preprocessing recipe expressed
as small Woodpecker fixes:

```python
recipe = woodpecker.recipe.get("xmip.cmip6_preprocessing")
```

Use [Fix Reference](FIXES.md) and [Recipe Reference](recipe-reference.md) for
the full registered list.

## Labels

Labels are user-facing metadata for fixes.

| Field | Purpose |
| ----- | ------- |
| id | Stable label identifier. |
| title | Short user-facing name. |
| description | Longer explanation. |
| category | Group such as `info`, `risk-low`, `risk-medium`, or `risk-high`. |

Labels help users understand a fix. They do not affect recipes, priority,
matching, or automation.

Plugins can use predefined labels:

```python
from woodpecker.fixes import FixFunction, Labels


class RenameTempVariable(FixFunction):
    labels = [Labels.RISK_REVERSIBLE_RENAME]
```

Plugins can also register custom labels:

```python
from woodpecker.fixes import LabelCategories, register_label

register_label(
    "my_plugin.experimental",
    "experimental",
    description="Early plugin fix that should be reviewed carefully.",
    category=LabelCategories.RISK_HIGH,
)
```
