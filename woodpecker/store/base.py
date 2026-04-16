from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import FixPlan


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
