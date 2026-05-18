# woodpecker-cmip7-plugin

CMIP7-style fixes for Woodpecker.

This plugin registers:

- `cmip7.ensure_project_id_present`
- `cmip7.rename_temp_variable_to_tas`
- `cmip7.configurable_reformat_bridge`

## Install

```bash
pip install -e .
```

## Verify

```bash
woodpecker list-fixes --dataset CMIP7
pytest
```

You should see `cmip7.*` fixes after installation.

## Example

See `examples/usage.py` for a minimal public API example using
`woodpecker.testing.make_cmip7()`.
