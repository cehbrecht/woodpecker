from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..plans.matcher import plan_matches_dataset
from ..plans.models import DatasetMatcher, FixPlan, FixRef
from .base import FixPlanStore


class DuckDBFixPlanStore(FixPlanStore):
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._ensure_schema()

    @staticmethod
    def _import_duckdb() -> Any:
        try:
            import duckdb
        except ImportError as exc:  # pragma: no cover - exercised in environments without duckdb
            raise RuntimeError(
                "DuckDBFixPlanStore requires optional dependency 'duckdb'. Install with: pip install duckdb"
            ) from exc
        return duckdb

    def _connect(self) -> Any:
        duckdb = self._import_duckdb()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return duckdb.connect(str(self.path))

    def _ensure_schema(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS fix_plans (
                    id TEXT PRIMARY KEY,
                    description TEXT,
                    match_json TEXT,
                    fixes_json TEXT
                )
                """
            )

    def list_plans(self) -> list[FixPlan]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT id, description, match_json, fixes_json FROM fix_plans ORDER BY id"
            ).fetchall()

        plans: list[FixPlan] = []
        for plan_id, description, match_json, fixes_json in rows:
            match_payload = json.loads(match_json) if match_json else None
            fixes_payload = json.loads(fixes_json) if fixes_json else []
            plans.append(
                FixPlan(
                    id=str(plan_id),
                    description=str(description or ""),
                    match=DatasetMatcher.from_dict(match_payload)
                    if isinstance(match_payload, dict)
                    else None,
                    fixes=[FixRef.from_dict(item) for item in fixes_payload],
                )
            )
        return plans

    def save_plan(self, plan: FixPlan) -> None:
        match_json = json.dumps(plan.match.to_dict()) if plan.match is not None else None
        fixes_json = json.dumps([item.to_dict() for item in plan.fixes])

        with self._connect() as con:
            con.execute(
                """
                INSERT OR REPLACE INTO fix_plans (id, description, match_json, fixes_json)
                VALUES (?, ?, ?, ?)
                """,
                [plan.id, plan.description, match_json, fixes_json],
            )

    def lookup(self, dataset: Any, path: str | None = None) -> list[FixPlan]:
        return [plan for plan in self.list_plans() if plan_matches_dataset(plan, dataset, path=path)]
