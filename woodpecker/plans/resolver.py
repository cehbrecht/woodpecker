from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, Sequence

from woodpecker.execution import select_fixes
from woodpecker.io import DataInput, normalize_inputs
from woodpecker.plans.models import FixPlan
from woodpecker.stores.base import FixPlanStore
from woodpecker.stores.helpers import create_fix_plan_store


@dataclass(frozen=True)
class RunContext:
    """Resolved execution context shared by `check` and `fix`.

    Precedence rules:
    - explicit CLI arguments override plan/store-derived values
    - when `--plan` is set, plans are loaded through selected `--store`
    - with no plan/store source, direct registry selection is used
    """

    inputs: list[DataInput]
    fixes: list[Any]
    selected_plans: list[FixPlan]
    resolved_dataset: str | None
    resolved_categories: tuple[str, ...]
    resolved_identifiers: tuple[str, ...]
    resolved_fix_options: dict[str, dict[str, Any]]
    resolved_output_format: str
    source: Literal["direct", "store"]


def normalize_ordered_identifiers(identifiers: Sequence[str]) -> tuple[str, ...]:
    """Normalize and deduplicate fix identifiers while preserving order."""

    out: list[str] = []
    seen: set[str] = set()
    for raw in identifiers:
        identifier = str(raw).strip()
        if not identifier or identifier in seen:
            continue
        out.append(identifier)
        seen.add(identifier)
    return tuple(out)


def _plan_key(plan: FixPlan) -> str:
    return plan.id or json.dumps(plan.model_dump(), sort_keys=True)


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
        not_found_message="No matching plan found for --plan-id '{plan_id}'.",
        multiple_message_prefix="Multiple matching fix plans found; specify --plan-id to choose one: ",
    )


def resolve_plan_source(
    *,
    inputs: Sequence[DataInput],
    store_type: str,
    plan_location: Path | None,
    plan_id: str | None,
) -> tuple[
    Literal["direct", "store"],
    list[FixPlan],
    tuple[str, ...],
    dict[str, dict[str, Any]],
]:
    """Resolve plan selection through FixPlanStore with direct-mode fallback.

    Returns source marker, selected plans, resolved identifiers, and resolved fix options.
    """

    if plan_location is None:
        if plan_id:
            raise ValueError("--plan-id requires --plan.")
        return "direct", [], (), {}

    store = create_fix_plan_store(store_type, plan_location)
    plans = select_matching_store_plans(store=store, inputs=inputs, plan_id=plan_id)
    if not plans:
        raise ValueError("No matching fix plans found in selected store for selected inputs.")

    selected = plans[0]
    identifiers, fix_options = selected.step_identifiers_and_options()
    return "store", [selected], identifiers, fix_options


def resolve_target_paths(paths: tuple[Path, ...]) -> list[Path]:
    """Resolve CLI path arguments to execution inputs."""

    if paths:
        return list(paths)
    return [Path.cwd()]


def resolve_selection_inputs(
    *,
    cli_identifiers: Sequence[str],
    source_identifiers: tuple[str, ...],
    source_fix_options: dict[str, dict[str, Any]],
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, dict[str, Any]]]:
    """Resolve identifier/option precedence between CLI and plan/store defaults."""

    normalized_cli_identifiers = normalize_ordered_identifiers(cli_identifiers)
    resolved_identifiers = normalized_cli_identifiers or source_identifiers
    resolved_ordered_identifiers = resolved_identifiers
    resolved_fix_options = {key: dict(value) for key, value in source_fix_options.items()}
    return resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options


def resolve_run_context(
    *,
    paths: tuple[Path, ...],
    store_type: str,
    plan_location: Path | None,
    plan_id: str | None,
    dataset: str | None,
    categories: tuple[str, ...],
    identifiers: tuple[str, ...],
    output_format: str,
) -> RunContext:
    """Resolve inputs and fix selection for check/fix commands.

    Precedence:
        - store lookup when `--plan` is provided
        - direct selection otherwise

    - explicit CLI filters (`--dataset`, `--category`, `--select`) override
      store-derived defaults
    """

    target_paths = resolve_target_paths(paths)
    inputs = normalize_inputs(target_paths)

    source, selected_plans, source_identifiers, source_fix_options = resolve_plan_source(
        inputs=inputs,
        store_type=store_type,
        plan_location=plan_location,
        plan_id=plan_id,
    )

    resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options = (
        resolve_selection_inputs(
            cli_identifiers=identifiers,
            source_identifiers=source_identifiers,
            source_fix_options=source_fix_options,
        )
    )
    resolved_dataset = dataset
    resolved_categories = categories
    resolved_output_format = output_format

    fixes = select_fixes(
        dataset=resolved_dataset,
        categories=resolved_categories,
        identifiers=resolved_identifiers,
        strict_identifiers=True,
        fix_options=resolved_fix_options,
        ordered_identifiers=resolved_ordered_identifiers,
    )

    return RunContext(
        inputs=inputs,
        fixes=fixes,
        selected_plans=selected_plans,
        resolved_dataset=resolved_dataset,
        resolved_categories=tuple(resolved_categories),
        resolved_identifiers=tuple(resolved_identifiers),
        resolved_fix_options=resolved_fix_options,
        resolved_output_format=resolved_output_format,
        source=source,
    )


def resolve_load_source_plans(
    *,
    from_plan: Path | None,
    from_store_type: str | None,
    plan_id: str | None,
) -> list[FixPlan]:
    """Resolve source plans for load-plans command."""

    if from_plan is None:
        raise ValueError("Provide --from-plan as the source store location.")

    source_store_type = from_store_type or "json"
    source_store = create_fix_plan_store(source_store_type, from_plan)
    plans = list(source_store.list_plans())

    if plan_id:
        requested = plan_id.strip()
        plans = [plan for plan in plans if plan.id == requested]
        if not plans:
            raise ValueError(f"No plans found for --plan-id '{requested}' in selected source.")

    if not plans:
        raise ValueError("No plans found in selected source store.")

    return plans
