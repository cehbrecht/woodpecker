# User-Friendliness Notes

This page collects product and documentation ideas that could make Woodpecker
easier to understand, trust, and use. It reflects the current vocabulary and
highlights useful next steps.

## Lead With Recipes

Users often think in workflows rather than implementation concepts. Make
`recipe` the main user-facing word for curated, reusable repair workflows.

Example:

```bash
woodpecker fix file.nc --recipe xmip.cmip6_preprocessing
```

Possible recipe names could be oriented around user goals:

- prepare CMIP6 for xarray,
- clean CMIP6 before publishing,
- normalize xMIP-style CMIP6 preprocessing,
- clean C3S Atlas output.

In user documentation, CLI messages, and notebooks, prefer `recipe` when the
object represents a ready-to-run workflow. Contributor docs, schemas, storage
backends, and API internals should use the same vocabulary.

ESMValTool already uses the word recipe for configured analysis workflows. That
can help users understand the idea quickly, as long as Woodpecker documentation
is explicit that these are repair recipes for checking and fixing datasets, not
ESMValTool diagnostic recipes.

## Explain Fixes In Plain Language

Add an explanation surface for each fix function, for example through
`woodpecker explain`, a Python helper, or richer check output.

Good explanations should answer:

- what Woodpecker found,
- why it matters,
- what would change,
- whether the change is safe to apply automatically.

This would help users understand fixes without reading the plugin source code.

## Use One Label Model

Woodpecker has one label concept. Labels are user-facing metadata with an id,
title, description, and category. They are informational only: labels do not
affect recipe selection, fix priority, matching, or automation.

Built-in risk-related labels use ids such as:

- `risk.metadata_only`,
- `risk.reversible_rename`,
- `risk.value_transformation`,
- `risk.workflow_transformation`.

Their severity lives in the category, not in the id:

- `info`,
- `risk-low`,
- `risk-medium`,
- `risk-high`.

In code, use the predefined constants instead of raw strings:

```python
from woodpecker.fixes import Labels


class NormalizeUnits(FixFunction):
    labels = [Labels.RISK_VALUE_TRANSFORMATION]
```

Plugins can extend the same model with their own namespaced labels, for example
`my_plugin.info.experimental` or `my_plugin.risk.requires_domain_review`.
User-facing tables may show a `Severity` column, but that is only a display
view derived from label categories.

## Improve Check Output

Make the default check result easier to scan in the CLI and notebooks. Instead
of only listing ids, show grouped, human-readable findings with the planned
change when Woodpecker can infer it.

Example:

```text
3 fixes available for tas_Amon.nc

[structure] Rename CMIP6 axes
  i -> x, j -> y, longitude -> lon, latitude -> lat

[metadata] Fix known CMIP6 metadata
  branch_time_in_parent: nonsense -> 91250
```

This would make Woodpecker feel less like a low-level linter and more like a
dataset repair assistant.

## Make Dry-Run Preview First Class

Treat dry-run previews as a central trust-building feature. A preview should
summarize structured differences before any data is mutated or persisted.

Useful preview sections could include:

- attributes changed,
- variables renamed,
- coordinates added or removed,
- dimensions changed,
- encodings changed,
- data values transformed.

The preview should be available from both Python and the CLI.

## Expand Pythonic Recipe Examples

Continue developing copy-pasteable examples for the Python builder. Many
users will be more comfortable writing a small Python recipe than editing JSON
or YAML by hand.

Example direction:

```python
from woodpecker.recipes import fix, recipe

cmip6 = recipe("cmip6.cleanup").steps(
    fix("woodpecker.rename_variables", mapping={"x": ["i"], "y": ["j"]}),
    fix("woodpecker.convert_units", units={"lev": "m"}),
)
```

These examples should show how to generate JSON or YAML when users need a
shareable recipe file or contributor-facing recipe document.

## Keep User-Facing Names Simple

Use implementation terms like `FixFunction` in contributor and plugin docs, but
prefer simpler user-facing words in everyday workflows:

- check,
- fix,
- recipe,
- preview.

This keeps the public experience approachable while preserving precise terms
for developers.

## Add Interactive Selection Later

An interactive CLI could help users review and apply fixes one by one:

```bash
woodpecker check file.nc --interactive
```

This is not urgent, but it would be useful once check output and dry-run
previews are rich enough to support informed decisions.

## Highest-Impact Recommendation

The strongest next usability investment is to lead with recipes and pair them
with excellent preview and diff output. Recipes give users the right mental
model for reusable workflows; previews show exactly what Woodpecker will do
before it changes anything.
