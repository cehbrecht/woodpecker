# Woodpecker

[![CI](https://github.com/macpingu/woodpecker/actions/workflows/ci.yml/badge.svg)](https://github.com/macpingu/woodpecker/actions/workflows/ci.yml)
[![Docs](https://github.com/macpingu/woodpecker/actions/workflows/docs.yml/badge.svg)](https://github.com/macpingu/woodpecker/actions/workflows/docs.yml)

Woodpecker is a small, code-based catalog of dataset fixes for climate workflows.
Each fix has a stable code (for example `CMIP6D_0001`) so tools and services can reference it directly.

Contributor and developer docs live in `CONTRIBUTING.md`.

## Quickstart

Recommended setup:

```bash
conda env create -f environment.yml
conda activate woodpecker
make install
make list-fixes
```

Pip-only setup:

```bash
pip install -e .
woodpecker list-fixes
```

Optional extras:

```bash
pip install -e ".[io]"       # NetCDF backends
pip install -e ".[zarr]"     # Zarr backend
pip install -e ".[io,zarr]"  # both
```

If a backend is missing (for example Zarr without `.[zarr]`), Woodpecker warns and reports persistence failure in fix stats.

## Usage

Flow: `discover fixes -> check findings -> apply selected fixes`.

Core commands:

```bash
woodpecker list-fixes
woodpecker check . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001 --dry-run
```

Advanced options (`--workflow`, `--force-apply`, output formats, JSON output) are in `CONTRIBUTING.md`.

## Example

```bash
touch cmip6_case.nc
woodpecker check . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001
woodpecker fix . --select CMIP6D_0001 --dry-run
```

## GitHub Pages

This repository includes a workflow that builds and deploys the MkDocs site to GitHub Pages.
After enabling Pages in repo settings, fix codes are available as direct links (for example `.../fixes.html#CMIP6D_0001`).
