from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Sequence, TypedDict

from woodpecker.fixes.registry import FixRegistry
from woodpecker.identity import dataset_type_matches_declared, resolve_dataset_identity
from woodpecker.io import DataInput, get_output_adapter, normalize_inputs


if TYPE_CHECKING:
    from woodpecker.plans.models import FixPlan
    from woodpecker.plans.resolver import RunContext


class RunFixKwargs(TypedDict, total=False):
    """Keyword arguments accepted by run_fix for command-level orchestration."""

    dry_run: bool
    output_format: str
    force_apply: bool
    embed_provenance_metadata: bool
    provenance_run_id: str


def _resolve_plan_api_selection(
    *,
    plan_path: str | Path,
    inputs: Any | None,
    identifiers: Sequence[str],
    plan_id: str | None,
) -> tuple[list[DataInput], tuple[str, ...], tuple[str, ...], dict[str, dict[str, Any]]]:
    # Local import avoids an import cycle with plans.resolver -> commands.select_fixes.
    from woodpecker.plans.resolver import resolve_plan_source, resolve_selection_inputs

    resolved_inputs = inputs if inputs is not None else [Path.cwd()]
    normalized = normalize_inputs(resolved_inputs)
    _, _, source_identifiers, source_fix_options = resolve_plan_source(
        inputs=normalized,
        store_type="json",
        plan_location=Path(plan_path),
        plan_id=plan_id,
    )
    resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options = (
        resolve_selection_inputs(
            cli_identifiers=identifiers,
            source_identifiers=source_identifiers,
            source_fix_options=source_fix_options,
        )
    )
    return normalized, resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options


def execute_check(
    inputs: Any,
    *,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_identifiers: Sequence[str] = (),
) -> list[dict[str, str]]:
    normalized = normalize_inputs(inputs)
    fixes = select_fixes(
        dataset=dataset,
        categories=categories,
        identifiers=identifiers,
        strict_identifiers=True,
        fix_options=fix_options,
        ordered_identifiers=ordered_identifiers,
    )
    return run_check(normalized, fixes)


def execute_fix(
    inputs: Any,
    *,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    write: bool = False,
    output_format: str = "auto",
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_identifiers: Sequence[str] = (),
) -> dict[str, int]:
    normalized = normalize_inputs(inputs)
    fixes = select_fixes(
        dataset=dataset,
        categories=categories,
        identifiers=identifiers,
        strict_identifiers=True,
        fix_options=fix_options,
        ordered_identifiers=ordered_identifiers,
    )
    return run_fix(normalized, fixes, dry_run=not write, output_format=output_format)


def execute_check_plan(
    plan_path: str | Path,
    *,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    plan_id: str | None = None,
) -> list[dict[str, str]]:
    normalized, resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options = (
        _resolve_plan_api_selection(
            plan_path=plan_path,
            inputs=inputs,
            identifiers=identifiers,
            plan_id=plan_id,
        )
    )

    return execute_check(
        normalized,
        dataset=dataset,
        categories=categories,
        identifiers=resolved_identifiers,
        fix_options=resolved_fix_options,
        ordered_identifiers=resolved_ordered_identifiers,
    )


def execute_fix_plan(
    plan_path: str | Path,
    *,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    write: bool = False,
    output_format: str = "auto",
    plan_id: str | None = None,
) -> dict[str, int]:
    normalized, resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options = (
        _resolve_plan_api_selection(
            plan_path=plan_path,
            inputs=inputs,
            identifiers=identifiers,
            plan_id=plan_id,
        )
    )

    return execute_fix(
        normalized,
        dataset=dataset,
        categories=categories,
        identifiers=resolved_identifiers,
        write=write,
        output_format=output_format,
        fix_options=resolved_fix_options,
        ordered_identifiers=resolved_ordered_identifiers,
    )


def execute_check_context(context: "RunContext") -> list[dict[str, str]]:
    """Run check execution from a pre-resolved run context."""

    return run_check(context.inputs, context.fixes)


def build_run_fix_kwargs(
    *,
    output_format: str,
    dry_run: bool,
    force_apply: bool,
    embed_provenance_metadata: bool,
    provenance_run_id: str | None,
) -> RunFixKwargs:
    """Build run_fix kwargs from command-level execution flags."""

    run_fix_kwargs: RunFixKwargs = {
        "dry_run": dry_run,
        "output_format": output_format,
    }
    if force_apply:
        run_fix_kwargs["force_apply"] = True
    if embed_provenance_metadata and not dry_run:
        run_fix_kwargs["embed_provenance_metadata"] = True
        run_fix_kwargs["provenance_run_id"] = provenance_run_id or ""
    return run_fix_kwargs


def execute_fix_context(
    context: "RunContext",
    *,
    dry_run: bool,
    force_apply: bool,
    embed_provenance_metadata: bool,
    provenance_run_id: str | None,
) -> dict[str, int]:
    """Run fix execution from a pre-resolved run context."""

    if force_apply and not context.resolved_identifiers:
        raise ValueError(
            "--force-apply requires explicit fix selection via --select or plan identifiers."
        )
    run_fix_kwargs = build_run_fix_kwargs(
        output_format=context.resolved_output_format,
        dry_run=dry_run,
        force_apply=force_apply,
        embed_provenance_metadata=embed_provenance_metadata,
        provenance_run_id=provenance_run_id,
    )
    return run_fix(context.inputs, context.fixes, **run_fix_kwargs)


def _normalize_identifiers(identifiers: Sequence[str]) -> set[str]:
    return {str(identifier).strip() for identifier in identifiers if str(identifier).strip()}


def _normalize_ordered_identifiers(identifiers: Sequence[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in identifiers:
        identifier = str(raw).strip()
        if not identifier or identifier in seen:
            continue
        out.append(identifier)
        seen.add(identifier)
    return out


def _validate_selected_identifiers(selected_identifiers: set[str]) -> None:
    unknown: list[str] = []
    for identifier in sorted(selected_identifiers):
        try:
            FixRegistry.resolve_identifier(identifier)
        except (KeyError, ValueError):
            unknown.append(identifier)
    if unknown:
        unknown_text = ", ".join(unknown)
        raise ValueError(f"Unknown fix identifier(s): {unknown_text}")


def _resolve_identifiers(identifiers: Sequence[str], *, strict: bool = False) -> list[str]:
    resolved: list[str] = []
    for item in identifiers:
        token = str(item).strip()
        if not token:
            continue
        try:
            resolved.append(FixRegistry.resolve_identifier(token))
        except (KeyError, ValueError):
            if strict:
                raise
    return resolved


def _normalize_fix_options(
    fix_options: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    if not fix_options:
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for identifier, options in fix_options.items():
        key = str(identifier).strip()
        if not key:
            continue
        try:
            resolved = FixRegistry.resolve_identifier(key)
        except (KeyError, ValueError):
            resolved = key
        normalized[resolved] = dict(options or {})
    return normalized


def select_fixes(
    dataset: Optional[str] = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    strict_identifiers: bool = False,
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_identifiers: Sequence[str] = (),
) -> List[Any]:
    filters: Dict[str, Any] = {}
    if dataset:
        filters["dataset"] = dataset
    if categories:
        filters["categories"] = list(categories) if len(categories) > 1 else categories[0]

    fixes = FixRegistry.discover(filters=filters or None)
    selected_identifiers = _normalize_identifiers(identifiers)
    normalized_ordered_identifiers = _normalize_ordered_identifiers(ordered_identifiers)
    normalized_fix_options = _normalize_fix_options(fix_options)
    configured_identifiers = set(normalized_fix_options.keys())

    if strict_identifiers and configured_identifiers:
        _validate_selected_identifiers(configured_identifiers)

    if strict_identifiers and normalized_ordered_identifiers:
        _validate_selected_identifiers(set(normalized_ordered_identifiers))
    if strict_identifiers and selected_identifiers:
        _validate_selected_identifiers(selected_identifiers)

    resolved_selected_identifiers = set(
        _resolve_identifiers(tuple(selected_identifiers), strict=False)
    )
    resolved_ordered_identifiers = _resolve_identifiers(
        tuple(normalized_ordered_identifiers), strict=False
    )

    if resolved_ordered_identifiers:
        by_id = {getattr(fix, "canonical_id", ""): fix for fix in fixes}
        missing = [item for item in resolved_ordered_identifiers if item not in by_id]
        if strict_identifiers and missing:
            raise ValueError(
                "Selected fix identifier(s) not available with current dataset/category filters: "
                + ", ".join(missing)
            )
        selected = [by_id[item] for item in resolved_ordered_identifiers if item in by_id]
    elif not resolved_selected_identifiers:
        selected = fixes
    else:
        selected = [
            fix
            for fix in fixes
            if getattr(fix, "canonical_id", "") in resolved_selected_identifiers
        ]

    if normalized_fix_options:
        for fix in selected:
            options = normalized_fix_options.get(getattr(fix, "canonical_id", ""))
            if options and hasattr(fix, "configure"):
                fix.configure(options)

    return selected


def run_check(inputs: Iterable[DataInput], fixes: Iterable[Any]) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    for data_input in inputs:
        dataset = data_input.load()
        identity = resolve_dataset_identity(dataset)
        for fix in fixes:
            if not dataset_type_matches_declared(
                getattr(fix, "dataset", None), identity.dataset_type
            ):
                continue
            if not fix.matches(dataset):
                continue
            for message in fix.check(dataset):
                findings.append(
                    {
                        "path": data_input.reference,
                        "fix_id": getattr(fix, "canonical_id", ""),
                        "name": fix.name,
                        "message": message,
                    }
                )
        close = getattr(dataset, "close", None)
        if callable(close):
            close()
    return findings


def run_fix(
    inputs: Iterable[DataInput],
    fixes: Iterable[Any],
    dry_run: bool = True,
    force_apply: bool = False,
    output_format: str = "auto",
    embed_provenance_metadata: bool = False,
    provenance_run_id: str | None = None,
) -> Dict[str, int]:
    changed = 0
    attempted = 0
    persist_attempted = 0
    persisted = 0
    persist_failed = 0
    output_adapter = get_output_adapter(output_format)
    for data_input in inputs:
        dataset = data_input.load()
        identity = resolve_dataset_identity(dataset)
        dataset_changed = False
        applied_fix_ids: list[str] = []
        for fix in fixes:
            canonical_id = getattr(fix, "canonical_id", "")
            attempted_fix, changed_fix = _apply_configured_fix(
                dataset,
                fix,
                dataset_type=identity.dataset_type,
                dry_run=dry_run,
                force_apply=force_apply,
                fix_id=canonical_id,
            )
            if attempted_fix:
                attempted += 1
            if changed_fix:
                changed += 1
                dataset_changed = True
                applied_fix_ids.append(canonical_id)
        if dataset_changed and not dry_run:
            if embed_provenance_metadata:
                dataset.attrs["woodpecker_provenance"] = json.dumps(
                    {
                        "run_id": provenance_run_id or "",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "source": data_input.reference,
                        "applied_fix_ids": applied_fix_ids,
                    },
                    sort_keys=True,
                )
            persist_attempted += 1
            if data_input.save(dataset, dry_run=False, output_adapter=output_adapter):
                persisted += 1
            else:
                persist_failed += 1
        close = getattr(dataset, "close", None)
        if callable(close):
            close()
    return {
        "attempted": attempted,
        "changed": changed,
        "persist_attempted": persist_attempted,
        "persisted": persisted,
        "persist_failed": persist_failed,
    }


def _apply_configured_fix(
    dataset: Any,
    fix: Any,
    *,
    dataset_type: str | None,
    dry_run: bool,
    force_apply: bool,
    fix_id: str,
) -> tuple[bool, bool]:
    if not dataset_type_matches_declared(getattr(fix, "dataset", None), dataset_type):
        return False, False

    if not force_apply and not fix.matches(dataset):
        return False, False

    if not hasattr(fix, "apply"):
        raise TypeError(f"Fix '{fix_id}' does not implement apply()")

    return True, bool(fix.apply(dataset, dry_run=dry_run))


def _instantiate_fix(registry: Any, fix_id: str) -> Any:
    instantiate = getattr(registry, "instantiate", None)
    if not callable(instantiate):
        raise TypeError("Registry must provide instantiate(canonical_id)")
    return instantiate(fix_id)


def apply_fix_plan(ds: Any, plan: "FixPlan", registry: Any) -> Any:
    """Resolve plan fix identifiers and apply fixes in order."""

    identity = resolve_dataset_identity(ds)

    for ref in plan.steps:
        resolved_fix_id = plan.resolve_fix_identifier(ref)
        fix = _instantiate_fix(registry, resolved_fix_id)

        if hasattr(fix, "configure"):
            configured_fix = fix.configure(ref.options)
            if configured_fix is not None:
                fix = configured_fix

        _apply_configured_fix(
            ds,
            fix,
            dataset_type=identity.dataset_type,
            dry_run=False,
            force_apply=False,
            fix_id=resolved_fix_id,
        )

    return ds


def execute_load_plans(
    store_type: str,
    plan_location: Path,
    from_plan: Path,
    from_store: str,
    plan_id: str | None = None,
) -> dict:
    """Load plans into a target store from a source store location."""
    from woodpecker.stores.helpers import create_fix_plan_store
    from woodpecker.plans.resolver import resolve_load_source_plans

    target_store = create_fix_plan_store(store_type, plan_location)
    plans = resolve_load_source_plans(
        from_plan=from_plan,
        from_store_type=from_store,
        plan_id=plan_id,
    )
    # For test monkeypatching (do not use at runtime)
    try:
        from woodpecker.plans.resolver import resolve_load_source_plans
        from woodpecker.stores.helpers import create_fix_plan_store
    except ImportError:
        resolve_load_source_plans = None
        create_fix_plan_store = None
    for plan in plans:
        target_store.save_plan(plan)
    plan_ids = [plan.id or "<unnamed>" for plan in plans]
    return {
        "loaded": len(plans),
        "target_store": store_type,
        "target_path": str(plan_location),
        "plan_ids": plan_ids,
    }


def write_fix_provenance(
    context,
    stats,
    dry_run: bool,
    store_type: str,
    plan_location,
    provenance_path,
):
    """Write a provenance document for a fix run."""
    from woodpecker.provenance import build_prov_document, write_prov_document
    from woodpecker.cli import format_provenance_source
    provenance_source = format_provenance_source(context, store_type, plan_location)
    prov = build_prov_document(
        inputs=context.inputs,
        selected_fix_ids=[getattr(fix, "canonical_id", "") for fix in context.fixes],
        selected_fixes=context.fixes,
        selected_plans=context.selected_plans,
        stats=stats,
        mode="dry-run" if dry_run else "write",
        output_format=context.resolved_output_format,
        plan=provenance_source,
    )
    write_prov_document(prov, provenance_path)
