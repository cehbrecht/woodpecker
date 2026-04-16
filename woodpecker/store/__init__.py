"""Fix plan store package with optional backends."""

from .base import FixPlanStore
from .duckdb_store import DuckDBFixPlanStore
from .json_store import JsonFixPlanStore
from .matcher import plan_matches_dataset
from .models import DatasetMatcher, FixPlan, FixRef

__all__ = [
    "FixRef",
    "DatasetMatcher",
    "FixPlan",
    "FixPlanStore",
    "plan_matches_dataset",
    "JsonFixPlanStore",
    "DuckDBFixPlanStore",
]
