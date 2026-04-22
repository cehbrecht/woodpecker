# Changelog

## Unreleased

- Introduced canonical identifiers for fixes and fix plans with alias support. Simplified plan lookup and shared identifier handling across the codebase.


## 0.2.0 (2026-04-17)

- Added minimal entry-point plugin support (`woodpecker.plugins`) for external fix discovery.
- Moved dataset-specific fixes out of core and into external plugin packages, keeping only common fixes in `woodpecker`.
- Added a lightweight FixPlan abstraction (`FixRef`, `FixPlan`, `apply_plan`, `load_fix_plan`) for JSON/YAML-defined fix sequences.
- Added `FixPlanStore` backends for JSON files and DuckDB.
- Merged workflow specification/loading into `fix_plan.py`, removed `workflow.py`, and switched CLI/API usage to plan-first semantics (`--plan`, `check_plan`, `fix_plan`).

## 0.1.0 (2026-04-15)

- Moved dataset I/O into `woodpecker.inout` and wired API, CLI, and runner to use it.
- Added fix plan workflow support to drive fix selection/options from JSON or YAML.
- Added optional backend support (`io` and `zarr` extras) with `io-status` reporting and safe fallbacks.
- Improved fix reporting with persistence stats and JSON output.
- Expanded tooling and tests (Ruff, `uv` workflow, CI profiles, backend-aware tests).
