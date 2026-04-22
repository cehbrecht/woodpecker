"""Fix plan models, matching, and execution runner."""

from .io import SUPPORTED_EXTENSIONS, load_fix_plan, load_fix_plan_document
from .matcher import plan_matches_dataset
from .models import DatasetMatcher, FixPlan, FixPlanDocument, FixRef, Link, parse_fix_ref
from .runner import apply_fix_plan, run_check, run_fix, select_fixes

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
