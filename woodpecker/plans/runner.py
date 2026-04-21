from __future__ import annotations

import inspect
import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from woodpecker.fixes.registry import FixRegistry
from woodpecker.identity import dataset_type_matches_declared, resolve_dataset_identity
from woodpecker.inout import DataInput, get_output_adapter

from .models import FixPlan


def _normalize_codes(codes: Sequence[str]) -> set[str]:
    return {str(code).strip() for code in codes if str(code).strip()}


def _normalize_ordered_codes(codes: Sequence[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in codes:
        code = str(raw).strip()
        if not code or code in seen:
            continue
        out.append(code)
        seen.add(code)
    return out


def _validate_selected_codes(selected_codes: set[str]) -> None:
    unknown: list[str] = []
    for code in sorted(selected_codes):
        try:
            FixRegistry.resolve_identifier(code)
        except (KeyError, ValueError):
            unknown.append(code)
    if unknown:
        unknown_text = ", ".join(unknown)
        raise ValueError(f"Unknown fix code(s): {unknown_text}")


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
    codes: Sequence[str] = (),
    strict_codes: bool = False,
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_codes: Sequence[str] = (),
) -> List[Any]:
    filters: Dict[str, Any] = {}
    if dataset:
        filters["dataset"] = dataset
    if categories:
        filters["categories"] = list(categories) if len(categories) > 1 else categories[0]

    fixes = FixRegistry.discover(filters=filters or None)
    selected_codes = _normalize_codes(codes)
    ordered = _normalize_ordered_codes(ordered_codes)
    normalized_fix_options = _normalize_fix_options(fix_options)
    configured_codes = set(normalized_fix_options.keys())

    if strict_codes and configured_codes:
        _validate_selected_codes(configured_codes)

    if strict_codes and ordered:
        _validate_selected_codes(set(ordered))
    if strict_codes and selected_codes:
        _validate_selected_codes(selected_codes)

    resolved_selected_codes = set(_resolve_identifiers(tuple(selected_codes), strict=False))
    resolved_ordered = _resolve_identifiers(tuple(ordered), strict=False)

    if resolved_ordered:
        by_code = {getattr(fix, "code", ""): fix for fix in fixes}
        missing = [code for code in resolved_ordered if code not in by_code]
        if strict_codes and missing:
            raise ValueError(
                "Selected fix code(s) not available with current dataset/category filters: "
                + ", ".join(missing)
            )
        selected = [by_code[code] for code in resolved_ordered if code in by_code]
    elif not resolved_selected_codes:
        selected = fixes
    else:
        selected = [fix for fix in fixes if getattr(fix, "code", "") in resolved_selected_codes]

    if normalized_fix_options:
        for fix in selected:
            options = normalized_fix_options.get(getattr(fix, "code", ""))
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
                        "code": getattr(fix, "canonical_id", getattr(fix, "code", "")),
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
        applied_codes: list[str] = []
        for fix in fixes:
            if not dataset_type_matches_declared(
                getattr(fix, "dataset", None), identity.dataset_type
            ):
                continue
            if not force_apply and not fix.matches(dataset):
                continue
            attempted += 1
            if fix.apply(dataset, dry_run=dry_run):
                changed += 1
                dataset_changed = True
                applied_codes.append(getattr(fix, "canonical_id", getattr(fix, "code", "")))
        if dataset_changed and not dry_run:
            if embed_provenance_metadata:
                dataset.attrs["woodpecker_provenance"] = json.dumps(
                    {
                        "run_id": provenance_run_id or "",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "source": data_input.reference,
                        "applied_codes": applied_codes,
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


def resolve_fix(registry: Any, fix_id: str) -> Any:
    key = FixRegistry.resolve_identifier(str(fix_id).strip())
    source: Any | None = None
    if isinstance(registry, Mapping):
        source = registry.get(key)
    elif hasattr(registry, "_registry"):
        source = getattr(registry, "_registry", {}).get(key)
    elif hasattr(registry, "get"):
        source = registry.get(key)

    if source is None:
        raise KeyError(f"Unknown fix id: {key}")

    if isinstance(source, type):
        return source()
    if callable(source) and not hasattr(source, "check"):
        return source()
    return source


def invoke_with_optional_options(method: Any, ds: Any, options: Mapping[str, Any]) -> Any:
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        return method(ds, options=options)

    parameters = signature.parameters.values()
    supports_options = any(
        param.kind is inspect.Parameter.VAR_KEYWORD or param.name == "options"
        for param in parameters
    )
    if supports_options:
        return method(ds, options=options)
    return method(ds)


def apply_fix_plan(ds: Any, plan: FixPlan, registry: Any) -> Any:
    """Resolve plan fix ids and apply fixes in order.

    For each fix: call check(), then call fix()/apply() when check result indicates apply.
    """

    for ref in plan.fixes:
        resolved_fix_id = plan.resolve_fix_identifier(ref)
        fix = resolve_fix(registry, resolved_fix_id)

        if hasattr(fix, "configure"):
            fix = fix.configure(ref.options)

        if not hasattr(fix, "check"):
            raise TypeError(f"Fix '{ref.fix}' does not implement check()")
        should_apply = invoke_with_optional_options(fix.check, ds, ref.options)
        if not isinstance(should_apply, bool):
            # Backward-compatible behavior for legacy fixes with non-bool check output.
            should_apply = True

        if not should_apply:
            continue

        if hasattr(fix, "fix"):
            invoke_with_optional_options(fix.fix, ds, ref.options)
        elif hasattr(fix, "apply"):
            fix.apply(ds, dry_run=False)
        else:
            raise TypeError(f"Fix '{ref.fix}' does not implement fix() or apply()")

    return ds
