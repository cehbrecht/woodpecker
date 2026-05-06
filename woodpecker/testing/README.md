# Synthetic Climate Test Data

`woodpecker.testing` provides tiny synthetic `xarray.Dataset` factories for
tests, examples, docs, and CI.

Synthetic dataset generation logic lives in the
`woodpecker.testing.synthetic` subpackage.

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

## Import Guidance

Use these canonical public imports in tests and examples:

```python
from woodpecker.testing import make_cmip6, make_cmip7, make_atlas, make_cordex
```

Use internals from `woodpecker.testing.synthetic` only when extending the
testing package itself.

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

## API Stability

The package-level names exported by `woodpecker.testing` are the stable public
API for test code in this repository.

Modules under `woodpecker.testing.synthetic` are internal implementation
details and may change when synthetic generation internals evolve.
