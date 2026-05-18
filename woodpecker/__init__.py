"""Woodpecker: lightweight fix catalog + scaffolding for climate dataset fixes."""

from .api import check, fix
from .fix_plans import (
    FixPlanDocument,
    FixRef,
    load_fix_plan,
    load_fix_plan_document,
)
from .results import CheckResult, FixResult
from .runner import apply_fix_plan
from .sources import Fixes, FixPlan
from .stores import AutoFixPlanStore, FixPlanCatalog, JsonFixPlanStore

__all__ = [
    "fixes",
    "check",
    "fix",
    "Fixes",
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
