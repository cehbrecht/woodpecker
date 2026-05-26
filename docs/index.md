# Woodpecker Documentation

Woodpecker helps climate-data workflows check, select, and apply known dataset
fixes through a small Python API, a CLI, and discoverable fix plans.

Use this documentation site as a map. The [Overview](OVERVIEW.md) is the short
project introduction; the pages below are organized by what you want to do next.

## If You Are Running Fixes

Start here when you have a dataset and want to check or repair it.

- [Concepts](concepts.md): learn the vocabulary for fixes, plans, stores,
  catalogs, plugins, and identifiers.
- [Discovered Fix Plans](plans.md): run an ordered workflow from core, plugin,
  user, or system plan sources.
- [CLI](cli.md): inspect fixes and plans, check datasets, apply fixes, and use
  output or safety flags from the terminal.
- [Examples](examples.md): open executed notebooks using deterministic synthetic
  datasets.
- [Generated Fixes Reference](FIXES.md): find registered fix ids for direct
  selection.
- [Interactive Fix Browser](fixes.html): search fix ids and copy stable anchors.

Typical plan-based usage:

```python
import woodpecker

plan = woodpecker.plan.get("cmip6.core_units")
findings = woodpecker.plan.check(dataset, plan)

if findings:
    woodpecker.plan.fix(dataset, plan, dry_run=False)
```

Typical CLI usage:

```bash
woodpecker list-plans
woodpecker check ./data --plan-id cmip6.core_units
```

See [CLI](cli.md) for direct fix selection, store backends, dry runs,
provenance, strict I/O, and output formats.

## If You Are Choosing A Workflow

Start with [Discovered Fix Plans](plans.md) when you want Woodpecker to select a
curated recipe by id or matching rules.

Use the [Generated Fix Plans Reference](FIX_PLANS.md) when you want a generated
table of currently discovered plans, their match rules, steps, and source files.

Use the [Generated Fixes Reference](FIXES.md) when you already know you need a
single fix id or want to inspect all registered fixes.

## If You Are Working With Plugins

Start with [Plugins](plugins.md) for bundled plugin status, namespace prefixes,
fix counts, and plan coverage.

Plugins can register fixes and may bundle fix-plan documents in package
`plans/` resources. Installed plugin plans are discovered through the same
catalog APIs as core plans.

## If You Are Contributing

Use the [Contributing Guide](CONTRIBUTING_GUIDE.md) for local setup, fix
authoring, plan-file schema details, plugin guidance, and testing conventions.
Use [Docs Development](docs-development.md) when you are editing or regenerating
the documentation site.

Useful local commands:

```bash
make format
make lint
make test
make docs
```

## Reference Pages

- [Generated Fixes Reference](FIXES.md): generated table of registered fixes.
- [Generated Fix Plans Reference](FIX_PLANS.md): generated table of discovered
  plans.
- [Interactive Fix Browser](fixes.html): searchable fix ids with stable anchors.

The xMIP plugin is currently a demo plugin that translates xMIP-style CMIP6
preprocessing into small, inspectable Woodpecker fixes.
