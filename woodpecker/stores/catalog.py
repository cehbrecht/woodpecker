from __future__ import annotations

from typing import Any, Iterable

from ..plans.models import FixPlan
from .base import FixPlanStore
from .index import FixPlanIndex


class FixPlanCatalog(FixPlanStore):
    """Aggregate multiple fix-plan sources into one read-only query surface."""

    def __init__(self, sources: Iterable[FixPlanStore]):
        self.sources = list(sources)

    @staticmethod
    def _deduplicate(plans: Iterable[FixPlan]) -> list[FixPlan]:
        out: list[FixPlan] = []
        positions: dict[str, int] = {}
        for plan in plans:
            plan_id = FixPlanIndex.plan_id(plan)
            if plan_id in positions:
                idx = positions[plan_id]
                existing = out[idx]
                aliases = list(existing.aliases)
                for alias in plan.aliases:
                    if alias not in aliases:
                        aliases.append(alias)
                payload = existing.model_dump()
                payload["aliases"] = aliases
                out[idx] = FixPlan.model_validate(payload)
                continue
            positions[plan_id] = len(out)
            out.append(plan)
        return out

    def list_plans(self) -> list[FixPlan]:
        plans: list[FixPlan] = []
        for source in self.sources:
            plans.extend(source.list_plans())
        return self._deduplicate(plans)

    def lookup(self, dataset: Any, path: str | None = None) -> list[FixPlan]:
        plans: list[FixPlan] = []
        for source in self.sources:
            plans.extend(source.lookup(dataset, path=path))
        return self._deduplicate(plans)

    def get_plan(self, identifier: str) -> FixPlan:
        return FixPlanIndex(self.list_plans()).get(identifier)

    def save_plan(self, plan: FixPlan) -> None:
        _ = plan
        raise NotImplementedError("FixPlanCatalog is read-only.")
