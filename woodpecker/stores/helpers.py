from __future__ import annotations

from pathlib import Path

from .base import FixPlanStore
from .duckdb_store import DuckDBFixPlanStore
from .json_store import JsonFixPlanStore


def create_fix_plan_store(store_type: str, plan_location: Path | None) -> FixPlanStore:
    """Create a FixPlanStore backend for the selected store type and location."""

    if plan_location is None:
        raise ValueError("--plan is required when using a plan store backend.")

    if store_type == "json":
        return JsonFixPlanStore(plan_location)
    if store_type == "duckdb":
        return DuckDBFixPlanStore(plan_location)

    raise ValueError(f"Unsupported plan store type: {store_type}")
