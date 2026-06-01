# User Friendliness Ideas

This page collects product and documentation ideas that could make Woodpecker
easier to understand, trust, and use. These are recommendations for later work,
not current feature guarantees.

## Explain Fixes In Plain Language

Add an explanation surface for each fix function, for example through
`woodpecker explain`, a Python helper, or richer check output.

Good explanations should answer:

- what Woodpecker found,
- why it matters,
- what would change,
- whether the change is safe to apply automatically.

This would help users understand fixes without reading the plugin source code.

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

## Expand Pythonic Plan Builder Examples

Continue developing copy-pasteable examples for the Python plan builder. Many
users will be more comfortable writing a small Python recipe than editing JSON
or YAML by hand.

Example direction:

```python
from woodpecker.fix_plans import fix, plan

cmip6 = plan("cmip6.cleanup").steps(
    fix("woodpecker.rename_variables", mapping={"x": ["i"], "y": ["j"]}),
    fix("woodpecker.convert_units", units={"lev": "m"}),
)
```

These examples should show how to generate JSON or YAML when users need a
shareable plan file.

## Introduce Recipes Or Profiles

Users often think in workflows rather than implementation concepts. Consider
using user-facing terms such as recipes or profiles for curated plans.

Example:

```bash
woodpecker fix file.nc --recipe xmip.cmip6_preprocessing
```

Possible recipe names could be oriented around user goals:

- prepare CMIP6 for xarray,
- clean CMIP6 before publishing,
- normalize xMIP-style CMIP6 preprocessing,
- clean C3S Atlas output.

Internally these recipes can still be fix plans.

## Add Confidence Or Risk Labels

Fix functions could advertise a simple risk level so users know when automation
is appropriate.

Possible labels:

- safe: metadata only,
- safe: reversible rename,
- careful: coordinate interpolation,
- careful: value transformation.

Risk labels would be useful in check output, dry-run previews, plan references,
and interactive workflows.

## Keep User-Facing Names Simple

Use implementation terms like `FixFunction` in contributor and plugin docs, but
prefer simpler user-facing words in everyday workflows:

- check,
- fix,
- plan,
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

The strongest next usability investment is excellent preview and diff output.
If users can see exactly what Woodpecker will do before it changes anything,
they can build trust in the tool much faster.
