from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..plans.models import FixPlan
from .index import FixPlanIndex


class FixPlanStore(ABC):
    """Abstract base for fix-plan storage backends.

    Backends must implement ``lookup``, ``list_plans``, and ``save_plan``.
    ``get_plan`` is provided for free via ``FixPlanIndex`` and does not need
    to be overridden unless the backend wants to optimize the hot path.
    """

    @abstractmethod
    def lookup(self, dataset: Any, path: str | None = None) -> list[FixPlan]:
        raise NotImplementedError

    @abstractmethod
    def list_plans(self) -> list[FixPlan]:
        raise NotImplementedError

    @abstractmethod
    def save_plan(self, plan: FixPlan) -> None:
        raise NotImplementedError

    def get_plan(self, identifier: str) -> FixPlan:
        # If this becomes a hot path, concrete stores can cache FixPlanIndex and
        # invalidate on save_plan(); keep base class behavior stateless and minimal.
        return FixPlanIndex(self.list_plans()).get(identifier)
