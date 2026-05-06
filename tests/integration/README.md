# Integration Tests

These tests exercise Woodpecker end to end through the public Python API.

They intentionally use synthetic climate datasets from `woodpecker.testing`
instead of hand-built `xarray.Dataset` fixtures or real ESGF/CORDEX/Atlas data.
That keeps the suite fast and deterministic while still making the inputs look
like real climate files.

The integration tests should read like executable examples:

1. create a realistic synthetic dataset,
2. corrupt it in a realistic way,
3. call `woodpecker.check(...)` or `woodpecker.check_plan(...)`,
4. call `woodpecker.fix(..., write=False)` or `woodpecker.fix_plan(..., write=False)` for a dry run,
5. call `woodpecker.fix(..., write=True)` or `woodpecker.fix_plan(..., write=True)` to apply the fix,
6. check that the dataset is corrected and the finding is gone.

Prefer the public API here. Avoid reaching into registries, runners, stores, or
fix internals unless a test is explicitly about those lower-level pieces.

The helper functions in `helpers.py` only remove repeated assertion boilerplate.
When adding a new dataset family or demonstrating a new API pattern, prefer a
plain test first. `test_api_usage_examples.py` is the deliberately minimal
reference for that style.
