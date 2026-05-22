from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, TypeVar

import click

# Importing woodpecker.fixes registers built-in fixes.
import woodpecker.fixes  # noqa: F401
from woodpecker.commands import (
    execute_check_context,
    execute_fix_context,
    execute_load_plans,
)
from woodpecker.fix_plans.resolver import RunContext, resolve_run_context
from woodpecker.fixes.registry import FixRegistry
from woodpecker.io import get_io_availability
from woodpecker.provenance import write_fix_provenance
from woodpecker.stores.helpers import create_fix_plan_store
from woodpecker.ui.formatting import format_findings, format_fix_stats, format_fixes, format_plans

T = TypeVar("T")
STORE_CHOICES = ["catalog", "json", "duckdb", "auto"]
WRITABLE_STORE_CHOICES = ["json", "duckdb"]


def _with_click_errors(func: Callable[[], T]) -> T:
    """Run a callable and normalize common argument/config errors for CLI output."""

    try:
        return func()
    except click.ClickException:
        raise
    except (TypeError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc


@click.group()
def cli():
    """Woodpecker CLI."""
    pass


@cli.command("list-fixes")
@click.option("--dataset", default=None, help="Filter fixes by dataset (e.g., CMIP6-decadal)")
@click.option("--category", "categories", multiple=True, help="Filter by category (repeatable)")
@click.option("--format", "fmt", type=click.Choice(["text", "json", "md"]), default="text")
def list_fixes(dataset: str | None, categories: tuple[str, ...], fmt: str):
    """List registered fixes (discoverable identifiers)."""
    filters = {}
    if dataset:
        filters["dataset"] = dataset
    if categories:
        filters["categories"] = list(categories) if len(categories) > 1 else categories[0]

    fixes = FixRegistry.discover(filters=filters or None)
    click.echo(format_fixes(fixes, fmt))


@cli.command("list-plans")
@click.option(
    "--store",
    "store_type",
    type=click.Choice(STORE_CHOICES),
    default="catalog",
    show_default=True,
    help="FixPlanStore backend.",
)
@click.option(
    "--plan",
    "plan_location",
    type=click.Path(path_type=Path),
    required=False,
    help=(
        "Path or location used by selected store backend "
        "(catalog: extra file/directory, JSON: local file, DuckDB: database file; not needed for auto)."
    ),
)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def list_plans(store_type: str, plan_location: Path | None, fmt: str):
    """List FixPlan entries from a configured store backend.

    Catalog mode discovers plans from package resources, user config, system
    locations, and optional `--plan` paths.
    """

    store = _with_click_errors(lambda: create_fix_plan_store(store_type, plan_location))
    plans = _with_click_errors(store.list_plans)

    click.echo(format_plans(plans, fmt))


@cli.command("load-plans")
@click.option(
    "--store",
    "store_type",
    type=click.Choice(WRITABLE_STORE_CHOICES),
    default="json",
    show_default=True,
    help="Target FixPlanStore backend.",
)
@click.option(
    "--plan",
    "plan_location",
    type=click.Path(path_type=Path),
    required=True,
    help=(
        "Path or location used by selected target store backend "
        "(JSON: local file, DuckDB: database file)."
    ),
)
@click.option(
    "--from-plan",
    "from_plan",
    type=click.Path(path_type=Path),
    required=False,
    help=(
        "Source plan location interpreted by --from-store "
        "(catalog: extra file/directory, JSON: local file, DuckDB: database file; not needed for auto)."
    ),
)
@click.option(
    "--from-store",
    "from_store",
    type=click.Choice(STORE_CHOICES),
    default="json",
    show_default=True,
    help="Source FixPlanStore backend for --from-plan location.",
)
@click.option("--plan-id", "plan_id", default=None, help="Load only this plan id from source.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def load_plans(
    store_type: str,
    plan_location: Path,
    from_plan: Path | None,
    from_store: str,
    plan_id: str | None,
    fmt: str,
):
    """Load plans into a target store from a source store location."""
    result = _with_click_errors(
        lambda: execute_load_plans(
            store_type=store_type,
            plan_location=plan_location,
            from_plan=from_plan,
            from_store=from_store,
            plan_id=plan_id,
        )
    )
    if fmt == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(
            f"Loaded {result['loaded']} plan(s) into {result['target_store']} store at {result['target_path']}: "
            + ", ".join(result["plan_ids"])
        )


@cli.command("check")
@click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option(
    "--store",
    "store_type",
    type=click.Choice(STORE_CHOICES),
    default="json",
    show_default=True,
    help="FixPlanStore backend (default: json).",
)
@click.option(
    "--plan",
    "plan",
    type=click.Path(path_type=Path),
    default=None,
    help=(
        "Path or location used by selected store backend "
        "(catalog: extra file/directory, JSON: local file, DuckDB: database file; not needed for auto)."
    ),
)
@click.option("--plan-id", "plan_id", default=None, help="Select a specific stored plan id.")
@click.option("--dataset", default=None, help="Filter fixes by dataset.")
@click.option(
    "--category", "categories", multiple=True, help="Filter fixes by category (repeatable)"
)
@click.option(
    "--select",
    "identifiers",
    multiple=True,
    help="Run only selected fix identifiers (repeatable)",
)
@click.option(
    "--strict-io/--no-strict-io",
    default=False,
    show_default=True,
    help="Fail if dataset loading falls back due to unavailable/failed I/O backend.",
)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def check_cmd(
    paths: tuple[Path, ...],
    store_type: str,
    plan: Path | None,
    plan_id: str | None,
    dataset: str | None,
    categories: tuple[str, ...],
    identifiers: tuple[str, ...],
    strict_io: bool,
    fmt: str,
):
    """Check NetCDF files and report findings grouped by fix identifier."""
    context = _with_click_errors(
        lambda: resolve_run_context(
            paths=paths,
            store_type=store_type,
            plan_location=plan,
            plan_id=plan_id,
            dataset=dataset,
            categories=categories,
            identifiers=identifiers,
            output_format="auto",
        )
    )

    findings = _with_click_errors(lambda: execute_check_context(context, strict_io=strict_io))
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
    "--store",
    "store_type",
    type=click.Choice(STORE_CHOICES),
    default="json",
    show_default=True,
    help="FixPlanStore backend (default: json).",
)
@click.option(
    "--plan",
    "plan",
    type=click.Path(path_type=Path),
    default=None,
    help=(
        "Path or location used by selected store backend "
        "(catalog: extra file/directory, JSON: local file, DuckDB: database file; not needed for auto)."
    ),
)
@click.option("--plan-id", "plan_id", default=None, help="Select a specific stored plan id.")
@click.option("--dataset", default=None, help="Filter fixes by dataset.")
@click.option(
    "--category", "categories", multiple=True, help="Filter fixes by category (repeatable)"
)
@click.option(
    "--select",
    "identifiers",
    multiple=True,
    help="Run only selected fix identifiers (repeatable)",
)
@click.option(
    "--strict-io/--no-strict-io",
    default=False,
    show_default=True,
    help="Fail if dataset loading falls back due to unavailable/failed I/O backend.",
)
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
def fix_cmd(
    paths: tuple[Path, ...],
    store_type: str,
    plan: Path | None,
    plan_id: str | None,
    dataset: str | None,
    categories: tuple[str, ...],
    identifiers: tuple[str, ...],
    strict_io: bool,
    dry_run: bool,
    force_apply: bool,
    output_format: str,
    provenance: bool,
    provenance_path: Path,
    embed_provenance_metadata: bool,
    fmt: str,
):
    """Apply selected fixes to NetCDF files."""

    def run_fix_command() -> tuple[RunContext, dict[str, int]]:
        context = resolve_run_context(
            paths=paths,
            store_type=store_type,
            plan_location=plan,
            plan_id=plan_id,
            dataset=dataset,
            categories=categories,
            identifiers=identifiers,
            output_format=output_format,
        )
        run_id = None
        if embed_provenance_metadata and not dry_run:
            run_id = f"woodpecker-{Path.cwd().name}"
        stats = execute_fix_context(
            context,
            dry_run=dry_run,
            force_apply=force_apply,
            embed_provenance_metadata=embed_provenance_metadata,
            provenance_run_id=run_id,
            strict_io=strict_io,
        )
        return context, stats

    context, stats = _with_click_errors(run_fix_command)

    if provenance:
        _with_click_errors(
            lambda: write_fix_provenance(
                context,
                stats,
                dry_run=dry_run,
                store_type=store_type,
                plan_location=plan,
                provenance_path=provenance_path,
            )
        )

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


if __name__ == "__main__":
    cli()
