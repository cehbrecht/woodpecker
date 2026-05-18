# Examples

The examples are executed notebooks built from small deterministic synthetic
datasets. They are meant to show the public API shape without requiring real
climate files.

Use the direct API example when you want to select fixes explicitly:

- [Direct CMIP6 API](notebooks/cmip6_core_api_example.ipynb)
- [Auto Plan Store](notebooks/auto_fix_plan_store_example.ipynb)
- [FixPlanCatalog](notebooks/fix_plan_catalog_example.ipynb)

Use the fix-plan examples when you want Woodpecker to load an ordered workflow
from a plan document:

- [CMIP6 Fix Plan](notebooks/cmip6_core_fix_plan_example.ipynb)
- [DuckDB Plan Store](notebooks/duckdb_fix_plan_store_example.ipynb)
- [Atlas Fix Plan](notebooks/atlas_fix_plan_example.ipynb)
- [ESA CCI Fix Plan](notebooks/esa_cci_fix_plan_example.ipynb)

The auto store and catalog notebooks show exploratory plan discovery from
registered fixes and multiple plan sources. The fix-plan notebooks also show
the loaded plan content directly. The DuckDB
store example loads all shared plan fixtures into a temporary DuckDB database
and queries matching plans for representative synthetic dataset IDs. The CMIP6
fix-plan notebook loads a shared YAML plan fixture from
`tests/integration/plans/cmip6_core_plan.yaml`, while the Atlas and ESA CCI
examples load JSON fixtures. This exercises JSON, YAML, and DuckDB-backed plan
workflows in documentation builds.

When no explicit plan document exists, registered fixes can also be exposed as
single-step auto plans. Use the `auto` store to list or query those generated
plans, for example `woodpecker list-plans --store auto` or the Python API with
`woodpecker.check(dataset, source=woodpecker.FixPlan.auto("..."))`.

For exploratory workflows, `FixPlanCatalog` can combine multiple plan sources:
for example a local JSON/YAML plan store plus `AutoFixPlanStore`. Query the
catalog when you want to see curated plans and generated one-step plans through
one result list.

The notebooks use `woodpecker.testing` factories such as `make_cmip6()` and
`make_atlas()` so they can run in CI and in the documentation build. The
fix-plan documents are shared with integration tests and live in
`tests/integration/plans/`.

Raw notebook files can also be viewed through
[nbviewer](https://nbviewer.org/github/cehbrecht/woodpecker/tree/main/docs/notebooks/).
