from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence

from woodpecker.identity import dataset_type_matches_declared, resolve_dataset_identity
from woodpecker.inout import DataInput, get_output_adapter

from .registry import FixRegistry


def _normalize_codes(codes: Sequence[str]) -> set[str]:
    return {code.strip().upper() for code in codes if code.strip()}


def _normalize_ordered_codes(codes: Sequence[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in codes:
        code = raw.strip().upper()
        if not code or code in seen:
            continue
        out.append(code)
        seen.add(code)
    return out


def _validate_selected_codes(selected_codes: set[str]) -> None:
    available = {code.upper() for code in FixRegistry.registered_codes()}
    unknown = sorted(code for code in selected_codes if code not in available)
    if unknown:
        unknown_text = ", ".join(unknown)
        raise ValueError(f"Unknown fix code(s): {unknown_text}")


def _normalize_fix_options(
    fix_options: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    if not fix_options:
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for code, options in fix_options.items():
        key = str(code).strip().upper()
        if not key:
            continue
        normalized[key] = dict(options or {})
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

    if ordered:
        if strict_codes:
            _validate_selected_codes(set(ordered))
        by_code = {getattr(fix, "code", "").upper(): fix for fix in fixes}
        missing = [code for code in ordered if code not in by_code]
        if strict_codes and missing:
            raise ValueError(
                "Selected fix code(s) not available with current dataset/category filters: "
                + ", ".join(missing)
            )
        selected = [by_code[code] for code in ordered if code in by_code]
    elif not selected_codes:
        selected = fixes
    else:
        if strict_codes:
            _validate_selected_codes(selected_codes)

        selected = [fix for fix in fixes if getattr(fix, "code", "").upper() in selected_codes]

    if normalized_fix_options:
        for fix in selected:
            options = normalized_fix_options.get(getattr(fix, "code", "").upper())
            if options and hasattr(fix, "configure"):
                fix.configure(options)

    return selected


def run_check(inputs: Iterable[DataInput], fixes: Iterable[Any]) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    for data_input in inputs:
        dataset = data_input.load()
        identity = resolve_dataset_identity(dataset)
        for fix in fixes:
            if not dataset_type_matches_declared(getattr(fix, "dataset", None), identity.dataset_type):
                continue
            if not fix.matches(dataset):
                continue
            for message in fix.check(dataset):
                findings.append(
                    {
                        "path": data_input.reference,
                        "code": fix.code,
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
            if not dataset_type_matches_declared(getattr(fix, "dataset", None), identity.dataset_type):
                continue
            if not force_apply and not fix.matches(dataset):
                continue
            attempted += 1
            if fix.apply(dataset, dry_run=dry_run):
                changed += 1
                dataset_changed = True
                applied_codes.append(getattr(fix, "code", ""))
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
