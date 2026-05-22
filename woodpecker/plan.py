from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

# Importing woodpecker.fixes registers built-in fixes before API selection runs.
import woodpecker.fixes  # noqa: F401
from woodpecker.commands import execute_check, execute_check_plan, execute_fix, execute_fix_plan
from woodpecker.fix_plans.models import FixPlan
from woodpecker.results import CheckResult, FixResult
from woodpecker.stores.helpers import create_fix_plan_store


@dataclass(frozen=True)
class PlanSelector:
    """Plan source selector for the public plan API."""

    plan: str | Path | None
    plan_id: str | None = None
    store_type: str = "json"


PlanSource = str | Path | None | PlanSelector | FixPlan


def auto(plan_id: str | None = None) -> PlanSelector:
    """Select generated one-step plans from registered fixes."""
    return PlanSelector(plan=None, plan_id=plan_id, store_type="auto")


def catalog(plan_id: str | None = None, plan: str | Path | None = None) -> PlanSelector:
    """Select plans from discovered package, user, system, and optional explicit locations."""
    return PlanSelector(plan=plan, plan_id=plan_id, store_type="catalog")


discovered = catalog


def get(plan_id: str, plan: str | Path | None = None) -> FixPlan:
    """Load a discovered fix plan by id or alias."""
    return create_fix_plan_store("catalog", Path(plan) if plan is not None else None).get_plan(
        plan_id
    )


def list_plans(plan: str | Path | None = None) -> list[FixPlan]:
    """List discovered fix plans."""
    return create_fix_plan_store("catalog", Path(plan) if plan is not None else None).list_plans()


def _normalize_fixes(fixes: str | Sequence[str] | None) -> tuple[str, ...]:
    if fixes is None:
        return ()
    if isinstance(fixes, str):
        return (fixes,)
    return tuple(str(item) for item in fixes)


def _resolve_plan_source(
    plan: PlanSource,
    *,
    plan_id: str | None,
    store_type: str,
) -> tuple[str | Path | None, str | None, str]:
    if isinstance(plan, PlanSelector):
        return plan.plan, plan_id or plan.plan_id, plan.store_type
    return plan, plan_id, store_type


def _resolve_fix_plan_selection(
    plan: FixPlan,
    fixes: str | Sequence[str] | None,
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, dict[str, Any]]]:
    source_identifiers, source_fix_options = plan.step_identifiers_and_options()
    resolved_identifiers = _normalize_fixes(fixes) or source_identifiers
    return resolved_identifiers, resolved_identifiers, dict(source_fix_options)


def check(
    inputs: Any,
    plan: PlanSource,
    *,
    plan_id: str | None = None,
    store_type: str = "json",
    dataset: str | None = None,
    categories: Sequence[str] = (),
    fixes: str | Sequence[str] | None = None,
    strict_io: bool = False,
) -> CheckResult:
    """Check inputs using fixes selected from a fix plan."""
    if isinstance(plan, FixPlan):
        resolved_identifiers, ordered_identifiers, fix_options = _resolve_fix_plan_selection(
            plan,
            fixes,
        )
        return CheckResult(
            findings=tuple(
                execute_check(
                    inputs,
                    dataset=dataset,
                    categories=categories,
                    identifiers=resolved_identifiers,
                    fix_options=fix_options,
                    ordered_identifiers=ordered_identifiers,
                    strict_io=strict_io,
                )
            )
        )

    plan_location, resolved_plan_id, resolved_store_type = _resolve_plan_source(
        plan,
        plan_id=plan_id,
        store_type=store_type,
    )
    return CheckResult(
        findings=tuple(
            execute_check_plan(
                plan_location,
                inputs=inputs,
                dataset=dataset,
                categories=categories,
                identifiers=_normalize_fixes(fixes),
                plan_id=resolved_plan_id,
                store_type=resolved_store_type,
                strict_io=strict_io,
            )
        )
    )


def fix(
    inputs: Any,
    plan: PlanSource,
    *,
    plan_id: str | None = None,
    store_type: str = "json",
    dataset: str | None = None,
    categories: Sequence[str] = (),
    fixes: str | Sequence[str] | None = None,
    dry_run: bool = True,
    output_format: str = "auto",
    strict_io: bool = False,
) -> FixResult:
    """Apply fixes selected from a fix plan."""
    if isinstance(plan, FixPlan):
        resolved_identifiers, ordered_identifiers, fix_options = _resolve_fix_plan_selection(
            plan,
            fixes,
        )
        return FixResult(
            stats=execute_fix(
                inputs,
                dataset=dataset,
                categories=categories,
                identifiers=resolved_identifiers,
                dry_run=dry_run,
                output_format=output_format,
                fix_options=fix_options,
                ordered_identifiers=ordered_identifiers,
                strict_io=strict_io,
            )
        )

    plan_location, resolved_plan_id, resolved_store_type = _resolve_plan_source(
        plan,
        plan_id=plan_id,
        store_type=store_type,
    )
    return FixResult(
        stats=execute_fix_plan(
            plan_location,
            inputs=inputs,
            dataset=dataset,
            categories=categories,
            identifiers=_normalize_fixes(fixes),
            dry_run=dry_run,
            output_format=output_format,
            plan_id=resolved_plan_id,
            store_type=resolved_store_type,
            strict_io=strict_io,
        )
    )
