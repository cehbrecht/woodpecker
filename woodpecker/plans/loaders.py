from __future__ import annotations

from pathlib import Path

from woodpecker.plans.models import FixPlan, FixPlanDocument
from woodpecker.stores.json_store import JsonFixPlanStore

SUPPORTED_EXTENSIONS = {".json", ".yaml", ".yml"}


def load_fix_plan(path: str | Path) -> FixPlan:
    plans = JsonFixPlanStore(path).list_plans()
    if not plans:
        raise ValueError("No plans found in fix plan file")
    return plans[0]


def load_fix_plan_document(path: str | Path) -> FixPlanDocument:
    return FixPlanDocument(plans=JsonFixPlanStore(path).list_plans())
