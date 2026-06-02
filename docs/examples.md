# Examples

These executed notebooks use small deterministic synthetic datasets. They show
the public API shape without requiring real climate files.

## Direct Selection

- [Direct CMIP6 API](notebooks/cmip6_core_api_example.ipynb)

Use this when you already know the fix id you want to run.

## Discovered Recipes

- [CMIP6 Recipe](notebooks/cmip6_core_recipe_example.ipynb)
- [Atlas Recipe](notebooks/atlas_recipe_example.ipynb)
- [ESA CCI Recipe](notebooks/esa_cci_recipe_example.ipynb)
- [xMIP Plugin Demo](notebooks/xmip_plugin_demo.ipynb)

Use these when you want an ordered workflow loaded by recipe id, for example:

```python
recipe = woodpecker.recipe.get("cmip6.core_units")
findings = woodpecker.recipe.check(dataset, recipe)
```

## Recipe Authoring

- [Pythonic Recipe Builder](notebooks/pythonic_recipe_builder_example.ipynb)

Use this when you want to author recipes in Python and generate the JSON/YAML
recipe document schema.

## Stores And Catalogs

- [Auto Recipe Store](notebooks/auto_recipe_store_example.ipynb)
- [RecipeCatalog](notebooks/recipe_catalog_example.ipynb)
- [DuckDB Recipe Store](notebooks/duckdb_recipe_store_example.ipynb)

Use these when you need generated one-step recipes, multiple recipe sources, or
a persistent query backend.

The notebooks use `woodpecker.testing` factories such as `make_cmip6()` and
`make_atlas()` so they can run in CI and in the documentation build.

Raw notebook files can also be viewed through
[nbviewer](https://nbviewer.org/github/cehbrecht/woodpecker/tree/main/docs/notebooks/).
