# Tests

Woodpecker has two test layers:

| Layer | Path | Purpose | Run when... |
| ----- | ---- | ------- | ----------- |
| Unit | `tests/unit/` | Small, focused checks for parsing, identifiers, recipes, stores, selection, provenance, formatting, CLI option forwarding, and fix internals. | You change one module or low-level contract. |
| Integration | `tests/integration/` | Functional public API flows using synthetic climate datasets. | You change check/fix behavior, recipes, plugins, stores, or user-facing workflows. |

Run all tests with:

```bash
make test
```

Run one layer with:

```bash
pytest tests/unit
pytest tests/integration
```

## What Belongs Where

Put a test in `tests/unit/` when it can use small fixtures, mocks, or direct
model objects and does not need a full check/fix workflow.

Put a test in `tests/integration/` when it should read like a user workflow:

1. create or load a realistic synthetic dataset,
2. corrupt it in a realistic way,
3. call `woodpecker.check(...)` or `woodpecker.recipe.check(...)`,
4. call `woodpecker.fix(..., dry_run=True)` or `woodpecker.recipe.fix(..., dry_run=True)`,
5. apply with `dry_run=False`,
6. confirm the issue is fixed and no longer reported.

Keep `tests/integration/test_api_usage_examples.py` as the plain style
reference for public API examples.

## Duplication Audit

Keep these overlaps intentional:

- CLI unit tests cover option parsing, error handling, JSON/text output shape,
  and forwarding flags into command execution.
- Integration tests cover public API behavior after selection has resolved.
- Fix unit tests cover individual fix matching and mutation details.
- Family integration tests cover one representative end-to-end cycle per
  dataset family or workflow.
- Recipe/store unit tests cover schema, matching, aliases, and backend behavior.
- Recipe integration tests cover recipe-driven public API flows with real
  registered fixes.

Before adding a new test, check whether it is:

- a low-level edge case already covered by a unit test,
- a broad workflow that belongs in integration instead of unit,
- another copy of an existing check/dry-run/apply cycle.

## Cache Files

`__pycache__/`, `.pytest_cache/`, and Python bytecode files are ignored by
`.gitignore`. They may appear locally after test runs but should not be tracked.
