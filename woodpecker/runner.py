from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from woodpecker.fixes.registry import FixRegistry


def collect_netcdf_files(paths: Sequence[Path]) -> List[Path]:
    files: List[Path] = []
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".nc":
            files.append(path)
            continue
        if path.is_dir():
            files.extend(sorted(path.rglob("*.nc")))
    return files


def _normalize_codes(codes: Sequence[str]) -> set[str]:
    return {code.strip().upper() for code in codes if code.strip()}


def select_fixes(dataset: Optional[str] = None, categories: Sequence[str] = (), codes: Sequence[str] = ()) -> List[Any]:
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


def run_check(files: Iterable[Path], fixes: Iterable[Any]) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    for file_path in files:
        for fix in fixes:
            if not fix.matches(file_path):
                continue
            for message in fix.check(file_path):
                findings.append(
                    {
                        "path": str(file_path),
                        "code": fix.code,
                        "name": fix.name,
                        "message": message,
                    }
                )
    return findings


def run_fix(files: Iterable[Path], fixes: Iterable[Any], dry_run: bool = True) -> Dict[str, int]:
    changed = 0
    attempted = 0
    for file_path in files:
        for fix in fixes:
            if not fix.matches(file_path):
                continue
            attempted += 1
            if fix.apply(file_path, dry_run=dry_run):
                changed += 1
    return {"attempted": attempted, "changed": changed}
