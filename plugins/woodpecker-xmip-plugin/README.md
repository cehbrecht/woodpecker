# woodpecker-xmip-plugin

xMIP-derived CMIP6 preprocessing fixes for Woodpecker.

This plugin registers:

- `xmip.cmip6_preprocessing`

The implementation is adapted from the original xMIP `combined_preprocessing`
pipeline at `/Users/pingu/Documents/GitHub/misc/xMIP`. It focuses on
Woodpecker-compatible structural and metadata cleanup:

- normalize common CMIP6 dimension and coordinate names
- promote bare dimensions to coordinates
- mark known spatial coordinates as coordinates
- broadcast 1D lon/lat to 2D
- wrap longitudes to the 0-360 convention
- normalize lon/lat bounds and vertex-style coordinates
- apply selected GFDL-CM4 branch-time metadata corrections
- drop helper `bnds` and `vertex` coordinates

The xMIP unit-conversion step is intentionally not included here, because it
requires optional pint dependencies that the existing Woodpecker plugins do not
otherwise need.

## Install

```bash
pip install -e .
```

## Verify

```bash
woodpecker list-fixes --dataset CMIP6
pytest
```

You should see `xmip.cmip6_preprocessing` after installation.
