# Examples

These executed notebooks use deterministic synthetic datasets, so they run in
CI and do not need real climate files.

| Need | Notebook |
| ---- | -------- |
| Run a known fix id | [Direct CMIP6 API](notebooks/cmip6_core_api_example.ipynb) |
| Run a recipe id | [CMIP6 Recipe](notebooks/cmip6_core_recipe_example.ipynb) |
| Use bundled plugin recipes | [Atlas Recipe](notebooks/atlas_recipe_example.ipynb), [ESA CCI Recipe](notebooks/esa_cci_recipe_example.ipynb), [xMIP Plugin Demo](notebooks/xmip_plugin_demo.ipynb) |
| Build recipes in Python | [Pythonic Recipe Builder](notebooks/pythonic_recipe_builder_example.ipynb) |
| Work with recipe stores | [Auto Recipe Store](notebooks/auto_recipe_store_example.ipynb), [RecipeCatalog](notebooks/recipe_catalog_example.ipynb), [DuckDB Recipe Store](notebooks/duckdb_recipe_store_example.ipynb) |

Minimal recipe shape:

```python
recipe = woodpecker.recipe.get("cmip6.core_units")
findings = woodpecker.recipe.check(dataset, recipe)
```

The notebooks use `woodpecker.testing` factories such as `make_cmip6()` and
`make_atlas()`. Raw notebook files are also available on
[nbviewer](https://nbviewer.org/github/cehbrecht/woodpecker/tree/main/docs/notebooks/).
