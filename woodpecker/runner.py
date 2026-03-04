from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence

from woodpecker.data_input import DataInput
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
        for fix in fixes:
            if not fix.matches(data_input):
                continue
            for message in fix.check(data_input):
                findings.append(
                    {
                        "path": data_input.reference,
                        "code": fix.code,
                        "name": fix.name,
                        "message": message,
                    }
                )
    return findings


def run_fix(
    inputs: Iterable[DataInput], fixes: Iterable[Any], dry_run: bool = True
) -> Dict[str, int]:
    changed = 0
    attempted = 0
    for data_input in inputs:
        for fix in fixes:
            if not fix.matches(data_input):
                continue
            attempted += 1
            if fix.apply(data_input, dry_run=dry_run):
                changed += 1
    return {"attempted": attempted, "changed": changed}
