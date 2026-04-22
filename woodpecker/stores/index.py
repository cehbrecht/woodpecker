from __future__ import annotations

from ..identifiers import IdentifierResolver
from ..plans.models import FixPlan


class FixPlanIndex:
    """Index a collection of ``FixPlan`` objects for fast identifier-based retrieval.

    On construction, plans are keyed by their canonical id and an
    ``IdentifierResolver`` is built so plans can be looked up by canonical id,
    local id, or any declared alias.  Duplicate canonical ids raise immediately.
    """

    def __init__(self, plans: list[FixPlan]):
        self._plans = list(plans)
        self._plans_by_canonical_id = self._index_plans_by_canonical_id(self._plans)
        self._resolver = self._build_plan_identifier_resolver(self._plans_by_canonical_id)

    @staticmethod
    def canonical_plan_id(plan: FixPlan) -> str:
        """Return the canonical id for *plan*.

        When the plan carries a full ``IdentifierSet``, that canonical id is
        used.  Otherwise the normalized raw ``plan.id`` string is returned.
        """
        if plan.identifier_set is not None:
            return plan.identifier_set.canonical_id
        return str(plan.id).strip().lower()

    @classmethod
    def _index_plans_by_canonical_id(cls, plans: list[FixPlan]) -> dict[str, FixPlan]:
        """Build a canonical-id-keyed dict, raising on duplicate ids."""
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
        """Build a resolver seeded with every canonical id and alias in the index."""
        resolver = IdentifierResolver(
            index={canonical_id: canonical_id for canonical_id in plans_by_canonical_id}
        )
        for plan in plans_by_canonical_id.values():
            if plan.identifier_set is not None:
                resolver.register(plan.identifier_set)
        return resolver

    def get(self, identifier: str) -> FixPlan:
        """Return the plan matching *identifier* (canonical id, local id, or alias).

        Raises ``ValueError`` for unknown or ambiguous identifiers.
        """
        try:
            canonical_id = self._resolver.resolve(identifier)
        except KeyError as exc:
            raise ValueError(f"Unknown plan identifier: {identifier}") from exc

        return self._plans_by_canonical_id[canonical_id]

    def list(self) -> list[FixPlan]:
        """Return all plans in insertion order."""
        return list(self._plans)
