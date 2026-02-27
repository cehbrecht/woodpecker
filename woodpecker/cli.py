from __future__ import annotations

import json
from pathlib import Path
import click

# Importing woodpecker.fixes registers built-in fixes.
import woodpecker.fixes  # noqa: F401
from woodpecker.fixes.registry import FixRegistry
from woodpecker.runner import collect_netcdf_files, run_check, run_fix, select_fixes


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


@cli.command("check")
@click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("--dataset", default=None, help="Filter fixes by dataset.")
@click.option("--category", "categories", multiple=True, help="Filter fixes by category (repeatable)")
@click.option("--select", "codes", multiple=True, help="Run only selected fix codes (repeatable)")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def check(paths: tuple[Path, ...], dataset: str | None, categories: tuple[str, ...], codes: tuple[str, ...], fmt: str):
    """Check NetCDF files and report findings grouped by fix code."""
    target_paths = list(paths) or [Path.cwd()]
    files = collect_netcdf_files(target_paths)
    fixes = select_fixes(dataset=dataset, categories=categories, codes=codes)
    findings = run_check(files, fixes)

    if fmt == "json":
        click.echo(json.dumps(findings, indent=2))
    else:
        for item in findings:
            click.echo(f"{item['path']}: {item['code']} {item['message']}")

    if not findings and fmt == "text":
        click.echo(f"No issues found ({len(files)} NetCDF files scanned, {len(fixes)} fixes selected).")

    raise SystemExit(1 if findings else 0)


@cli.command("fix")
@click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("--dataset", default=None, help="Filter fixes by dataset.")
@click.option("--category", "categories", multiple=True, help="Filter fixes by category (repeatable)")
@click.option("--select", "codes", multiple=True, help="Run only selected fix codes (repeatable)")
@click.option("--write", is_flag=True, default=False, help="Apply changes. Without this flag, run in dry-run mode.")
def fix(paths: tuple[Path, ...], dataset: str | None, categories: tuple[str, ...], codes: tuple[str, ...], write: bool):
    """Apply selected fixes to NetCDF files."""
    target_paths = list(paths) or [Path.cwd()]
    files = collect_netcdf_files(target_paths)
    fixes = select_fixes(dataset=dataset, categories=categories, codes=codes)
    stats = run_fix(files, fixes, dry_run=not write)
    mode = "write" if write else "dry-run"
    click.echo(
        f"Fix run complete ({mode}): {stats['attempted']} fix applications attempted, {stats['changed']} files changed."
    )


if __name__ == "__main__":
    cli()
