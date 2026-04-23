from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import woodpecker.fixes  # noqa: F401
from woodpecker.inout import normalize_inputs
from woodpecker.plans.matcher import plan_matches_dataset
from woodpecker.plans.models import FixPlan
from woodpecker.plans.runner import run_check, run_fix, select_fixes
from woodpecker.stores.json_store import JsonFixPlanStore


def check(
    inputs: Any,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    codes: Sequence[str] = (),
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_codes: Sequence[str] = (),
) -> list[dict[str, str]]:
    normalized = normalize_inputs(inputs)
    fixes = select_fixes(
        dataset=dataset,
        categories=categories,
        codes=codes,
        strict_codes=True,
        fix_options=fix_options,
        ordered_codes=ordered_codes,
    )
    return run_check(normalized, fixes)


def fix(
    inputs: Any,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    codes: Sequence[str] = (),
    write: bool = False,
    output_format: str = "auto",
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_codes: Sequence[str] = (),
) -> dict[str, int]:
    normalized = normalize_inputs(inputs)
    fixes = select_fixes(
        dataset=dataset,
        categories=categories,
        codes=codes,
        strict_codes=True,
        fix_options=fix_options,
        ordered_codes=ordered_codes,
    )
    return run_fix(normalized, fixes, dry_run=not write, output_format=output_format)


def _plan_codes_and_options(plan: FixPlan) -> tuple[tuple[str, ...], dict[str, dict[str, Any]]]:
    codes = tuple(plan.resolve_fix_identifier(ref) for ref in plan.fixes)
    options = {plan.resolve_fix_identifier(ref): dict(ref.options) for ref in plan.fixes}
    return codes, options


def _select_plan_from_document(
    *,
    plans: Sequence[FixPlan],
    inputs: Sequence[Any],
    plan_id: str | None = None,
) -> FixPlan:
    matches: dict[str, FixPlan] = {}
    for item in inputs:
        dataset = item.load()
        try:
            for plan in plans:
                if plan_matches_dataset(plan, dataset, path=item.reference):
                    key = plan.id or str(id(plan))
                    matches[key] = plan
        finally:
            close = getattr(dataset, "close", None)
            if callable(close):
                close()

    selected = list(matches.values())
    if plan_id:
        selected = [plan for plan in selected if plan.id == plan_id]
        if not selected:
            raise ValueError(f"No matching plan found for plan_id '{plan_id}'")

    if not selected:
        raise ValueError("No matching plans found in plan document for selected inputs")
    if len(selected) > 1:
        ids = [plan.id for plan in selected if plan.id]
        label = ", ".join(ids) if ids else f"{len(selected)} unnamed plans"
        raise ValueError("Multiple matching plans found; provide plan_id to choose one: " + label)
    return selected[0]


def _load_plans(plan_path: str | Path) -> list[FixPlan]:
    store = JsonFixPlanStore(Path(plan_path))
    return store.list_plans()


def check_plan(
    plan_path: str | Path,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    codes: Sequence[str] = (),
    plan_id: str | None = None,
) -> list[dict[str, str]]:
    plans = _load_plans(plan_path)
    resolved_inputs = inputs if inputs is not None else [Path.cwd()]
    normalized = normalize_inputs(resolved_inputs)
    selected = _select_plan_from_document(plans=plans, inputs=normalized, plan_id=plan_id)
    plan_codes, plan_fix_options = _plan_codes_and_options(selected)

    resolved_dataset = dataset
    resolved_categories = categories
    resolved_codes = codes or plan_codes
    resolved_fix_options = plan_fix_options
    resolved_ordered_codes = (
        tuple(code.strip() for code in codes if code.strip()) if codes else tuple(plan_codes)
    )
    return check(
        normalized,
        dataset=resolved_dataset,
        categories=resolved_categories,
        codes=resolved_codes,
        fix_options=resolved_fix_options,
        ordered_codes=resolved_ordered_codes,
    )


def fix_plan(
    plan_path: str | Path,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    codes: Sequence[str] = (),
    write: bool = False,
    output_format: str = "auto",
    plan_id: str | None = None,
) -> dict[str, int]:
    plans = _load_plans(plan_path)
    resolved_inputs = inputs if inputs is not None else [Path.cwd()]
    normalized = normalize_inputs(resolved_inputs)
    selected = _select_plan_from_document(plans=plans, inputs=normalized, plan_id=plan_id)
    plan_codes, plan_fix_options = _plan_codes_and_options(selected)

    resolved_dataset = dataset
    resolved_categories = categories
    resolved_codes = codes or plan_codes
    resolved_fix_options = plan_fix_options
    resolved_ordered_codes = (
        tuple(code.strip() for code in codes if code.strip()) if codes else tuple(plan_codes)
    )
    resolved_output = output_format
    return fix(
        normalized,
        dataset=resolved_dataset,
        categories=resolved_categories,
        codes=resolved_codes,
        write=write,
        output_format=resolved_output,
        fix_options=resolved_fix_options,
        ordered_codes=resolved_ordered_codes,
    )
