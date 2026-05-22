# Examples

These executed notebooks use small deterministic synthetic datasets. They show
the public API shape without requiring real climate files.

## Direct Selection

- [Direct CMIP6 API](notebooks/cmip6_core_api_example.ipynb)

Use this when you already know the fix id you want to run.

## Discovered Plans

- [CMIP6 Fix Plan](notebooks/cmip6_core_fix_plan_example.ipynb)
- [Atlas Fix Plan](notebooks/atlas_fix_plan_example.ipynb)
- [ESA CCI Fix Plan](notebooks/esa_cci_fix_plan_example.ipynb)
- [xMIP Plugin Demo](notebooks/xmip_plugin_demo.ipynb)

Use these when you want an ordered workflow loaded by plan id, for example:

```python
plan = woodpecker.plan.get("cmip6.core_units")
findings = woodpecker.plan.check(dataset, plan)
```

## Stores And Catalogs

- [Auto Plan Store](notebooks/auto_fix_plan_store_example.ipynb)
- [FixPlanCatalog](notebooks/fix_plan_catalog_example.ipynb)
- [DuckDB Plan Store](notebooks/duckdb_fix_plan_store_example.ipynb)

Use these when you need generated one-step plans, multiple plan sources, or a
persistent query backend.

The notebooks use `woodpecker.testing` factories such as `make_cmip6()` and
`make_atlas()` so they can run in CI and in the documentation build.

Raw notebook files can also be viewed through
[nbviewer](https://nbviewer.org/github/cehbrecht/woodpecker/tree/main/docs/notebooks/).
