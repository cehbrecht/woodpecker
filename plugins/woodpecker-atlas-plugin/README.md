# woodpecker-atlas-plugin

ATLAS fixes for Woodpecker.

This plugin registers:

- `atlas.encoding_cleanup`
- `atlas.project_id_normalization`

## Install

```bash
pip install -e .
```

## Verify

```bash
woodpecker list-fixes --dataset ATLAS
pytest
```

## Example

See `examples/usage.py` for a minimal public API example using
`woodpecker.testing.make_atlas()`.
