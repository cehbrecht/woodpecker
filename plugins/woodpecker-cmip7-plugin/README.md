# woodpecker-cmip7-plugin

Reference external plugin package for Woodpecker.

This package is the canonical CMIP7 fix source for Woodpecker and provides
`CMIP7_0001`, `CMIP7_0002`, and `CMIP7_0003`.

## Install

```bash
pip install -e .
```

## Verify

```bash
woodpecker list-fixes --dataset CMIP7
```

You should see `CMIP7_*` fixes after installation.
