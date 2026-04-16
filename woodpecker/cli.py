from __future__ import annotations

import json
from pathlib import Path

import click

# Importing woodpecker.fixes registers built-in fixes.
import woodpecker.fixes  # noqa: F401
from woodpecker.fix_plan import load_fix_plan_spec
from woodpecker.fixes.registry import FixRegistry
from woodpecker.inout import get_io_availability, normalize_inputs
from woodpecker.provenance import build_prov_document, write_prov_document
from woodpecker.runner import run_check, run_fix, select_fixes


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
@click.option(
    "--plan",
    "plan",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Load fix selection/options from a fix plan file.",
)
@click.option("--dataset", default=None, help="Filter fixes by dataset.")
@click.option(
    "--category", "categories", multiple=True, help="Filter fixes by category (repeatable)"
)
@click.option("--select", "codes", multiple=True, help="Run only selected fix codes (repeatable)")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def check(
    paths: tuple[Path, ...],
    plan: Path | None,
    dataset: str | None,
    categories: tuple[str, ...],
    codes: tuple[str, ...],
    fmt: str,
):
    """Check NetCDF files and report findings grouped by fix code."""
    try:
        plan_spec = load_fix_plan_spec(plan) if plan else None

        resolved_paths = list(paths)
        if not resolved_paths and plan_spec and plan_spec.inputs:
            resolved_paths = [Path(item) for item in plan_spec.inputs]
        target_paths = resolved_paths or [Path.cwd()]

        inputs = normalize_inputs(target_paths)
        resolution = plan_spec.resolve([item.reference for item in inputs]) if plan_spec else None

        resolved_dataset = dataset or (resolution.dataset if resolution else None)
        resolved_categories = categories or tuple(resolution.categories if resolution else [])
        resolved_codes = codes or tuple(resolution.codes if resolution else [])
        resolved_fix_options = resolution.fixes if resolution else {}
        resolved_ordered_codes = (
            tuple(code.strip().upper() for code in codes if code.strip())
            if codes
            else tuple(resolution.ordered_ids if resolution else [])
        )

        fixes = select_fixes(
            dataset=resolved_dataset,
            categories=resolved_categories,
            codes=resolved_codes,
            strict_codes=True,
            fix_options=resolved_fix_options,
            ordered_codes=resolved_ordered_codes,
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
@click.option(
    "--plan",
    "plan",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Load fix selection/options from a fix plan file.",
)
@click.option("--dataset", default=None, help="Filter fixes by dataset.")
@click.option(
    "--category", "categories", multiple=True, help="Filter fixes by category (repeatable)"
)
@click.option("--select", "codes", multiple=True, help="Run only selected fix codes (repeatable)")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview changes without writing outputs.",
)
@click.option(
    "--force-apply",
    is_flag=True,
    default=False,
    help="Apply selected fixes without evaluating matches().",
)
@click.option(
    "--output-format",
    type=click.Choice(["auto", "netcdf", "zarr"]),
    default="auto",
    show_default=True,
    help="Output format for writes.",
)
@click.option(
    "--provenance/--no-provenance",
    default=True,
    show_default=True,
    help="Write W3C PROV-JSON provenance output file.",
)
@click.option(
    "--provenance-path",
    type=click.Path(path_type=Path),
    default=Path("woodpecker.prov.json"),
    show_default=True,
    help="Output path for provenance JSON.",
)
@click.option(
    "--embed-provenance-metadata",
    is_flag=True,
    default=False,
    help="Embed per-dataset provenance metadata into output dataset attrs on write.",
)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def fix(
    paths: tuple[Path, ...],
    plan: Path | None,
    dataset: str | None,
    categories: tuple[str, ...],
    codes: tuple[str, ...],
    dry_run: bool,
    force_apply: bool,
    output_format: str,
    provenance: bool,
    provenance_path: Path,
    embed_provenance_metadata: bool,
    fmt: str,
):
    """Apply selected fixes to NetCDF files."""
    try:
        plan_path = plan
        plan_spec = load_fix_plan_spec(plan_path) if plan_path else None

        resolved_paths = list(paths)
        if not resolved_paths and plan_spec and plan_spec.inputs:
            resolved_paths = [Path(item) for item in plan_spec.inputs]
        target_paths = resolved_paths or [Path.cwd()]

        inputs = normalize_inputs(target_paths)
        resolution = plan_spec.resolve([item.reference for item in inputs]) if plan_spec else None

        resolved_dataset = dataset or (resolution.dataset if resolution else None)
        resolved_categories = categories or tuple(resolution.categories if resolution else [])
        resolved_codes = codes or tuple(resolution.codes if resolution else [])
        resolved_fix_options = resolution.fixes if resolution else {}
        resolved_ordered_codes = (
            tuple(code.strip().upper() for code in codes if code.strip())
            if codes
            else tuple(resolution.ordered_ids if resolution else [])
        )
        if force_apply and not resolved_codes:
            raise click.ClickException(
                "--force-apply requires explicit fix selection via --select or plan codes."
            )
        resolved_output_format = output_format
        if resolution and resolution.output_format and output_format == "auto":
            resolved_output_format = resolution.output_format

        fixes = select_fixes(
            dataset=resolved_dataset,
            categories=resolved_categories,
            codes=resolved_codes,
            strict_codes=True,
            fix_options=resolved_fix_options,
            ordered_codes=resolved_ordered_codes,
        )
        run_id = f"woodpecker-{Path.cwd().name}"
        run_fix_kwargs = {
            "dry_run": dry_run,
            "output_format": resolved_output_format,
        }
        if force_apply:
            run_fix_kwargs["force_apply"] = True
        if embed_provenance_metadata and not dry_run:
            run_fix_kwargs["embed_provenance_metadata"] = True
            run_fix_kwargs["provenance_run_id"] = run_id
        stats = run_fix(inputs, fixes, **run_fix_kwargs)
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    if provenance:
        prov = build_prov_document(
            inputs=inputs,
            selected_codes=[getattr(fix, "code", "") for fix in fixes],
            stats=stats,
            mode="dry-run" if dry_run else "write",
            output_format=resolved_output_format,
            plan=str(plan_path) if plan_path else None,
        )
        write_prov_document(prov, provenance_path)

    if fmt == "json":
        payload = {
            "mode": "dry-run" if dry_run else "write",
            "force_apply": force_apply,
            "output_format": resolved_output_format,
            "provenance": str(provenance_path) if provenance else None,
            **stats,
        }
        click.echo(json.dumps(payload, indent=2))
        if not dry_run and stats.get("persist_failed", 0) > 0:
            raise SystemExit(1)
        return

    mode = "dry-run" if dry_run else "write"
    if not dry_run:
        click.echo(
            f"Fix run complete ({mode}): {stats['attempted']} fix applications attempted, {stats['changed']} files changed, {stats['persisted']} persisted, {stats['persist_failed']} failed to persist."
        )
        return
    click.echo(
        f"Fix run complete ({mode}): {stats['attempted']} fix applications attempted, {stats['changed']} files changed."
    )


if __name__ == "__main__":
    cli()
