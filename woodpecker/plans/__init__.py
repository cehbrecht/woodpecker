"""Fix plan models, matching, and resolution helpers."""

from pathlib import Path

from ..execution import apply_fix_plan, run_check, run_fix, select_fixes
from ..stores.json_store import JsonFixPlanStore
from .matcher import plan_matches_dataset
from .models import DatasetMatcher, FixPlan, FixPlanDocument, FixRef, Link, parse_fix_ref

SUPPORTED_EXTENSIONS = {".json", ".yaml", ".yml"}


def load_fix_plan(path: str | Path) -> FixPlan:
    plans = JsonFixPlanStore(path).list_plans()
    if not plans:
        raise ValueError("No plans found in fix plan file")
    return plans[0]


def load_fix_plan_document(path: str | Path) -> FixPlanDocument:
    return FixPlanDocument(plans=JsonFixPlanStore(path).list_plans())


__all__ = [
    "Link",
    "FixRef",
    "DatasetMatcher",
    "FixPlan",
    "FixPlanDocument",
    "parse_fix_ref",
    "SUPPORTED_EXTENSIONS",
    "load_fix_plan",
    "load_fix_plan_document",
    "plan_matches_dataset",
    "apply_fix_plan",
    "select_fixes",
    "run_check",
    "run_fix",
]
