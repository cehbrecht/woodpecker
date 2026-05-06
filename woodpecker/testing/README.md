# Synthetic Climate Test Data

`woodpecker.testing` provides tiny synthetic `xarray.Dataset` factories for
tests, examples, docs, and CI.

The datasets are not real source data, but they are shaped to look like common
climate-data families that Woodpecker needs to understand:

- `make_cmip6()`
- `make_cmip6_decadal()`
- `make_cmip7()`
- `make_atlas()`
- `make_cordex()`

Each factory returns a small dataset with realistic coordinates, variable
metadata, and global attributes. Defaults are intentionally CI-friendly:
`time=12`, `lat=18`, and `lon=36`.

## Basic Usage

```python
from woodpecker.testing import make_cmip6

dataset = make_cmip6()
```

Factories are deterministic by default. Passing a seed adds repeatable
perturbations:

```python
first = make_cmip6(seed=10)
second = make_cmip6(seed=10)
```

## Broken Datasets

Use the corruption options to create realistic broken inputs for fix tests:

```python
from woodpecker.testing import make_cmip6

dataset = make_cmip6(
    missing=["units"],
    overrides={"experiment_id": "ssp585"},
    rename_vars={"tas": "temperature"},
)
```

The corruption API is the same across all public factories:

- `missing=` removes global attrs and matching variable attrs.
- `overrides=` replaces global attrs. `units` is also mirrored to variable attrs.
- `rename_vars=` renames data variables.

## Design Notes

Keep this package independent from runtime IO. It should create in-memory
datasets only, without downloads or access to real climate archives.

Prefer adding realistic metadata to these factories before hand-building large
`xarray.Dataset` fixtures in tests. Small, readable synthetic datasets usually
make better tests than large custom fixtures.
