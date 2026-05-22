from __future__ import annotations

from typing import Any, Iterable

from ..fix_plans.matcher import plan_matches_dataset
from ..fix_plans.models import FixPlan
from .base import FixPlanStore


class StaticFixPlanStore(FixPlanStore):
    """Read-only FixPlanStore backed by an in-memory plan list."""

    def __init__(self, plans: Iterable[FixPlan]):
        self._plans = list(plans)

    def list_plans(self) -> list[FixPlan]:
        return list(self._plans)

    def lookup(self, dataset: Any, path: str | None = None) -> list[FixPlan]:
        return [plan for plan in self._plans if plan_matches_dataset(plan, dataset, path=path)]

    def save_plan(self, plan: FixPlan) -> None:
        _ = plan
        raise NotImplementedError("StaticFixPlanStore is read-only.")
