from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence

from woodpecker.fixes.registry import FixRegistry
from woodpecker.identity import dataset_type_matches_declared, resolve_dataset_identity
from woodpecker.inout import DataInput, get_output_adapter

from .models import FixPlan


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


def apply_fix_plan(ds: Any, plan: FixPlan, registry: Any) -> Any:
    """Resolve plan fix identifiers and apply fixes in order."""

    identity = resolve_dataset_identity(ds)

    for ref in plan.fixes:
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
