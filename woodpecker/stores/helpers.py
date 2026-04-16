from __future__ import annotations

from pathlib import Path

from .base import FixPlanStore
from .duckdb_store import DuckDBFixPlanStore
from .json_store import JsonFixPlanStore


def create_fix_plan_store(store_type: str | None, store_path: Path | None) -> FixPlanStore | None:
    """Create an optional FixPlanStore backend from CLI options.

    Returns None when both values are omitted. Raises ValueError for invalid or
    incomplete configuration.
    """

    if store_type is None and store_path is None:
        return None
    if store_type is None or store_path is None:
        raise ValueError("--plan-store and --plan-store-path must be provided together.")

    if store_type == "json":
        return JsonFixPlanStore(store_path)
    if store_type == "duckdb":
        return DuckDBFixPlanStore(store_path)

    raise ValueError(f"Unsupported plan store type: {store_type}")
