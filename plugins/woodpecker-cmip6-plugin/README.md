# woodpecker-cmip6-plugin

CMIP6 fixes for Woodpecker.

This plugin currently registers the placeholder fix:

- `cmip6.dummy_placeholder`

## Install

```bash
pip install -e .
```

## Verify

```bash
woodpecker list-fixes --dataset CMIP6
pytest
```

## Example

See `examples/usage.py` for a minimal public API example using
`woodpecker.testing.make_cmip6()`.
