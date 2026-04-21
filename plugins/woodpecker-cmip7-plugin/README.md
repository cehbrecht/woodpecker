# woodpecker-cmip7-plugin

Reference external plugin package for Woodpecker.

This package is the canonical CMIP7 fix source for Woodpecker and provides
`cmip7.ensure_project_id_present`, `cmip7.rename_temp_variable_to_tas`, and
`cmip7.configurable_reformat_bridge`.

## Install

```bash
pip install -e .
```

## Verify

```bash
woodpecker list-fixes --dataset CMIP7
```

You should see `CMIP7_*` fixes after installation.
You should see `cmip7.*` fixes after installation.
