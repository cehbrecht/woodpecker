# Design Notes

Woodpecker separates executable fixes from user-facing fix plans.

## Core Concepts

**Fix**

A fix is Python implementation code. It can be selected and applied directly through the Python API or CLI. A fix has a stable `prefix.suffix` identifier, optional aliases, metadata, and optional `matches()` / `check()` logic. Matching and checks should stay lightweight and metadata-oriented; applying the fix is the operation that changes the dataset.

Fixes can live in Woodpecker core or in plugins. Plugin fixes use the same `Fix` API and the same identifier rules. By default, the plugin package name defines the prefix, after removing the `woodpecker_` and `_plugin` parts.

**Fix plan**

A fix plan is a recipe for users. It has its own `prefix.suffix` identifier, aliases, links, match rules, and an ordered list of fix steps with options. A plan answers the question: which fixes should be applied to this kind of dataset, and in what order?

**Fix-plan document**

A fix-plan document is JSON or YAML that serializes one or more fix plans. Documents are useful for examples, sharing, versioning, and loading plans into a store.

**Fix-plan store**

A fix-plan store is a query backend for plan definitions. A store can list plans, load/save plans, look up a plan by id or alias, and return plans matching a dataset. Current stores include JSON/YAML files, DuckDB, and the read-only auto store.

**Fix-plan catalog**

A catalog is the conceptual collection of available plans. It is not a separate runtime class yet. Today the catalog can be represented by plan documents, generated documentation, or plans loaded into a `FixPlanStore`.

## Identifiers

Fixes and fix plans use the same identifier shape: `prefix.suffix`.

They live in separate lookup spaces:

- fix lookup uses `fix_id`
- plan lookup uses `plan_id`

Use clear labels in APIs and docs so users can tell whether an identifier refers to executable implementation or a recipe.

## Matching

Plan matching is intentionally extensible. Current match rules are AND-based:

- `attrs`: exact metadata key/value constraints
- `dataset_id_patterns`: wildcard patterns matched against dataset identity metadata
- `path_patterns`: wildcard patterns matched against the input path

More match rule types can be added without changing the overall plan model.

## Discovery Direction

Explicit fix plans are preferred because they provide better matching, options, links, and multi-step workflows.

Woodpecker can also expose implicit one-step plans from registered fixes through the auto store. That gives developers a simple path: implement a fix first, and add an explicit plan when the user-facing recipe needs better guidance.

Plugins should remain able to ship only fixes. If a plugin also ships fix plans later, those plans should be loaded into a `FixPlanStore` and should reference the plugin fixes by their normal `prefix.suffix` ids.
