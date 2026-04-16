"""Fix plan models, matching, and execution runner."""

from .io import SUPPORTED_EXTENSIONS, load_fix_plan, load_fix_plan_spec
from .matcher import plan_matches_dataset
from .models import DatasetMatcher, FixPlan, FixRef, parse_fix_ref
from .runner import apply_fix_plan, run_check, run_fix, select_fixes
from .spec import DatasetFixPlan, FixPlanResolution, FixPlanSpec, PlanStep

__all__ = [
    "FixRef",
    "DatasetMatcher",
    "FixPlan",
    "PlanStep",
    "DatasetFixPlan",
    "FixPlanResolution",
    "FixPlanSpec",
    "parse_fix_ref",
    "SUPPORTED_EXTENSIONS",
    "load_fix_plan",
    "load_fix_plan_spec",
    "plan_matches_dataset",
    "apply_fix_plan",
    "select_fixes",
    "run_check",
    "run_fix",
]
