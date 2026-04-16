from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

import click

# Importing woodpecker.fixes registers built-in fixes.
import woodpecker.fixes  # noqa: F401
from woodpecker.fixes.registry import FixRegistry
from woodpecker.formatting import format_findings, format_fix_stats, format_plans
from woodpecker.inout import get_io_availability
from woodpecker.plans.resolver import RunContext, resolve_load_source_plans, resolve_run_context
from woodpecker.plans.runner import run_check, run_fix
from woodpecker.provenance import build_prov_document, write_prov_document
from woodpecker.stores.helpers import create_fix_plan_store


class RunFixKwargs(TypedDict, total=False):
    """Keyword arguments accepted by run_fix in this CLI context."""

    dry_run: bool
    output_format: str
    force_apply: bool
    embed_provenance_metadata: bool
    provenance_run_id: str


def build_run_fix_kwargs(
    context: RunContext,
    dry_run: bool,
    force_apply: bool,
    embed_provenance_metadata: bool,
) -> RunFixKwargs:
    """Build run_fix kwargs from command flags and resolved run context."""

    run_fix_kwargs: RunFixKwargs = {
        "dry_run": dry_run,
        "output_format": context.resolved_output_format,
    }
    if force_apply:
        run_fix_kwargs["force_apply"] = True
    if embed_provenance_metadata and not dry_run:
        run_id = f"woodpecker-{Path.cwd().name}"
        run_fix_kwargs["embed_provenance_metadata"] = True
        run_fix_kwargs["provenance_run_id"] = run_id
    return run_fix_kwargs


def format_provenance_source(
    context: RunContext,
    plan: Path | None,
    plan_store: str | None,
    plan_store_path: Path | None,
) -> str | None:
    """Return a concise provenance source description for selected plan input."""

    if context.source == "plan":
        return str(plan) if plan else None

    if context.source == "store":
        plan_ids = [selected.id for selected in context.selected_plans if selected.id]
        selected_text = ", ".join(plan_ids) if plan_ids else "<unnamed>"
        return f"store type={plan_store} path={plan_store_path} plans={selected_text}"

    return None


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


@cli.command("list-plans")
@click.option(
    "--plan-store",
    "plan_store",
    type=click.Choice(["json", "duckdb"]),
    required=True,
    help="Fix plan store backend.",
)
@click.option(
    "--plan-store-path",
    "plan_store_path",
    type=click.Path(path_type=Path),
    required=True,
    help="Path to fix plan store file/database.",
)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def list_plans(plan_store: str, plan_store_path: Path, fmt: str):
    """List fix plans available in a configured store backend."""

    try:
        store = create_fix_plan_store(plan_store, plan_store_path)
    except click.ClickException:
        raise
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    if store is None:  # pragma: no cover - guarded by required=True on options
        raise click.ClickException("--plan-store and --plan-store-path are required.")

    try:
        plans = store.list_plans()
    except click.ClickException:
        raise
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(format_plans(plans, fmt))


@cli.command("load-plans")
@click.option(
    "--plan-store",
    "plan_store",
    type=click.Choice(["json", "duckdb"]),
    required=True,
    help="Target fix plan store backend.",
)
@click.option(
    "--plan-store-path",
    "plan_store_path",
    type=click.Path(path_type=Path),
    required=True,
    help="Path to target fix plan store file/database.",
)
@click.option(
    "--from-plan",
    "from_plan",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Load plans from a FixPlanDocument file.",
)
@click.option(
    "--from-store",
    "from_store",
    type=click.Choice(["json", "duckdb"]),
    default=None,
    help="Load plans from a source fix plan store backend.",
)
@click.option(
    "--from-store-path",
    "from_store_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to source fix plan store file/database.",
)
@click.option("--plan-id", "plan_id", default=None, help="Load only this plan id from source.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def load_plans(
    plan_store: str,
    plan_store_path: Path,
    from_plan: Path | None,
    from_store: str | None,
    from_store_path: Path | None,
    plan_id: str | None,
    fmt: str,
):
    """Load plans into a target store from a plan document or another store."""

    try:
        target_store = create_fix_plan_store(plan_store, plan_store_path)
    except click.ClickException:
        raise
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    if target_store is None:  # pragma: no cover - guarded by required=True
        raise click.ClickException("--plan-store and --plan-store-path are required.")

    try:
        plans = resolve_load_source_plans(
            from_plan=from_plan,
            from_store_type=from_store,
            from_store_path=from_store_path,
            plan_id=plan_id,
        )
    except click.ClickException:
        raise
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        for plan in plans:
            target_store.save_plan(plan)
    except click.ClickException:
        raise
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    plan_ids = [plan.id or "<unnamed>" for plan in plans]
    if fmt == "json":
        click.echo(
            json.dumps(
                {
                    "loaded": len(plans),
                    "target_store": plan_store,
                    "target_path": str(plan_store_path),
                    "plan_ids": plan_ids,
                },
                indent=2,
            )
        )
        return

    click.echo(
        f"Loaded {len(plans)} plan(s) into {plan_store} store at {plan_store_path}: "
        + ", ".join(plan_ids)
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
@click.option(
    "--plan-store",
    "plan_store",
    type=click.Choice(["json", "duckdb"]),
    default=None,
    help="Optional fix plan store backend when --plan is not provided.",
)
@click.option(
    "--plan-store-path",
    "plan_store_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to fix plan store file/database.",
)
@click.option("--plan-id", "plan_id", default=None, help="Select a specific stored plan id.")
@click.option("--dataset", default=None, help="Filter fixes by dataset.")
@click.option(
    "--category", "categories", multiple=True, help="Filter fixes by category (repeatable)"
)
@click.option("--select", "codes", multiple=True, help="Run only selected fix codes (repeatable)")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def check(
    paths: tuple[Path, ...],
    plan: Path | None,
    plan_store: str | None,
    plan_store_path: Path | None,
    plan_id: str | None,
    dataset: str | None,
    categories: tuple[str, ...],
    codes: tuple[str, ...],
    fmt: str,
):
    """Check NetCDF files and report findings grouped by fix code."""
    try:
        context = resolve_run_context(
            paths=paths,
            plan_path=plan,
            store_type=plan_store,
            store_path=plan_store_path,
            plan_id=plan_id,
            dataset=dataset,
            categories=categories,
            codes=codes,
            output_format="auto",
        )
    except click.ClickException:
        raise
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    findings = run_check(context.inputs, context.fixes)
    output = format_findings(findings, fmt)
    if output:
        click.echo(output)

    if not findings and fmt == "text":
        click.echo(
            f"No issues found ({len(context.inputs)} NetCDF files scanned, {len(context.fixes)} fixes selected)."
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
@click.option(
    "--plan-store",
    "plan_store",
    type=click.Choice(["json", "duckdb"]),
    default=None,
    help="Optional fix plan store backend when --plan is not provided.",
)
@click.option(
    "--plan-store-path",
    "plan_store_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to fix plan store file/database.",
)
@click.option("--plan-id", "plan_id", default=None, help="Select a specific stored plan id.")
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
    plan_store: str | None,
    plan_store_path: Path | None,
    plan_id: str | None,
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
        context = resolve_run_context(
            paths=paths,
            plan_path=plan,
            store_type=plan_store,
            store_path=plan_store_path,
            plan_id=plan_id,
            dataset=dataset,
            categories=categories,
            codes=codes,
            output_format=output_format,
        )
        if force_apply and not context.resolved_codes:
            raise click.ClickException(
                "--force-apply requires explicit fix selection via --select or plan codes."
            )
        run_fix_kwargs = build_run_fix_kwargs(
            context,
            dry_run,
            force_apply,
            embed_provenance_metadata,
        )
        stats = run_fix(context.inputs, context.fixes, **run_fix_kwargs)
    except click.ClickException:
        raise
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    if provenance:
        provenance_source = format_provenance_source(context, plan, plan_store, plan_store_path)
        prov = build_prov_document(
            inputs=context.inputs,
            selected_codes=[getattr(fix, "code", "") for fix in context.fixes],
            stats=stats,
            mode="dry-run" if dry_run else "write",
            output_format=context.resolved_output_format,
            plan=provenance_source,
        )
        write_prov_document(prov, provenance_path)

    click.echo(
        format_fix_stats(
            stats,
            fmt=fmt,
            dry_run=dry_run,
            force_apply=force_apply,
            resolved_output_format=context.resolved_output_format,
            provenance=provenance,
            provenance_path=provenance_path,
        )
    )
    if fmt == "json" and not dry_run and stats.get("persist_failed", 0) > 0:
        raise SystemExit(1)
    if not dry_run:
        return


if __name__ == "__main__":
    cli()
