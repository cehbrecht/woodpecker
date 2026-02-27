from __future__ import annotations

import json
import click

# Importing woodpecker.fixes registers built-in fixes.
import woodpecker.fixes  # noqa: F401
from woodpecker.fixes.registry import FixRegistry


@click.group()
def cli():
    """Woodpecker CLI."""
    pass


@cli.command("list-fixes")
@click.option("--dataset", default=None, help="Filter fixes by dataset (e.g., CMIP6-decadal)")
@click.option("--category", "categories", multiple=True, help="Filter by category (repeatable)")
@click.option("--format", "fmt", type=click.Choice(["text", "json", "md"]), default="text")
def list_fixes(dataset: str | None, categories: tuple[str, ...], fmt: str):
    """List registered fixes (discoverable codes)."""
    filters = {}
    if dataset:
        filters["dataset"] = dataset
    if categories:
        filters["categories"] = list(categories) if len(categories) > 1 else categories[0]

    fixes = FixRegistry.discover(filters=filters or None)

    if fmt == "json":
        payload = [
            (f.model_dump() if hasattr(f, "model_dump") else f.__dict__)
            for f in fixes
        ]
        click.echo(json.dumps(payload, indent=2))
        return

    if fmt == "md":
        click.echo("| Code | Name | Description | Categories | Dataset | Priority |")
        click.echo("|------|------|-------------|------------|---------|---------|")
        for f in fixes:
            cats = ", ".join(getattr(f, "categories", []) or [])
            click.echo(f"| {f.code} | {f.name} | {f.description} | {cats} | {f.dataset or ''} | {f.priority} |")
        return

    # text
    for f in fixes:
        cats = ", ".join(getattr(f, "categories", []) or [])
        click.echo(f"{f.code}: {f.description} (cats: {cats}; dataset: {f.dataset or '-'}; priority: {f.priority})")


if __name__ == "__main__":
    cli()
