from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence

from woodpecker.data_input import DataInput, get_output_adapter
from woodpecker.fixes.registry import FixRegistry


def _normalize_codes(codes: Sequence[str]) -> set[str]:
    return {code.strip().upper() for code in codes if code.strip()}


def select_fixes(
    dataset: Optional[str] = None, categories: Sequence[str] = (), codes: Sequence[str] = ()
) -> List[Any]:
    filters: Dict[str, Any] = {}
    if dataset:
        filters["dataset"] = dataset
    if categories:
        filters["categories"] = list(categories) if len(categories) > 1 else categories[0]

    fixes = FixRegistry.discover(filters=filters or None)
    selected_codes = _normalize_codes(codes)
    if not selected_codes:
        return fixes

    return [fix for fix in fixes if getattr(fix, "code", "").upper() in selected_codes]


def run_check(inputs: Iterable[DataInput], fixes: Iterable[Any]) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    for data_input in inputs:
        dataset = data_input.load()
        for fix in fixes:
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
    output_format: str = "auto",
) -> Dict[str, int]:
    changed = 0
    attempted = 0
    persist_attempted = 0
    persisted = 0
    persist_failed = 0
    output_adapter = get_output_adapter(output_format)
    for data_input in inputs:
        dataset = data_input.load()
        dataset_changed = False
        for fix in fixes:
            if not fix.matches(dataset):
                continue
            attempted += 1
            if fix.apply(dataset, dry_run=dry_run):
                changed += 1
                dataset_changed = True
        if dataset_changed and not dry_run:
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
