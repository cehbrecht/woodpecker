# Examples

The examples are executed notebooks built from small deterministic synthetic
datasets. They are meant to show the public API shape without requiring real
climate files.

Use the direct API example when you want to select fixes explicitly:

- [Direct CMIP6 API](notebooks/cmip6_core_api_example.ipynb)
- [Auto Plan Store](notebooks/auto_fix_plan_store_example.ipynb)
- [FixPlanCatalog](notebooks/fix_plan_catalog_example.ipynb)

Use the fix-plan examples when you want Woodpecker to discover and load an
ordered workflow:

- [CMIP6 Fix Plan](notebooks/cmip6_core_fix_plan_example.ipynb)
- [DuckDB Plan Store](notebooks/duckdb_fix_plan_store_example.ipynb)
- [Atlas Fix Plan](notebooks/atlas_fix_plan_example.ipynb)
- [ESA CCI Fix Plan](notebooks/esa_cci_fix_plan_example.ipynb)
- [xMIP Plugin Demo](notebooks/xmip_plugin_demo.ipynb)

The auto store and catalog notebooks show exploratory plan discovery from
registered fixes and multiple plan sources. The fix-plan notebooks also show
the loaded plan content directly through `FixPlanLoader`. The DuckDB store
example loads discovered plans into a temporary DuckDB database and queries
matching plans for representative synthetic dataset IDs. The CMIP6, Atlas, ESA
CCI, and xMIP examples use core or plugin-bundled plans discovered by id.

When no explicit plan document exists, registered fixes can also be exposed as
single-step auto plans. Use the `auto` store to list or query those generated
plans, for example `woodpecker list-plans --store auto` or the Python API with
`woodpecker.plan.check(dataset, woodpecker.plan.auto("..."))`.

For exploratory workflows, `FixPlanCatalog` can combine multiple plan sources:
for example a local JSON/YAML plan store plus `AutoFixPlanStore`. Query the
catalog when you want to see curated plans and generated one-step plans through
one result list.

The notebooks use `woodpecker.testing` factories such as `make_cmip6()` and
`make_atlas()` so they can run in CI and in the documentation build.

Raw notebook files can also be viewed through
[nbviewer](https://nbviewer.org/github/cehbrecht/woodpecker/tree/main/docs/notebooks/).
