# woodpecker-cmip6-decadal-plugin

CMIP6-decadal fixes for Woodpecker.

This plugin registers the CMIP6-decadal fix family, including:

- `cmip6_decadal.time_metadata`
- `cmip6_decadal.calendar_normalization`
- `cmip6_decadal.realization_variable`

## Install

```bash
pip install -e .
```

## Verify

```bash
woodpecker list-fixes --dataset CMIP6-decadal
pytest
```

## Example

See `examples/usage.py` for a minimal public API example using
`woodpecker.testing.make_cmip6_decadal()`.
