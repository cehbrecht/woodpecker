# woodpecker-cmip7-plugin

Reference external plugin package for Woodpecker.

This package is the canonical CMIP7 fix source for Woodpecker and provides
`cmip7.0001`, `cmip7.0002`, and `cmip7.0003`.

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
