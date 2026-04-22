from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..plans.models import FixPlan
from .index import FixPlanIndex


class FixPlanStore(ABC):
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
        return FixPlanIndex(self.list_plans()).get(identifier)
