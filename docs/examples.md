# Examples

The examples are executed notebooks built from small deterministic synthetic
datasets. They are meant to show the public API shape without requiring real
climate files.

Use the direct API example when you want to select fixes explicitly:

- [Direct CMIP6 API](notebooks/cmip6_core_api_example.ipynb)

Use the fix-plan examples when you want Woodpecker to load an ordered workflow
from a plan document:

- [CMIP6 Fix Plan](notebooks/cmip6_core_fix_plan_example.ipynb)
- [DuckDB Plan Store](notebooks/duckdb_fix_plan_store_example.ipynb)
- [Atlas Fix Plan](notebooks/atlas_fix_plan_example.ipynb)
- [ESA CCI Fix Plan](notebooks/esa_cci_fix_plan_example.ipynb)

The fix-plan notebooks also show the loaded plan content directly. The DuckDB
store example loads all shared plan fixtures into a temporary DuckDB database
and queries matching plans for representative synthetic dataset IDs. The CMIP6
fix-plan notebook loads a shared YAML plan fixture from
`tests/integration/plans/cmip6_core_plan.yaml`, while the Atlas and ESA CCI
examples load JSON fixtures. This exercises JSON, YAML, and DuckDB-backed plan
workflows in documentation builds.

The notebooks use `woodpecker.testing` factories such as `make_cmip6()` and
`make_atlas()` so they can run in CI and in the documentation build. The
fix-plan documents are shared with integration tests and live in
`tests/integration/plans/`.

Raw notebook files can also be viewed through
[nbviewer](https://nbviewer.org/github/cehbrecht/woodpecker/tree/main/docs/notebooks/).
