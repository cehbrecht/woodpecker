# Changelog

## Unreleased

- Refactored dataset I/O into a dedicated `woodpecker.inout` package and updated API/CLI/runner to use it.
- Added optional backend model (`io`, `zarr` extras), runtime capability reporting (`io-status`), and safe fallback behavior when backends are missing.
- Improved fix execution/reporting with explicit persistence stats and JSON output for machine-readable workflows.
- Expanded quality gates with Ruff tooling, `uv` developer workflow, and CI coverage for minimal/full dependency profiles.
- Added backend-aware tests (`pytest.mark.io_backend`) and updated project/docs/Make targets to match the new workflow.
