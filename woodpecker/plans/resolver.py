from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, Sequence

from woodpecker.inout import DataInput, normalize_inputs
from woodpecker.plans.io import load_fix_plan_document
from woodpecker.plans.matcher import plan_matches_dataset
from woodpecker.plans.models import FixPlan
from woodpecker.plans.runner import select_fixes
from woodpecker.stores.base import FixPlanStore
from woodpecker.stores.helpers import create_fix_plan_store


@dataclass(frozen=True)
class RunContext:
    """Resolved execution context shared by `check` and `fix`.

    Precedence rules:
    - explicit CLI arguments override plan/store-derived values
    - explicit `--plan` overrides store lookup
    - `--plan-store` is an optional fallback source
    - with no plan/store source, direct registry selection is used
    """

    inputs: list[DataInput]
    fixes: list[Any]
    selected_plans: list[FixPlan]
    resolved_dataset: str | None
    resolved_categories: tuple[str, ...]
    resolved_codes: tuple[str, ...]
    resolved_fix_options: dict[str, dict[str, Any]]
    resolved_output_format: str
    source: Literal["direct", "plan", "store"]


def normalize_ordered_codes(codes: Sequence[str]) -> tuple[str, ...]:
    """Normalize and deduplicate fix codes while preserving order."""

    out: list[str] = []
    seen: set[str] = set()
    for raw in codes:
        code = str(raw).strip().upper()
        if not code or code in seen:
            continue
        out.append(code)
        seen.add(code)
    return tuple(out)


def _plan_key(plan: FixPlan) -> str:
    return plan.id or json.dumps(plan.to_dict(), sort_keys=True)


def _finalize_matching_plans(
    plans: Iterable[FixPlan],
    *,
    plan_id: str | None,
    not_found_message: str,
    multiple_message_prefix: str,
) -> list[FixPlan]:
    """Deduplicate matched plans, apply optional id filter, and enforce uniqueness."""

    unique: dict[str, FixPlan] = {}
    for plan in plans:
        unique[_plan_key(plan)] = plan

    matches = list(unique.values())
    if plan_id:
        requested = plan_id.strip()
        matches = [plan for plan in matches if plan.id == requested]
        if not matches:
            raise ValueError(not_found_message.format(plan_id=requested))

    if not matches:
        return []
    if len(matches) > 1:
        plan_ids = [plan.id for plan in matches if plan.id]
        label = ", ".join(plan_ids) if plan_ids else f"{len(matches)} unnamed plans"
        raise ValueError(multiple_message_prefix + label)
    return matches


def _iter_store_matches(inputs: Sequence[DataInput], store: FixPlanStore) -> list[FixPlan]:
    """Collect plans returned by store lookup across all normalized inputs."""

    out: list[FixPlan] = []
    for data_input in inputs:
        dataset = data_input.load()
        try:
            out.extend(store.lookup(dataset, path=data_input.reference))
        finally:
            close = getattr(dataset, "close", None)
            if callable(close):
                close()
    return out


def select_matching_store_plans(
    *,
    store: FixPlanStore,
    inputs: Sequence[DataInput],
    plan_id: str | None,
) -> list[FixPlan]:
    """Select one matching plan from store lookups with clear ambiguity handling."""

    return _finalize_matching_plans(
        _iter_store_matches(inputs, store),
        plan_id=plan_id,
        not_found_message="No matching stored fix plan found for --plan-id '{plan_id}'.",
        multiple_message_prefix=(
            "Multiple matching stored fix plans found; specify --plan-id to choose one: "
        ),
    )


def _iter_document_matches(inputs: Sequence[DataInput], plans: Sequence[FixPlan]) -> list[FixPlan]:
    """Collect plans from a document that match any normalized input."""

    out: list[FixPlan] = []
    for data_input in inputs:
        dataset = data_input.load()
        try:
            for plan in plans:
                if plan_matches_dataset(plan, dataset, path=data_input.reference):
                    out.append(plan)
        finally:
            close = getattr(dataset, "close", None)
            if callable(close):
                close()
    return out


def select_matching_document_plans(
    *,
    plans: Sequence[FixPlan],
    inputs: Sequence[DataInput],
    plan_id: str | None,
) -> list[FixPlan]:
    """Select one matching plan from a FixPlanDocument with clear ambiguity handling."""

    return _finalize_matching_plans(
        _iter_document_matches(inputs, plans),
        plan_id=plan_id,
        not_found_message="No matching plan found for --plan-id '{plan_id}'.",
        multiple_message_prefix=(
            "Multiple matching plans found in plan document; specify --plan-id to choose one: "
        ),
    )


def extract_plan_codes_and_options(
    plan: FixPlan,
) -> tuple[tuple[str, ...], dict[str, dict[str, Any]]]:
    """Extract ordered fix codes and per-code options from a FixPlan."""

    codes = tuple(ref.id for ref in plan.fixes)
    options = {ref.id: dict(ref.options) for ref in plan.fixes}
    return codes, options


def resolve_plan_source(
    *,
    inputs: Sequence[DataInput],
    plan_path: Path | None,
    store_type: str | None,
    store_path: Path | None,
    plan_id: str | None,
) -> tuple[
    Literal["direct", "plan", "store"],
    list[FixPlan],
    tuple[str, ...],
    dict[str, dict[str, Any]],
]:
    """Resolve plan source with explicit precedence: plan file > store > direct.

    Returns source marker, selected plans, resolved codes, and resolved fix options.
    """

    if plan_path is None and plan_id and store_type is None and store_path is None:
        raise ValueError("--plan-id requires --plan-store and --plan-store-path.")

    if plan_path is not None:
        document = load_fix_plan_document(plan_path)
        plans = select_matching_document_plans(plans=document.plans, inputs=inputs, plan_id=plan_id)
        if not plans:
            raise ValueError("No matching plans found in the plan document for selected inputs.")
        selected = plans[0]
        codes, fix_options = extract_plan_codes_and_options(selected)
        return "plan", [selected], codes, fix_options

    store = create_fix_plan_store(store_type, store_path)
    if store is None:
        return "direct", [], (), {}

    plans = select_matching_store_plans(store=store, inputs=inputs, plan_id=plan_id)
    if not plans:
        return "store", [], (), {}

    selected = plans[0]
    codes, fix_options = extract_plan_codes_and_options(selected)
    return "store", [selected], codes, fix_options


def resolve_target_paths(paths: tuple[Path, ...]) -> list[Path]:
    """Resolve CLI path arguments to execution inputs."""

    if paths:
        return list(paths)
    return [Path.cwd()]


def resolve_run_context(
    *,
    paths: tuple[Path, ...],
    plan_path: Path | None,
    store_type: str | None,
    store_path: Path | None,
    plan_id: str | None,
    dataset: str | None,
    categories: tuple[str, ...],
    codes: tuple[str, ...],
    output_format: str,
) -> RunContext:
    """Resolve inputs and fix selection for check/fix commands.

    Precedence:
    - plan file (`--plan`) first
    - store lookup fallback (`--plan-store`, `--plan-store-path`)
    - direct selection otherwise
    - explicit CLI filters (`--dataset`, `--category`, `--select`) override
      plan/store-derived defaults
    """

    target_paths = resolve_target_paths(paths)
    inputs = normalize_inputs(target_paths)

    source, selected_plans, source_codes, source_fix_options = resolve_plan_source(
        inputs=inputs,
        plan_path=plan_path,
        store_type=store_type,
        store_path=store_path,
        plan_id=plan_id,
    )

    cli_codes = normalize_ordered_codes(codes)
    resolved_codes = cli_codes or source_codes
    resolved_ordered_codes = resolved_codes
    resolved_dataset = dataset
    resolved_categories = categories
    resolved_output_format = output_format
    resolved_fix_options = dict(source_fix_options)

    if source == "store" and not selected_plans and not resolved_codes:
        raise ValueError("No matching fix plans found in the plan store for selected inputs.")

    fixes = select_fixes(
        dataset=resolved_dataset,
        categories=resolved_categories,
        codes=resolved_codes,
        strict_codes=True,
        fix_options=resolved_fix_options,
        ordered_codes=resolved_ordered_codes,
    )

    return RunContext(
        inputs=inputs,
        fixes=fixes,
        selected_plans=selected_plans,
        resolved_dataset=resolved_dataset,
        resolved_categories=tuple(resolved_categories),
        resolved_codes=tuple(resolved_codes),
        resolved_fix_options=resolved_fix_options,
        resolved_output_format=resolved_output_format,
        source=source,
    )


def resolve_load_source_plans(
    *,
    from_plan: Path | None,
    from_store_type: str | None,
    from_store_path: Path | None,
    plan_id: str | None,
) -> list[FixPlan]:
    """Resolve source plans for load-plans command."""

    if (from_store_type is None) != (from_store_path is None):
        raise ValueError("--from-store and --from-store-path must be provided together.")

    source_modes = int(from_plan is not None) + int(from_store_type is not None)
    if source_modes != 1:
        raise ValueError(
            "Provide exactly one source: --from-plan or (--from-store and --from-store-path)."
        )

    if from_plan is not None:
        plans = list(load_fix_plan_document(from_plan).plans)
    else:
        source_store = create_fix_plan_store(from_store_type, from_store_path)
        if source_store is None:  # pragma: no cover - guarded above
            raise ValueError("Invalid source store configuration.")
        plans = list(source_store.list_plans())

    if plan_id:
        requested = plan_id.strip()
        plans = [plan for plan in plans if plan.id == requested]
        if not plans:
            raise ValueError(f"No plans found for --plan-id '{requested}' in selected source.")

    if not plans:
        raise ValueError("No plans found in selected source.")

    return plans
