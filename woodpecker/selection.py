from __future__ import annotations

from typing import Any, Optional, Sequence

from woodpecker.fixes.registry import FixRegistry


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
) -> list[Any]:
    filters: dict[str, Any] = {}
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
