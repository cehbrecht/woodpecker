from __future__ import annotations

from typing import Any

from woodpecker.fixes.registry import FixRegistry
from woodpecker.identity import dataset_type_matches_declared, resolve_dataset_identity

from ..plans.models import FixPlan, FixRef
from .base import FixPlanStore


class AutoFixPlanStore(FixPlanStore):
    """Read-only store that exposes registered fixes as single-step plans."""

    @staticmethod
    def _plan_from_fix(fix: Any) -> FixPlan:
        fix_id = str(getattr(fix, "id", "") or "")
        name = str(getattr(fix, "name", "") or "")
        description = str(getattr(fix, "description", "") or "")
        aliases = list(getattr(fix, "aliases", []) or [])

        return FixPlan(
            id=fix_id,
            aliases=aliases,
            description=description or name,
            steps=[FixRef(id=fix_id)],
        )

    def list_plans(self) -> list[FixPlan]:
        return [self._plan_from_fix(fix) for fix in FixRegistry.discover()]

    def lookup(self, dataset: Any, path: str | None = None) -> list[FixPlan]:
        _ = path
        identity = resolve_dataset_identity(dataset)
        plans: list[FixPlan] = []

        for fix in FixRegistry.discover():
            if not dataset_type_matches_declared(
                getattr(fix, "dataset", None), identity.dataset_type
            ):
                continue
            if not fix.matches(dataset):
                continue
            plans.append(self._plan_from_fix(fix))

        return plans

    def save_plan(self, plan: FixPlan) -> None:
        _ = plan
        raise NotImplementedError("AutoFixPlanStore is read-only.")
