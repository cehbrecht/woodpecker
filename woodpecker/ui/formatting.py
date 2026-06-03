from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..fixes.registry import UNPRIORITIZED
from ..recipes.models import Recipe


def _priority_value(fix: object) -> int:
    return int(getattr(fix, "priority", UNPRIORITIZED))


def _fix_json_payload(fix: object) -> dict[str, object]:
    if hasattr(fix, "model_dump"):
        return dict(fix.model_dump())
    if hasattr(fix, "metadata") and callable(fix.metadata):
        return dict(fix.metadata())
    raise TypeError("Fix function instance does not support JSON metadata serialization")


def format_fixes(fixes: list[object], fmt: str) -> str:
    """Format discovered fixes for CLI output."""

    if fmt == "json":
        payload = [_fix_json_payload(fix) for fix in fixes]
        return json.dumps(payload, indent=2)

    if fmt == "md":
        lines = [
            "| ID | Name | Description | Categories | Dataset | Priority |",
            "|----|------|-------------|------------|---------|---------|",
        ]
        for fix in fixes:
            cats = ", ".join(getattr(fix, "categories", []) or [])
            lines.append(
                "| "
                f"{getattr(fix, 'id', '')} | "
                f"{getattr(fix, 'name', '')} | "
                f"{getattr(fix, 'description', '')} | "
                f"{cats} | "
                f"{getattr(fix, 'dataset', None) or ''} | "
                f"{_priority_value(fix)} |"
            )
        return "\n".join(lines)

    lines: list[str] = []
    for fix in fixes:
        cats = ", ".join(getattr(fix, "categories", []) or [])
        lines.append(
            f"{getattr(fix, 'id', '')}: {getattr(fix, 'description', '')} "
            f"(cats: {cats}; dataset: {getattr(fix, 'dataset', None) or '-'}; "
            f"priority: {_priority_value(fix)})"
        )
    return "\n".join(lines)


def format_findings(findings: list[dict[str, str]], fmt: str) -> str:
    """Format check findings for CLI output."""

    if fmt == "json":
        return json.dumps(findings, indent=2)
    return "\n".join(f"{item['path']}: {item['fix_id']} {item['message']}" for item in findings)


def format_fix_stats(
    stats: Mapping[str, Any],
    *,
    fmt: str,
    dry_run: bool,
    force_apply: bool,
    resolved_output_format: str,
    provenance: bool,
    provenance_path: Path,
) -> str:
    """Format fix execution stats for CLI output."""

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
    preview = list(stats.get("preview", ()))
    if not dry_run:
        return (
            f"Fix run complete ({mode}): {stats['attempted']} fix applications attempted, "
            f"{stats['changed']} files changed, {stats['persisted']} persisted, "
            f"{stats['persist_failed']} failed to persist."
        )
    lines = [
        f"Fix run complete ({mode}): {stats['attempted']} fix applications attempted, "
        f"{stats['changed']} files changed."
    ]
    if preview:
        lines.append("Preview:")
        for item in preview:
            outcome = "would change" if item.get("changed") else "no change"
            name = item.get("name") or item.get("fix_id", "")
            lines.append(f"  {item.get('path', '')}: {item.get('fix_id', '')} ({name}) - {outcome}")
    return "\n".join(lines)


def format_recipes(recipes: Sequence[Recipe], fmt: str) -> str:
    """Format stored recipes for CLI output."""

    if fmt == "json":
        return json.dumps([recipe.model_dump() for recipe in recipes], indent=2)

    if not recipes:
        return "No recipes found."

    lines: list[str] = []
    for recipe in recipes:
        recipe_id = recipe.id or "<unnamed>"
        step_count = len(recipe.steps)
        label = "step" if step_count == 1 else "steps"
        lines.append(f"{recipe_id}: {step_count} {label}")
    return "\n".join(lines)
