# Changelog

## Unreleased

## 0.1.0 (2026-04-15)

- Moved dataset I/O into `woodpecker.inout` and wired API, CLI, and runner to use it.
- Added fix plan workflow support to drive fix selection/options from JSON or YAML.
- Added optional backend support (`io` and `zarr` extras) with `io-status` reporting and safe fallbacks.
- Improved fix reporting with persistence stats and JSON output.
- Expanded tooling and tests (Ruff, `uv` workflow, CI profiles, backend-aware tests).
