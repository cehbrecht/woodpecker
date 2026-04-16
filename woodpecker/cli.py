from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Sequence

import click

# Importing woodpecker.fixes registers built-in fixes.
import woodpecker.fixes  # noqa: F401
from woodpecker.fixes.registry import FixRegistry
from woodpecker.inout import DataInput, get_io_availability, normalize_inputs
from woodpecker.plans.io import load_fix_plan_document
from woodpecker.plans.matcher import plan_matches_dataset
from woodpecker.plans.models import FixPlan
from woodpecker.plans.runner import run_check, run_fix, select_fixes
from woodpecker.provenance import build_prov_document, write_prov_document
from woodpecker.stores import DuckDBFixPlanStore, FixPlanStore, JsonFixPlanStore


@dataclass(frozen=True)
class RunContext:
    """Resolved execution context shared by `check` and `fix`.

    Precedence rules:
    - explicit CLI arguments override plan/store-derived values
    - explicit `--plan` overrides store lookup
    - `--plan-store` is an optional fallback source
    - with no plan/store source, direct registry selection is used
    """

    inputs: list[DataInput]
    fixes: list[Any]
    selected_plans: list[FixPlan]
    resolved_dataset: str | None
    resolved_categories: tuple[str, ...]
    resolved_codes: tuple[str, ...]
    resolved_fix_options: dict[str, dict[str, Any]]
    resolved_output_format: str
    source: Literal["direct", "plan", "store"]


def _normalize_ordered_codes(codes: Sequence[str]) -> tuple[str, ...]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in codes:
        code = str(raw).strip().upper()
        if not code or code in seen:
            continue
        out.append(code)
        seen.add(code)
    return tuple(out)


def create_fix_plan_store(store_type: str | None, store_path: Path | None) -> FixPlanStore | None:
    """Create an optional FixPlanStore backend from CLI options."""

    if store_type is None and store_path is None:
        return None
    if store_type is None or store_path is None:
        raise click.ClickException("--plan-store and --plan-store-path must be provided together.")

    try:
        if store_type == "json":
            return JsonFixPlanStore(store_path)
        if store_type == "duckdb":
            return DuckDBFixPlanStore(store_path)
    except (RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    raise click.ClickException(f"Unsupported plan store type: {store_type}")


def _load_store_plans(
    *,
    store: FixPlanStore,
    inputs: Sequence[DataInput],
    plan_id: str | None,
) -> list[FixPlan]:
    plans_by_key: dict[str, FixPlan] = {}
    for data_input in inputs:
        dataset = data_input.load()
        try:
            for plan in store.lookup(dataset, path=data_input.reference):
                key = plan.id or json.dumps(plan.to_dict(), sort_keys=True)
                plans_by_key[key] = plan
        finally:
            close = getattr(dataset, "close", None)
            if callable(close):
                close()

    matches = list(plans_by_key.values())
    if plan_id:
        requested = plan_id.strip()
        matches = [plan for plan in matches if plan.id == requested]
        if not matches:
            raise click.ClickException(f"No matching stored fix plan found for --plan-id '{requested}'.")

    if not matches:
        return []
    if len(matches) > 1:
        plan_ids = [plan.id for plan in matches if plan.id]
        label = ", ".join(plan_ids) if plan_ids else f"{len(matches)} unnamed plans"
        raise click.ClickException(
            "Multiple matching stored fix plans found; specify --plan-id to choose one: " + label
        )
    return matches


def _load_document_plans(
    *,
    plans: Sequence[FixPlan],
    inputs: Sequence[DataInput],
    plan_id: str | None,
) -> list[FixPlan]:
    plans_by_key: dict[str, FixPlan] = {}
    for data_input in inputs:
        dataset = data_input.load()
        try:
            for plan in plans:
                if plan_matches_dataset(plan, dataset, path=data_input.reference):
                    key = plan.id or json.dumps(plan.to_dict(), sort_keys=True)
                    plans_by_key[key] = plan
        finally:
            close = getattr(dataset, "close", None)
            if callable(close):
                close()

    matches = list(plans_by_key.values())
    if plan_id:
        requested = plan_id.strip()
        matches = [plan for plan in matches if plan.id == requested]
        if not matches:
            raise click.ClickException(f"No matching plan found for --plan-id '{requested}'.")

    if not matches:
        return []
    if len(matches) > 1:
        plan_ids = [plan.id for plan in matches if plan.id]
        label = ", ".join(plan_ids) if plan_ids else f"{len(matches)} unnamed plans"
        raise click.ClickException(
            "Multiple matching plans found in plan document; specify --plan-id to choose one: " + label
        )
    return matches


def _plan_codes_and_options(plan: FixPlan) -> tuple[tuple[str, ...], dict[str, dict[str, Any]]]:
    codes = tuple(ref.id for ref in plan.fixes)
    options = {ref.id: dict(ref.options) for ref in plan.fixes}
    return codes, options


def load_plan_from_sources(
    *,
    inputs: Sequence[DataInput],
    plan_path: Path | None,
    store_type: str | None,
    store_path: Path | None,
    plan_id: str | None,
) -> tuple[
    Literal["direct", "plan", "store"],
    list[FixPlan],
    tuple[str, ...],
    dict[str, dict[str, Any]],
]:
    """Load plan selection from explicit file or optional store fallback."""

    if plan_path is None and plan_id and store_type is None and store_path is None:
        raise click.ClickException("--plan-id requires --plan-store and --plan-store-path.")

    if plan_path is not None:
        document = load_fix_plan_document(plan_path)
        plans = _load_document_plans(plans=document.plans, inputs=inputs, plan_id=plan_id)
        if not plans:
            raise click.ClickException("No matching plans found in the plan document for selected inputs.")
        selected = plans[0]
        codes, fix_options = _plan_codes_and_options(selected)
        return "plan", [selected], codes, fix_options

    store = create_fix_plan_store(store_type, store_path)
    if store is None:
        return "direct", [], (), {}

    plans = _load_store_plans(store=store, inputs=inputs, plan_id=plan_id)
    if not plans:
        return "store", [], (), {}

    selected = plans[0]
    codes, fix_options = _plan_codes_and_options(selected)
    return "store", [selected], codes, fix_options


def _resolve_target_paths(paths: tuple[Path, ...]) -> list[Path]:
    if paths:
        return list(paths)
    return [Path.cwd()]


def resolve_run_context(
    *,
    paths: tuple[Path, ...],
    plan_path: Path | None,
    store_type: str | None,
    store_path: Path | None,
    plan_id: str | None,
    dataset: str | None,
    categories: tuple[str, ...],
    codes: tuple[str, ...],
    output_format: str,
) -> RunContext:
    """Resolve inputs + fix selection from direct, plan, or store sources."""

    target_paths = _resolve_target_paths(paths)
    inputs = normalize_inputs(target_paths)

    (
        source,
        selected_plans,
        source_codes,
        source_fix_options,
    ) = load_plan_from_sources(
        inputs=inputs,
        plan_path=plan_path,
        store_type=store_type,
        store_path=store_path,
        plan_id=plan_id,
    )

    cli_codes = _normalize_ordered_codes(codes)
    resolved_codes = cli_codes or source_codes
    resolved_ordered_codes = resolved_codes
    resolved_dataset = dataset
    resolved_categories = categories

    resolved_output_format = output_format

    resolved_fix_options = dict(source_fix_options)

    if source == "store" and not selected_plans and not resolved_codes:
        raise click.ClickException("No matching fix plans found in the plan store for selected inputs.")

    fixes = select_fixes(
        dataset=resolved_dataset,
        categories=resolved_categories,
        codes=resolved_codes,
        strict_codes=True,
        fix_options=resolved_fix_options,
        ordered_codes=resolved_ordered_codes,
    )

    return RunContext(
        inputs=inputs,
        fixes=fixes,
        selected_plans=selected_plans,
        resolved_dataset=resolved_dataset,
        resolved_categories=tuple(resolved_categories),
        resolved_codes=tuple(resolved_codes),
        resolved_fix_options=resolved_fix_options,
        resolved_output_format=resolved_output_format,
        source=source,
    )


def format_findings(findings: list[dict[str, str]], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(findings, indent=2)
    return "\n".join(f"{item['path']}: {item['code']} {item['message']}" for item in findings)


def format_fix_stats(
    stats: dict[str, int],
    *,
    fmt: str,
    dry_run: bool,
    force_apply: bool,
    resolved_output_format: str,
    provenance: bool,
    provenance_path: Path,
) -> str:
    if fmt == "json":
        payload = {
            "mode": "dry-run" if dry_run else "write",
            "force_apply": force_apply,
            "output_format": resolved_output_format,
            "provenance": str(provenance_path) if provenance else None,
            **stats,
        }
        return json.dumps(payload, indent=2)

    mode = "dry-run" if dry_run else "write"
    if not dry_run:
        return (
            f"Fix run complete ({mode}): {stats['attempted']} fix applications attempted, "
            f"{stats['changed']} files changed, {stats['persisted']} persisted, "
            f"{stats['persist_failed']} failed to persist."
        )
    return (
        f"Fix run complete ({mode}): {stats['attempted']} fix applications attempted, "
        f"{stats['changed']} files changed."
    )


def format_plans(plans: Sequence[FixPlan], fmt: str) -> str:
    if fmt == "json":
        return json.dumps([plan.to_dict() for plan in plans], indent=2)

    if not plans:
        return "No plans found."

    lines: list[str] = []
    for plan in plans:
        plan_id = plan.id or "<unnamed>"
        lines.append(f"{plan_id}: {len(plan.fixes)} fixes")
    return "\n".join(lines)


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

    store = create_fix_plan_store(plan_store, plan_store_path)
    if store is None:  # pragma: no cover - guarded by required=True on options
        raise click.ClickException("--plan-store and --plan-store-path are required.")

    try:
        plans = store.list_plans()
    except (RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(format_plans(plans, fmt))


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
        run_id = f"woodpecker-{Path.cwd().name}"
        run_fix_kwargs = {
            "dry_run": dry_run,
            "output_format": context.resolved_output_format,
        }
        if force_apply:
            run_fix_kwargs["force_apply"] = True
        if embed_provenance_metadata and not dry_run:
            run_fix_kwargs["embed_provenance_metadata"] = True
            run_fix_kwargs["provenance_run_id"] = run_id
        stats = run_fix(context.inputs, context.fixes, **run_fix_kwargs)
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    if provenance:
        prov = build_prov_document(
            inputs=context.inputs,
            selected_codes=[getattr(fix, "code", "") for fix in context.fixes],
            stats=stats,
            mode="dry-run" if dry_run else "write",
            output_format=context.resolved_output_format,
            plan=str(plan) if plan else None,
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
