"""Woodpecker: lightweight fix catalog + scaffolding for climate dataset fixes."""

from .api import check, check_plan, fix, fix_plan
from .plans import (
    FixPlan,
    FixPlanDocument,
    FixRef,
    load_fix_plan,
    load_fix_plan_document,
)
from .results import CheckResult, FixResult
from .runner import apply_fix_plan
from .stores import AutoFixPlanStore, FixPlanCatalog, JsonFixPlanStore

__all__ = [
    "fixes",
    "check",
    "fix",
    "check_plan",
    "fix_plan",
    "CheckResult",
    "FixResult",
    "FixRef",
    "FixPlan",
    "FixPlanDocument",
    "AutoFixPlanStore",
    "FixPlanCatalog",
    "JsonFixPlanStore",
    "apply_fix_plan",
    "load_fix_plan",
    "load_fix_plan_document",
]
