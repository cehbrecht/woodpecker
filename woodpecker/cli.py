from __future__ import annotations

import json
from pathlib import Path

import click

# Importing woodpecker.fixes registers built-in fixes.
import woodpecker.fixes  # noqa: F401
from woodpecker.fixes.registry import FixRegistry
from woodpecker.inout import get_io_availability, normalize_inputs
from woodpecker.runner import run_check, run_fix, select_fixes
from woodpecker.workflow import load_workflow


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
        payload = [(f.model_dump() if hasattr(f, "model_dump") else f.__dict__) for f in fixes]
        click.echo(json.dumps(payload, indent=2))
        return

    if fmt == "md":
        click.echo("| Code | Name | Description | Categories | Dataset | Priority |")
        click.echo("|------|------|-------------|------------|---------|---------|")
        for f in fixes:
            cats = ", ".join(getattr(f, "categories", []) or [])
            click.echo(
                f"| {f.code} | {f.name} | {f.description} | {cats} | {f.dataset or ''} | {f.priority} |"
            )
        return

    # text
    for f in fixes:
        cats = ", ".join(getattr(f, "categories", []) or [])
        click.echo(
            f"{f.code}: {f.description} (cats: {cats}; dataset: {f.dataset or '-'}; priority: {f.priority})"
        )


@cli.command("check")
@click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("--workflow", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--dataset", default=None, help="Filter fixes by dataset.")
@click.option(
    "--category", "categories", multiple=True, help="Filter fixes by category (repeatable)"
)
@click.option("--select", "codes", multiple=True, help="Run only selected fix codes (repeatable)")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def check(
    paths: tuple[Path, ...],
    workflow: Path | None,
    dataset: str | None,
    categories: tuple[str, ...],
    codes: tuple[str, ...],
    fmt: str,
):
    """Check NetCDF files and report findings grouped by fix code."""
    try:
        workflow_spec = load_workflow(workflow) if workflow else None

        resolved_paths = list(paths)
        if not resolved_paths and workflow_spec and workflow_spec.inputs:
            resolved_paths = [Path(item) for item in workflow_spec.inputs]
        target_paths = resolved_paths or [Path.cwd()]

        resolved_dataset = dataset or (workflow_spec.dataset if workflow_spec else None)
        resolved_categories = categories or tuple(workflow_spec.categories if workflow_spec else [])
        resolved_codes = codes or tuple(workflow_spec.codes if workflow_spec else [])
        resolved_fix_options = workflow_spec.fixes if workflow_spec else {}

        inputs = normalize_inputs(target_paths)
        fixes = select_fixes(
            dataset=resolved_dataset,
            categories=resolved_categories,
            codes=resolved_codes,
            strict_codes=True,
            fix_options=resolved_fix_options,
        )
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    findings = run_check(inputs, fixes)

    if fmt == "json":
        click.echo(json.dumps(findings, indent=2))
    else:
        for item in findings:
            click.echo(f"{item['path']}: {item['code']} {item['message']}")

    if not findings and fmt == "text":
        click.echo(
            f"No issues found ({len(inputs)} NetCDF files scanned, {len(fixes)} fixes selected)."
        )

    raise SystemExit(1 if findings else 0)


@cli.command("io-status")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def io_status(fmt: str):
    """Report runtime availability of optional I/O backends."""
    report = get_io_availability()
    if fmt == "json":
        click.echo(json.dumps(report, indent=2))
        return

    for key, value in report.items():
        click.echo(f"{key}: {'available' if value else 'unavailable'}")


@cli.command("fix")
@click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("--workflow", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--dataset", default=None, help="Filter fixes by dataset.")
@click.option(
    "--category", "categories", multiple=True, help="Filter fixes by category (repeatable)"
)
@click.option("--select", "codes", multiple=True, help="Run only selected fix codes (repeatable)")
@click.option(
    "--write",
    is_flag=True,
    default=False,
    help="Apply changes. Without this flag, run in dry-run mode.",
)
@click.option(
    "--output-format",
    type=click.Choice(["auto", "netcdf", "zarr"]),
    default="auto",
    show_default=True,
    help="Output format for writes.",
)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def fix(
    paths: tuple[Path, ...],
    workflow: Path | None,
    dataset: str | None,
    categories: tuple[str, ...],
    codes: tuple[str, ...],
    write: bool,
    output_format: str,
    fmt: str,
):
    """Apply selected fixes to NetCDF files."""
    try:
        workflow_spec = load_workflow(workflow) if workflow else None

        resolved_paths = list(paths)
        if not resolved_paths and workflow_spec and workflow_spec.inputs:
            resolved_paths = [Path(item) for item in workflow_spec.inputs]
        target_paths = resolved_paths or [Path.cwd()]

        resolved_dataset = dataset or (workflow_spec.dataset if workflow_spec else None)
        resolved_categories = categories or tuple(workflow_spec.categories if workflow_spec else [])
        resolved_codes = codes or tuple(workflow_spec.codes if workflow_spec else [])
        resolved_fix_options = workflow_spec.fixes if workflow_spec else {}
        resolved_output_format = output_format
        if (
            workflow_spec
            and workflow_spec.output_format
            and output_format == "auto"
        ):
            resolved_output_format = workflow_spec.output_format

        inputs = normalize_inputs(target_paths)
        fixes = select_fixes(
            dataset=resolved_dataset,
            categories=resolved_categories,
            codes=resolved_codes,
            strict_codes=True,
            fix_options=resolved_fix_options,
        )
        stats = run_fix(inputs, fixes, dry_run=not write, output_format=resolved_output_format)
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    if fmt == "json":
        payload = {
            "mode": "write" if write else "dry-run",
            "output_format": resolved_output_format,
            **stats,
        }
        click.echo(json.dumps(payload, indent=2))
        if write and stats.get("persist_failed", 0) > 0:
            raise SystemExit(1)
        return

    mode = "write" if write else "dry-run"
    if write:
        click.echo(
            f"Fix run complete ({mode}): {stats['attempted']} fix applications attempted, {stats['changed']} files changed, {stats['persisted']} persisted, {stats['persist_failed']} failed to persist."
        )
        return
    click.echo(
        f"Fix run complete ({mode}): {stats['attempted']} fix applications attempted, {stats['changed']} files changed."
    )


if __name__ == "__main__":
    cli()
