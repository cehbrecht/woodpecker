"""Fix plan store package with optional backends."""

from ..plans.matcher import plan_matches_dataset
from ..plans.models import DatasetMatcher, FixPlan, FixRef
from ..stores import DuckDBFixPlanStore, FixPlanStore, JsonFixPlanStore

__all__ = [
    "FixRef",
    "DatasetMatcher",
    "FixPlan",
    "FixPlanStore",
    "plan_matches_dataset",
    "JsonFixPlanStore",
    "DuckDBFixPlanStore",
]
