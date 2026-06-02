# Integration Tests

These tests exercise Woodpecker end to end through the public Python API.

They intentionally use synthetic climate datasets from `woodpecker.testing`
instead of hand-built `xarray.Dataset` fixtures or real ESGF/CORDEX/Atlas data.
That keeps the suite fast and deterministic while still making the inputs look
like real climate files.

## Scope

The integration suite covers two public API styles:

- direct fix selection with `woodpecker.check(..., fixes=...)` and `woodpecker.fix(..., fixes=...)`,
- recipe-driven selection with `woodpecker.recipe.check(...)` and `woodpecker.recipe.fix(...)`.
- auto recipe selection with the read-only `auto` store when a fix has no
  curated recipe document yet.

Files are grouped by dataset family or example role:

- `test_api_usage_examples.py`: minimal, plain public API examples for direct
  fixes, fix recipes, and auto recipes.
- `test_api_fixes_*.py`: family-specific fix behavior against synthetic data.
- `test_api_recipes_*.py`: family-specific fix-recipe behavior against synthetic
  data.
- `recipes/*.json` and `recipes/*.yaml`: recipe documents used by recipe integration
  tests, notebooks, and the generated fix-recipe docs catalog.

## Test Shape

The integration tests should read like executable examples:

1. create a realistic synthetic dataset,
2. corrupt it in a realistic way,
3. call `woodpecker.check(...)` or `woodpecker.recipe.check(...)`,
4. call `woodpecker.fix(..., dry_run=True)` or `woodpecker.recipe.fix(..., dry_run=True)` for a dry run,
5. call `woodpecker.fix(..., dry_run=False)` or `woodpecker.recipe.fix(..., dry_run=False)` to apply the fix,
6. check that the dataset is corrected and the finding is gone.

Prefer the public API here. Avoid reaching into registries, runners, stores, or
fix internals unless a test is explicitly about those lower-level pieces.

The helper functions in `helpers.py` only remove repeated assertion boilerplate.
When adding a new dataset family or demonstrating a new API pattern, prefer a
plain test first. `test_api_usage_examples.py` is the deliberately minimal
reference for that style.

Keep reusable example recipe documents in `recipes/` when they are also useful to
notebooks or docs. Use temporary inline recipes only for tests that need a special
case, such as recipe options or ambiguity handling.
