from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..plans.matcher import plan_matches_dataset
from ..plans.models import FixPlan
from .base import FixPlanStore
from .index import FixPlanIndex


class JsonFixPlanStore(FixPlanStore):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _read_raw(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        payload = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        if isinstance(payload, dict):
            plans = payload.get("plans", [])
        else:
            plans = payload

        if not isinstance(plans, list):
            raise ValueError(
                "JSON fix-plan store file must contain a list or {'plans': [...]} payload"
            )
        return [item for item in plans if isinstance(item, dict)]

    def _write_raw(self, plans: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"schema_version": 1, "plans": plans}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def list_plans(self) -> list[FixPlan]:
        return [FixPlan.from_dict(item) for item in self._read_raw()]

    def save_plan(self, plan: FixPlan) -> None:
        plans = self._read_raw()
        target_canonical_id = FixPlanIndex.canonical_plan_id(plan)
        replaced = False
        for idx, existing in enumerate(plans):
            existing_plan = FixPlan.from_dict(existing)
            if FixPlanIndex.canonical_plan_id(existing_plan) == target_canonical_id:
                plans[idx] = plan.to_dict()
                replaced = True
                break
        if not replaced:
            plans.append(plan.to_dict())
        self._write_raw(plans)

    def lookup(self, dataset: Any, path: str | None = None) -> list[FixPlan]:
        return [
            plan for plan in self.list_plans() if plan_matches_dataset(plan, dataset, path=path)
        ]
