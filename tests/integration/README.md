# Integration Tests

These tests exercise Woodpecker end to end through the public Python API.

They intentionally use synthetic climate datasets from `woodpecker.testing`
instead of hand-built `xarray.Dataset` fixtures or real ESGF/CORDEX/Atlas data.
That keeps the suite fast and deterministic while still making the inputs look
like real climate files.

## Scope

The integration suite covers two public API styles:

- direct fix selection with `source=woodpecker.Fixes(...)`,
- plan-driven selection with `source=woodpecker.FixPlan(...)`.
- auto plan selection with the read-only `auto` store when a fix has no
  curated plan document yet.

Files are grouped by dataset family or example role:

- `test_api_usage_examples.py`: minimal, plain public API examples for direct
  fixes, fix plans, and auto plans.
- `test_api_fixes_*.py`: family-specific fix behavior against synthetic data.
- `test_api_plans_*.py`: family-specific fix-plan behavior against synthetic
  data.
- `plans/*.json` and `plans/*.yaml`: plan documents used by plan integration
  tests, notebooks, and the generated fix-plan docs catalog.

## Test Shape

The integration tests should read like executable examples:

1. create a realistic synthetic dataset,
2. corrupt it in a realistic way,
3. call `woodpecker.check(..., source=...)`,
4. call `woodpecker.fix(..., source=..., write=False)` for a dry run,
5. call `woodpecker.fix(..., source=..., write=True)` to apply the fix,
6. check that the dataset is corrected and the finding is gone.

Prefer the public API here. Avoid reaching into registries, runners, stores, or
fix internals unless a test is explicitly about those lower-level pieces.

The helper functions in `helpers.py` only remove repeated assertion boilerplate.
When adding a new dataset family or demonstrating a new API pattern, prefer a
plain test first. `test_api_usage_examples.py` is the deliberately minimal
reference for that style.

Keep reusable example plan documents in `plans/` when they are also useful to
notebooks or docs. Use temporary inline plans only for tests that need a special
case, such as plan options or ambiguity handling.
