# Changelog

## Unreleased

## 0.3.0 (2026-05-11)

- Introduced `prefix.suffix` identifiers for fixes and fix plans with alias support. Simplified plan lookup and shared identifier handling across the codebase.
- Simplified identifier metadata to `prefix`, `suffix`, `id`, and `aliases`.
- Added prefix/suffix based authoring for fix-plan identifiers.
- Restored alias resolution for fix-plan lookup and added a core fix alias example.
- Added synthetic climate test data.
- Added public API integration tests for fix plans, including CMIP6, Atlas, and ESA CCI/CMIP7 examples.
- Added a CMIP6-decadal full fix plan and removed the legacy `GroupFix` recipe abstraction.
- Kept one source format per example fix plan, with the CMIP6 core plan using YAML.
- Added a generated MkDocs fix-plan catalog from the integration-test plans.
- Added notebook examples for direct fixes and fix-plan workflows.
- Added a DuckDB fix-plan store notebook showing how to load and query plan documents.
- Added design notes for fixes, fix plans, plan documents, stores, and catalogs.
- Added dataset id wildcard patterns to fix-plan matching.
- Added an integration guard that shared fix plans resolve registered core and plugin fixes.
- Render notebook examples as executed pages in the MkDocs documentation.
- Added a docs examples overview with links to rendered notebooks and nbviewer.

## 0.2.0 (2026-04-17)

- Added minimal entry-point plugin support (`woodpecker.plugins`) for external fix discovery.
- Moved dataset-specific fixes out of core and into external plugin packages, keeping only common fixes in `woodpecker`.
- Added a lightweight FixPlan abstraction (`FixRef`, `FixPlan`, `apply_plan`, `load_fix_plan`) for JSON/YAML-defined fix sequences.
- Added `FixPlanStore` backends for JSON files and DuckDB.
- Merged workflow specification/loading into `fix_plan.py`, removed `workflow.py`, and switched CLI/API usage to plan-first semantics (`--plan`, `check_plan`, `fix_plan`).

## 0.1.0 (2026-04-15)

- Moved dataset I/O into `woodpecker.io` and wired API, CLI, and runner to use it.
- Added fix plan workflow support to drive fix selection/options from JSON or YAML.
- Added optional backend support (`io` and `zarr` extras) with `io-status` reporting and safe fallbacks.
- Improved fix reporting with persistence stats and JSON output.
- Expanded tooling and tests (Ruff, `uv` workflow, CI profiles, backend-aware tests).
