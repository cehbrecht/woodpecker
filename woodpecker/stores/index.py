from __future__ import annotations

from woodpecker.fixes.identifiers import IdentifierResolver

from ..plans.models import FixPlan


class FixPlanIndex:
    """Index a collection of ``FixPlan`` objects for fast identifier-based retrieval.

    On construction, plans are keyed by their id and an ``IdentifierResolver``
    is built so plans can be looked up by id, suffix, or any declared alias.
    Duplicate ids raise immediately.
    """

    def __init__(self, plans: list[FixPlan]):
        self._plans = list(plans)
        self._plans_by_id = self._index_plans_by_id(self._plans)
        self._resolver = self._build_plan_identifier_resolver(self._plans_by_id)

    @staticmethod
    def plan_id(plan: FixPlan) -> str:
        """Return normalized id for *plan*."""
        if plan.identifier_set is not None:
            return plan.identifier_set.id
        return str(plan.id).strip().lower()

    @classmethod
    def _index_plans_by_id(cls, plans: list[FixPlan]) -> dict[str, FixPlan]:
        """Build an id-keyed dict, raising on duplicate ids."""
        indexed: dict[str, FixPlan] = {}
        for plan in plans:
            plan_id = cls.plan_id(plan)
            if not plan_id:
                raise ValueError("Encountered plan with empty identifier.")
            if plan_id in indexed:
                raise ValueError(f"Duplicate plan id detected: {plan_id}")
            indexed[plan_id] = plan
        return indexed

    @staticmethod
    def _build_plan_identifier_resolver(
        plans_by_id: dict[str, FixPlan],
    ) -> IdentifierResolver:
        """Build a resolver seeded with every plan id and alias in the index."""
        resolver = IdentifierResolver(index={plan_id: plan_id for plan_id in plans_by_id})
        for plan in plans_by_id.values():
            if plan.identifier_set is not None:
                resolver.register(plan.identifier_set)
        return resolver

    def get(self, identifier: str) -> FixPlan:
        """Return the plan matching *identifier* (id, suffix, or alias).

        Raises ``ValueError`` for unknown or ambiguous identifiers.
        """
        try:
            resolved_id = self._resolver.resolve(identifier)
        except KeyError as exc:
            raise ValueError(f"Unknown plan identifier: {identifier}") from exc

        return self._plans_by_id[resolved_id]

    def list(self) -> list[FixPlan]:
        """Return all plans in insertion order."""
        return list(self._plans)
