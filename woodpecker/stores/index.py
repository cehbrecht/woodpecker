from __future__ import annotations

from ..identifiers import IdentifierResolver
from ..plans.models import FixPlan


class FixPlanIndex:
    def __init__(self, plans: list[FixPlan]):
        self._plans = list(plans)
        self._plans_by_canonical_id = self._index_plans_by_canonical_id(self._plans)
        self._resolver = self._build_plan_identifier_resolver(self._plans_by_canonical_id)

    @staticmethod
    def canonical_plan_id(plan: FixPlan) -> str:
        if plan.identifier_set is not None:
            return plan.identifier_set.canonical_id
        return str(plan.id).strip().lower()

    @classmethod
    def _index_plans_by_canonical_id(cls, plans: list[FixPlan]) -> dict[str, FixPlan]:
        indexed: dict[str, FixPlan] = {}
        for plan in plans:
            canonical_id = cls.canonical_plan_id(plan)
            if not canonical_id:
                raise ValueError("Encountered plan with empty identifier.")
            if canonical_id in indexed:
                raise ValueError(f"Duplicate canonical plan id detected: {canonical_id}")
            indexed[canonical_id] = plan
        return indexed

    @staticmethod
    def _build_plan_identifier_resolver(
        plans_by_canonical_id: dict[str, FixPlan],
    ) -> IdentifierResolver:
        resolver = IdentifierResolver(
            index={canonical_id: canonical_id for canonical_id in plans_by_canonical_id}
        )
        for plan in plans_by_canonical_id.values():
            if plan.identifier_set is not None:
                resolver.register(plan.identifier_set)
        return resolver

    def get(self, identifier: str) -> FixPlan:
        try:
            canonical_id = self._resolver.resolve(identifier)
        except KeyError as exc:
            raise ValueError(f"Unknown plan identifier: {identifier}") from exc

        return self._plans_by_canonical_id[canonical_id]

    def list(self) -> list[FixPlan]:
        return list(self._plans)
