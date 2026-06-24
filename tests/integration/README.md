# Integration Tests

These are functional public API tests. They use synthetic climate datasets from
`woodpecker.testing` instead of real ESGF, CORDEX, Atlas, or CMIP files.

See [`tests/README.md`](../README.md) for the full unit/integration split.

## Scope

- `test_api_usage_examples.py`: minimal public API examples.
- `test_api_fixes_*.py`: family-specific direct fix behavior.
- `test_api_recipes_*.py`: family-specific recipe behavior.
- `test_recipe_documents.py`: reusable recipe document coverage.
- `recipes/*.json` and `recipes/*.yaml`: shared recipe assets for tests,
  notebooks, and generated docs.

## Shape

Integration tests should read like executable examples:

1. create a realistic synthetic dataset,
2. corrupt it in a realistic way,
3. check for findings,
4. dry-run the repair,
5. apply the repair,
6. confirm the issue is fixed and no longer reported.

Prefer the public API here. Use `helpers.py` only to remove repeated assertion
boilerplate.
