# Concepts

Woodpecker separates executable repair logic from the user-facing workflows
that select and order that logic.

## How The Pieces Fit

```mermaid
flowchart LR
  Dataset["Dataset or path"] --> Selection["Fix selection"]
  Selection --> Direct["Direct fix function ids"]
  Selection --> Catalog["RecipeCatalog"]
  Loader["RecipeLoader"] --> Catalog
  Core["Core recipes"] --> Loader
  Local["User/system/explicit recipes"] --> Loader
  Plugins["Installed plugin recipes"] --> Loader
  Catalog --> Recipe["Recipe"]
  Direct --> FixFunctions["Fix functions"]
  Recipe --> FixFunctions
  FixFunctions --> Result["Findings or repaired dataset"]
```

Direct fix function ids are useful when you already know exactly what to run.
Recipes are useful when a workflow should carry ordered steps, options,
matching rules, and links to background material.

## Fix Function

A fix function is an executable Python rule for one known dataset issue. It can
check whether a dataset needs attention and can optionally apply a repair.

Fix functions are registered with stable ids such as:

```text
woodpecker.normalize_tas_units_to_kelvin
cmip6_decadal.time_metadata
atlas.encoding_cleanup
```

Use direct fix function selection when you already know the exact id:

```python
findings = woodpecker.check(
    dataset,
    fixes="woodpecker.normalize_tas_units_to_kelvin",
)
```

In a recipe, a fix is a fix function plus optional runtime options. The
[Generated Fixes Reference](FIXES.md) lists registered fix functions.

Fix functions may declare a non-negative `priority` for default discovery
ordering. The default priority is `-1`, which means unprioritized. Explicit fix
recipes keep their own step order.

## Recipe

A recipe is an ordered repair workflow. It contains one or more fixes and may
also include matching rules, aliases, and links to background material.

Use recipes when you want Woodpecker to run a known workflow by id:

```python
recipe = woodpecker.recipe.get("cmip6.core_units")
findings = woodpecker.recipe.check(dataset, recipe)
```

The [Generated Recipes Reference](FIX_PLANS.md) lists discovered recipes.

## Matching

Recipes can describe when they apply to a dataset. Matching rules may inspect:

- dataset attributes,
- dataset identity metadata,
- input paths.

Matching helps shared recipes stay reusable across automated workflows. Explicit
ids still work when a user wants to choose a recipe directly.

## Recipe Store

A recipe store is a lookup layer for recipe definitions. Stores can list
recipes, load a recipe by id, and find recipes that match a dataset.

Woodpecker supports stores for:

- discovered catalog sources,
- JSON or YAML documents,
- DuckDB-backed catalogs,
- auto-generated one-step recipes from registered fix functions.

## Recipe Loader

`RecipeLoader` discovers recipe documents from common locations:

- explicit files or directories,
- `WOODPECKER_RECIPE_PATH`,
- user configuration directories,
- system configuration directories,
- core package resources,
- installed plugin package `recipes/` resources.

See [Discovered Recipes](recipes.md) for the discovery order and examples.

## Recipe Catalog

`RecipeCatalog` aggregates one or more recipe sources behind a single lookup
surface. It can list recipes, resolve ids and aliases, find matching recipes,
and deduplicate results by recipe id.

Catalog-backed lookup is the default path for shared core and plugin workflows.

## Plugins

Plugins keep dataset-family behavior outside the core package. A plugin can
register fix functions and may bundle recipe documents in a package `recipes/`
directory.

Each plugin owns a namespace prefix, for example:

| Package | Prefix |
| ------- | ------ |
| `woodpecker-atlas-plugin` | `atlas` |
| `woodpecker-cmip6-plugin` | `cmip6` |
| `woodpecker-cmip6-decadal-plugin` | `cmip6_decadal` |
| `woodpecker-cmip7-plugin` | `cmip7` |
| `woodpecker-xmip-plugin` | `xmip` |

See [Plugins](plugins.md) for bundled plugin status and recipe coverage.

## Identifiers

Fixes and recipes use stable ids in the form:

```text
prefix.suffix
```

The prefix names the owning package or plugin. The suffix names the fix or
recipe within that namespace. Use full ids in examples, recipes, and automation so
references stay explicit.

Aliases can provide extra names for the same suffix, but canonical ids are the
preferred form in documentation.
