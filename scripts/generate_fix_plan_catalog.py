from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from woodpecker.fix_plans import FixPlanLoader
from woodpecker.fix_plans.models import FixPlan
from woodpecker.stores.json_store import JsonFixPlanStore

DEFAULT_PLAN_DIR = Path("tests/integration/plans")
GITHUB_BLOB_BASE_URL = "https://github.com/cehbrecht/woodpecker/blob/main"
DOCS_FIX_PLAN_ENV = "_WOODPECKER_DOCS_FIX_PLAN_PATH"


def _markdown_cell(value: object) -> str:
    text = str(value or "")
    return text.replace("\n", "<br>").replace("|", "\\|")


def _format_match(plan: FixPlan) -> str:
    if plan.match is None:
        return ""

    parts: list[str] = []
    if plan.match.dataset_id_patterns:
        parts.append(f"dataset ids: {', '.join(plan.match.dataset_id_patterns)}")
    if plan.match.attrs:
        attrs = ", ".join(f"{key}={value}" for key, value in sorted(plan.match.attrs.items()))
        parts.append(f"attrs: {attrs}")
    if plan.match.path_patterns:
        parts.append(f"paths: {', '.join(plan.match.path_patterns)}")
    return "; ".join(parts)


def _format_steps(plan: FixPlan) -> str:
    return "<br>".join(step.id for step in plan.steps)


def _github_source_links(source_files: list[str]) -> str:
    return "<br>".join(
        f"[{source_file}]({GITHUB_BLOB_BASE_URL}/{source_file})" for source_file in source_files
    )


def _plan_payload(plan: FixPlan, source_files: list[str], source: str) -> dict[str, Any]:
    payload = plan.model_dump()
    payload["prefix"] = plan.prefix
    payload["suffix"] = plan.suffix
    payload["source"] = source
    payload["source_files"] = source_files
    payload["step_ids"] = [step.id for step in plan.steps]
    return payload


def _add_plan(
    plan: FixPlan,
    source_files: list[str],
    source: str,
    plans_by_id: dict[str, FixPlan],
    source_files_by_id: dict[str, list[str]],
    source_by_id: dict[str, str],
) -> None:
    existing = plans_by_id.get(plan.id)
    if existing is not None:
        raise ValueError(f"Duplicate definition for plan id '{plan.id}'")
    plans_by_id[plan.id] = plan
    source_files_by_id[plan.id] = source_files
    source_by_id[plan.id] = source


def load_integration_plans(
    plan_dir: Path = DEFAULT_PLAN_DIR,
) -> list[tuple[FixPlan, list[str], str]]:
    """Load integration-test plans, raising on duplicate plan ids."""

    plans_by_id: dict[str, FixPlan] = {}
    source_files_by_id: dict[str, list[str]] = {}
    source_by_id: dict[str, str] = {}

    for path in sorted(plan_dir.glob("*")):
        if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
            continue

        source_label = path.as_posix()
        for plan in JsonFixPlanStore(path).list_plans():
            _add_plan(
                plan,
                [source_label],
                "integration-tests",
                plans_by_id,
                source_files_by_id,
                source_by_id,
            )

    return [
        (plans_by_id[plan_id], source_files_by_id[plan_id], source_by_id[plan_id])
        for plan_id in sorted(plans_by_id)
    ]


def load_plugin_plans() -> list[tuple[FixPlan, list[str], str]]:
    """Load plan documents bundled as package resources by local plugins."""

    return load_discovered_plans(include_core=False)


def _package_source_file(label: str) -> tuple[str, str]:
    package_resource = label.removeprefix("package:")
    package, resource_path = package_resource.split("/", 1)
    if package == "woodpecker.fix_plans":
        return "core", f"woodpecker/fix_plans/{resource_path}"
    if package.startswith("woodpecker_") and package.endswith("_plugin"):
        distribution = package.replace("_", "-")
        return "plugin:" + package, f"plugins/{distribution}/src/{package}/{resource_path}"
    return "package:" + package, package.replace(".", "/") + "/" + resource_path


def load_discovered_plans(include_core: bool = True) -> list[tuple[FixPlan, list[str], str]]:
    """Load package-bundled plans through the same loader used at runtime."""

    loader = FixPlanLoader(
        env_var=DOCS_FIX_PLAN_ENV,
        user_dirs=(),
        system_dirs=(),
        core_packages=("woodpecker.fix_plans",) if include_core else (),
    )
    plans_by_id: dict[str, FixPlan] = {}
    source_files_by_id: dict[str, list[str]] = {}
    source_by_id: dict[str, str] = {}

    for document in loader.load_documents():
        source, source_file = _package_source_file(document.label)
        for plan in document.plans:
            _add_plan(
                plan,
                [source_file],
                source,
                plans_by_id,
                source_files_by_id,
                source_by_id,
            )

    return [
        (plans_by_id[plan_id], source_files_by_id[plan_id], source_by_id[plan_id])
        for plan_id in sorted(plans_by_id)
    ]


def generate_fix_plan_catalog(
    md_path: str = "docs/FIX_PLANS.md",
    json_path: str = "docs/FIX_PLANS.json",
    plan_dir: str = str(DEFAULT_PLAN_DIR),
    include_plugin_plans: bool = True,
) -> None:
    plans = (
        load_integration_plans(Path(plan_dir))
        if not include_plugin_plans
        else load_discovered_plans(include_core=True)
    )

    md_lines = [
        "# Generated Fix Plans Reference",
        "",
        "This page is generated from plan documents discovered by `FixPlanLoader`.",
        "",
        "Fix plans are curated recipes for selecting and applying fixes to matching datasets.",
        "",
        "Source values point to core or package-bundled plugin plans discovered by FixPlanLoader.",
        "",
        "| ID | Description | Match | Steps | Source | Source Files |",
        "|----|-------------|-------|-------|--------|--------------|",
    ]
    json_list = []

    for plan, source_files, source in plans:
        md_lines.append(
            f"| {_markdown_cell(plan.id)}"
            f" | {_markdown_cell(plan.description)}"
            f" | {_markdown_cell(_format_match(plan))}"
            f" | {_markdown_cell(_format_steps(plan))}"
            f" | {_markdown_cell(source)}"
            f" | {_github_source_links(source_files)} |"
        )
        json_list.append(_plan_payload(plan, source_files, source))

    Path(md_path).write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    Path(json_path).write_text(json.dumps(json_list, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {md_path} and {json_path} with {len(plans)} fix plans")


if __name__ == "__main__":
    generate_fix_plan_catalog()
