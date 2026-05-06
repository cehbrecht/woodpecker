from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..plans.matcher import plan_matches_dataset
from ..plans.models import DatasetMatcher, FixPlan, FixRef
from .base import FixPlanStore
from .index import FixPlanIndex


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
                "DuckDBFixPlanStore requires optional dependency 'duckdb'. Install with: pip install duckdb (or pip install 'woodpecker[full]')"
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
                    aliases_json TEXT,
                    description TEXT,
                    match_json TEXT,
                    steps_json TEXT
                )
                """
            )
            con.execute("ALTER TABLE fix_plans ADD COLUMN IF NOT EXISTS aliases_json TEXT")

    def list_plans(self) -> list[FixPlan]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT id, aliases_json, description, match_json, steps_json FROM fix_plans ORDER BY id"
            ).fetchall()

        plans: list[FixPlan] = []
        for plan_id, aliases_json, description, match_json, steps_json in rows:
            aliases_payload = json.loads(aliases_json) if aliases_json else []
            match_payload = json.loads(match_json) if match_json else None
            steps_payload = json.loads(steps_json) if steps_json else []
            plans.append(
                FixPlan(
                    id=str(plan_id),
                    aliases=list(aliases_payload) if isinstance(aliases_payload, list) else [],
                    description=str(description or ""),
                    match=DatasetMatcher.model_validate(match_payload)
                    if isinstance(match_payload, dict)
                    else None,
                    steps=[FixRef.model_validate(item) for item in steps_payload],
                )
            )
        return plans

    def save_plan(self, plan: FixPlan) -> None:
        aliases_json = json.dumps(list(plan.aliases))
        match_json = json.dumps(plan.match.model_dump()) if plan.match is not None else None
        steps_json = json.dumps([item.model_dump() for item in plan.steps])
        plan_id = FixPlanIndex.plan_id(plan)

        with self._connect() as con:
            con.execute(
                """
                INSERT OR REPLACE INTO fix_plans (id, aliases_json, description, match_json, steps_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                [plan_id, aliases_json, plan.description, match_json, steps_json],
            )

    @staticmethod
    def _parse_matcher(match_json: str | None) -> DatasetMatcher | None:
        match_payload = json.loads(match_json) if match_json else None
        return (
            DatasetMatcher.model_validate(match_payload)
            if isinstance(match_payload, dict)
            else None
        )

    @staticmethod
    def _parse_steps(steps_json: str | None) -> list[FixRef]:
        steps_payload = json.loads(steps_json) if steps_json else []
        return [FixRef.model_validate(item) for item in steps_payload]

    def _candidate_query(self, dataset: Any) -> tuple[str, list[Any]]:
        """Build a coarse SQL prefilter; exact plan matching is done in Python."""

        sql = "SELECT id, aliases_json, description, match_json, steps_json FROM fix_plans"
        dataset_attrs = getattr(dataset, "attrs", None)
        if not isinstance(dataset_attrs, dict):
            dataset_attrs = dict(dataset_attrs or {})

        clauses: list[str] = []
        params: list[Any] = []
        for key, value in dataset_attrs.items():
            key_text = str(key)
            clauses.append(
                "("
                "match_json IS NULL "
                "OR json_extract_string(CAST(match_json AS JSON), '$.attrs."
                + key_text
                + "') IS NULL "
                "OR json_extract_string(CAST(match_json AS JSON), '$.attrs." + key_text + "') = ?"
                ")"
            )
            params.append(value)

        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id"
        return sql, params

    def lookup(self, dataset: Any, path: str | None = None) -> list[FixPlan]:
        sql, params = self._candidate_query(dataset)
        with self._connect() as con:
            rows = con.execute(sql, params).fetchall()

        matched: list[FixPlan] = []
        for plan_id, aliases_json, description, match_json, steps_json in rows:
            aliases_payload = json.loads(aliases_json) if aliases_json else []
            matcher = self._parse_matcher(match_json)
            candidate = FixPlan(
                id=str(plan_id),
                aliases=list(aliases_payload) if isinstance(aliases_payload, list) else [],
                description=str(description or ""),
                match=matcher,
                steps=[],
            )
            if not plan_matches_dataset(candidate, dataset, path=path):
                continue

            matched.append(
                FixPlan(
                    id=candidate.id,
                    aliases=candidate.aliases,
                    description=candidate.description,
                    match=matcher,
                    steps=self._parse_steps(steps_json),
                )
            )

        return matched
