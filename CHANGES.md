# Changelog

## Unreleased

## 0.5.0 (2026-06-24)

- Renamed fix-plan terminology and public surfaces to recipe terminology across code, CLI, tests, docs, and bundled examples.
- Added a Pythonic recipe builder API and example notebook.
- Added labels for fix risks and informational metadata, including registry, formatting, and generated catalog support.
- Added preview support for fix outputs in the API, CLI, notebooks, and xMIP plugin workflow.
- Updated the bundled plugin packages, recipes, tests, and examples for the `0.5.x` core dependency range.
- Expanded recipe loader, recipe builder, store, registry, runner, selection, provenance, and UI formatting tests.
- Refreshed generated fix and recipe reference artifacts, docs navigation, notebooks, and design notes.
- Updated the docs build workflow and local docs generation commands.

## 0.4.0 (2026-05-26)

- Renamed the internal `woodpecker.recipes` package to `woodpecker.recipes`.
- Simplified the public Python API to direct `woodpecker.check/fix(..., fixes=...)` and recipe-backed `woodpecker.recipe.check/fix(...)`.
- Added a read-only auto recipe store that exposes registered fixes as single-step recipes.
- Added API, CLI, and integration examples for auto recipes.
- Added a prototype `RecipeCatalog` for querying multiple recipe sources together.
- Added notebook examples for the auto store and `RecipeCatalog`.
- Added `RecipeLoader` discovery for core, plugin, user, system, environment, and explicit recipe sources.
- Added the bundled xMIP demo plugin for inspectable CMIP6 preprocessing fixes and recipes.
- Added generated MkDocs reference pages for registered fixes and discovered recipes.
- Added an interactive fix browser with searchable fix ids and stable anchors.
- Added dedicated Concepts, CLI, and Docs Development pages.
- Refined the README and MkDocs homepage so the README is a compact project entry point and the docs homepage is task-oriented.
- Updated bundled plugin packages for the `0.4.x` core dependency range.

## 0.3.0 (2026-05-11)

- Introduced `prefix.suffix` identifiers for fixes and recipes with alias support. Simplified recipe lookup and shared identifier handling across the codebase.
- Simplified identifier metadata to `prefix`, `suffix`, `id`, and `aliases`.
- Added prefix/suffix based authoring for recipe identifiers.
- Restored alias resolution for recipe lookup and added a core fix alias example.
- Added synthetic climate test data.
- Added public API integration tests for recipes, including CMIP6, Atlas, and ESA CCI/CMIP7 examples.
- Added a CMIP6-decadal full recipe and removed the legacy `GroupFix` recipe abstraction.
- Kept one source format per example recipe, with the CMIP6 core recipe using YAML.
- Added a generated MkDocs recipe catalog from the integration-test recipes.
- Added notebook examples for direct fixes and recipe workflows.
- Added a DuckDB recipe store notebook showing how to load and query recipe documents.
- Added design notes for fixes, recipes, recipe documents, stores, and catalogs.
- Added dataset id wildcard patterns to recipe matching.
- Added an integration guard that shared recipes resolve registered core and plugin fixes.
- Render notebook examples as executed pages in the MkDocs documentation.
- Added a docs examples overview with links to rendered notebooks and nbviewer.

## 0.2.0 (2026-04-17)

- Added minimal entry-point plugin support (`woodpecker.plugins`) for external fix discovery.
- Moved dataset-specific fixes out of core and into external plugin packages, keeping only common fixes in `woodpecker`.
- Added a lightweight Recipe abstraction (`FixRef`, `Recipe`, `apply_plan`, `load_recipe`) for JSON/YAML-defined fix sequences.
- Added `RecipeStore` backends for JSON files and DuckDB.
- Merged workflow specification/loading into `fix_recipe.py`, removed `workflow.py`, and switched CLI/API usage to recipe-first semantics (`--recipe`, `check_plan`, `fix_plan`).

## 0.1.0 (2026-04-15)

- Moved dataset I/O into `woodpecker.io` and wired API, CLI, and runner to use it.
- Added recipe workflow support to drive fix selection/options from JSON or YAML.
- Added optional backend support (`io` and `zarr` extras) with `io-status` reporting and safe fallbacks.
- Improved fix reporting with persistence stats and JSON output.
- Expanded tooling and tests (Ruff, `uv` workflow, CI profiles, backend-aware tests).
