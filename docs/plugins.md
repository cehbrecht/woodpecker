# Plugins

Woodpecker keeps dataset-family behavior in plugins. Each plugin registers fixes
under a stable namespace prefix, and plugins may also bundle discovered recipes
in a package `recipes/` directory.

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

The xMIP plugin is currently a demo of an xMIP-style CMIP6 preprocessing recipe
expressed as small Woodpecker fixes:

```python
recipe = woodpecker.recipe.get("xmip.cmip6_preprocessing")
```

Use the [Generated Fixes Reference](FIXES.md) and
[Generated Recipes Reference](recipe-reference.md) for the full registered reference.

## Labels

Labels are user-facing metadata with an id, title, description, and category.
They help users understand a fix, but they do not affect recipes, priority,
matching, or automation. Some predefined labels use category `risk`; custom
labels default to category `info`, and plugins may also use category `warning`
for labels that deserve extra attention.

Plugins can use predefined risk-category labels:

```python
from woodpecker.fixes import FixFunction, RiskLabels


class RenameTempVariable(FixFunction):
    labels = [RiskLabels.REVERSIBLE_RENAME]
```

Plugins can also register custom labels:

```python
from woodpecker.fixes import register_label

register_label(
    "my_plugin.experimental",
    "experimental",
    description="Early plugin fix that should be reviewed carefully.",
    category="warning",
)
```
