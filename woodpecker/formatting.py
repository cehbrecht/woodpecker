from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from .plans.models import FixPlan


def _fix_json_payload(fix: object) -> dict[str, object]:
    if hasattr(fix, "model_dump"):
        return dict(fix.model_dump())
    if hasattr(fix, "metadata") and callable(fix.metadata):
        return dict(fix.metadata())
    raise TypeError("Fix instance does not support JSON metadata serialization")


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
                f"{getattr(fix, 'canonical_id', '')} | "
                f"{getattr(fix, 'name', '')} | "
                f"{getattr(fix, 'description', '')} | "
                f"{cats} | "
                f"{getattr(fix, 'dataset', None) or ''} | "
                f"{getattr(fix, 'priority', 10)} |"
            )
        return "\n".join(lines)

    lines: list[str] = []
    for fix in fixes:
        cats = ", ".join(getattr(fix, "categories", []) or [])
        lines.append(
            f"{getattr(fix, 'canonical_id', '')}: {getattr(fix, 'description', '')} "
            f"(cats: {cats}; dataset: {getattr(fix, 'dataset', None) or '-'}; "
            f"priority: {getattr(fix, 'priority', 10)})"
        )
    return "\n".join(lines)


def format_findings(findings: list[dict[str, str]], fmt: str) -> str:
    """Format check findings for CLI output."""

    if fmt == "json":
        return json.dumps(findings, indent=2)
    return "\n".join(
        f"{item['path']}: {item['fix_id']} {item['message']}"
        for item in findings
    )


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
    """Format stored plans for CLI output."""

    if fmt == "json":
        return json.dumps([plan.model_dump() for plan in plans], indent=2)

    if not plans:
        return "No plans found."

    lines: list[str] = []
    for plan in plans:
        plan_id = plan.id or "<unnamed>"
        lines.append(f"{plan_id}: {len(plan.steps)} fixes")
    return "\n".join(lines)
