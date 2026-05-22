# woodpecker-xmip-plugin

xMIP-derived CMIP6 preprocessing fixes for Woodpecker.

This plugin registers small, composable fixes:

- `xmip.rename_cmip6_axes`
- `xmip.mark_spatial_coords`
- `xmip.broadcast_lon_lat`
- `xmip.normalize_coordinate_units`
- `xmip.replace_xy_with_nominal_lon_lat`
- `xmip.normalize_lon_lat_bounds`
- `xmip.sort_vertex_order`
- `xmip.convert_bounds_to_vertices`
- `xmip.convert_vertices_to_bounds`
- `xmip.fix_known_cmip6_metadata`
- `xmip.drop_helper_grid_coords`

It also ships a plan:

- `xmip.cmip6_preprocessing`
- `xmip.cmip6_preprocessing_nominal_xy`

Core-owned replacements used by the plan:

- `woodpecker.promote_missing_dimension_coords`
- `woodpecker.normalize_longitude_convention`

The implementation is adapted from the original xMIP `combined_preprocessing`
pipeline at `/Users/pingu/Documents/GitHub/misc/xMIP`, but expressed in a more
Woodpecker-native way: one readable fix per concern, composed by a fix plan.
It focuses on Woodpecker-compatible structural and metadata cleanup:

- normalize common CMIP6 dimension and coordinate names
- promote bare dimensions to coordinates
- mark known spatial coordinates as coordinates
- broadcast 1D lon/lat to 2D
- wrap longitudes to the 0-360 convention
- normalize supported coordinate units, currently `lev` to meters
- optionally replace x/y coordinates with nominal lon/lat-derived values
- normalize lon/lat bounds and vertex-style coordinates
- apply selected GFDL-CM4 branch-time metadata corrections
- drop helper `bnds` and `vertex` coordinates

The xMIP unit-conversion step is included for supported coordinates. The plugin
declares `cf_xarray`, `pint`, and `pint-xarray` so installed environments can use
the same unit machinery as xMIP; a small built-in fallback covers simple `lev`
centimeter-to-meter conversion in lightweight development environments.

## Install

```bash
pip install -e .
```

## Verify

```bash
woodpecker list-fixes --dataset CMIP6
pytest
```

You should see `xmip.*` fixes after installation. The plan lives at
`src/woodpecker_xmip_plugin/plans/cmip6_preprocessing.yaml`.
