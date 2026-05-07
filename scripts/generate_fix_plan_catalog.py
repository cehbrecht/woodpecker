from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from woodpecker.plans.models import FixPlan
from woodpecker.stores.json_store import JsonFixPlanStore

DEFAULT_PLAN_DIR = Path("tests/integration/plans")


def _markdown_cell(value: object) -> str:
    text = str(value or "")
    return text.replace("\n", "<br>").replace("|", "\\|")


def _format_match(plan: FixPlan) -> str:
    if plan.match is None:
        return ""

    parts: list[str] = []
    if plan.match.attrs:
        attrs = ", ".join(f"{key}={value}" for key, value in sorted(plan.match.attrs.items()))
        parts.append(f"attrs: {attrs}")
    if plan.match.path_patterns:
        parts.append(f"paths: {', '.join(plan.match.path_patterns)}")
    return "; ".join(parts)


def _format_steps(plan: FixPlan) -> str:
    return "<br>".join(step.id for step in plan.steps)


def _plan_payload(plan: FixPlan, source_files: list[str]) -> dict[str, Any]:
    payload = plan.model_dump()
    payload["prefix"] = plan.prefix
    payload["suffix"] = plan.suffix
    payload["source"] = "integration-tests"
    payload["source_files"] = source_files
    payload["step_ids"] = [step.id for step in plan.steps]
    return payload


def load_integration_plans(plan_dir: Path = DEFAULT_PLAN_DIR) -> list[tuple[FixPlan, list[str]]]:
    """Load integration-test plans, raising on duplicate plan ids."""

    plans_by_id: dict[str, FixPlan] = {}
    source_files_by_id: dict[str, list[str]] = {}

    for path in sorted(plan_dir.glob("*")):
        if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
            continue

        source_label = path.as_posix()
        for plan in JsonFixPlanStore(path).list_plans():
            existing = plans_by_id.get(plan.id)
            if existing is not None:
                raise ValueError(f"Duplicate definition for plan id '{plan.id}'")
            plans_by_id[plan.id] = plan
            source_files_by_id.setdefault(plan.id, []).append(source_label)

    return [(plans_by_id[plan_id], source_files_by_id[plan_id]) for plan_id in sorted(plans_by_id)]


def generate_fix_plan_catalog(
    md_path: str = "docs/FIX_PLANS.md",
    json_path: str = "docs/FIX_PLANS.json",
    plan_dir: str = str(DEFAULT_PLAN_DIR),
) -> None:
    plans = load_integration_plans(Path(plan_dir))

    md_lines = [
        "Fix plans are curated recipes for selecting and applying fixes to matching datasets.",
        "",
        "Source values currently point to integration-test plans used by the examples.",
        "",
        "| ID | Description | Match | Steps | Source Files |",
        "|----|-------------|-------|-------|--------------|",
    ]
    json_list = []

    for plan, source_files in plans:
        md_lines.append(
            f"| {_markdown_cell(plan.id)}"
            f" | {_markdown_cell(plan.description)}"
            f" | {_markdown_cell(_format_match(plan))}"
            f" | {_markdown_cell(_format_steps(plan))}"
            f" | {_markdown_cell('<br>'.join(source_files))} |"
        )
        json_list.append(_plan_payload(plan, source_files))

    Path(md_path).write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    Path(json_path).write_text(json.dumps(json_list, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {md_path} and {json_path} with {len(plans)} fix plans")


if __name__ == "__main__":
    generate_fix_plan_catalog()
