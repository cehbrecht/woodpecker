from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


@dataclass
class FixRef:
    id: str
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.id = str(self.id).strip().upper()
        if not self.id:
            raise ValueError("FixRef.id must be a non-empty string")
        if not isinstance(self.options, dict):
            raise ValueError("FixRef.options must be a mapping/object")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "options": dict(self.options)}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FixRef:
        return cls(id=str(payload.get("id", "")), options=dict(payload.get("options", {}) or {}))


@dataclass
class DatasetMatcher:
    attrs: dict[str, Any] = field(default_factory=dict)
    path_patterns: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.attrs, dict):
            raise ValueError("DatasetMatcher.attrs must be a mapping/object")
        if not isinstance(self.path_patterns, list):
            raise ValueError("DatasetMatcher.path_patterns must be a list")
        self.path_patterns = [str(pattern) for pattern in self.path_patterns]

    def to_dict(self) -> dict[str, Any]:
        return {"attrs": dict(self.attrs), "path_patterns": list(self.path_patterns)}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DatasetMatcher:
        return cls(
            attrs=dict(payload.get("attrs", {}) or {}),
            path_patterns=list(payload.get("path_patterns", []) or []),
        )


@dataclass
class FixPlan:
    id: str
    description: str = ""
    match: DatasetMatcher | None = None
    fixes: list[FixRef] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.id = str(self.id).strip()
        if not self.id:
            raise ValueError("FixPlan.id must be a non-empty string")
        self.description = str(self.description)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "match": self.match.to_dict() if self.match is not None else None,
            "fixes": [fix.to_dict() for fix in self.fixes],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FixPlan:
        raw_match = payload.get("match")
        return cls(
            id=str(payload.get("id", "")),
            description=str(payload.get("description", "")),
            match=DatasetMatcher.from_dict(raw_match) if isinstance(raw_match, dict) else None,
            fixes=[FixRef.from_dict(item) for item in list(payload.get("fixes", []) or [])],
        )

    @classmethod
    def from_json(cls, payload: str) -> FixPlan:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("FixPlan JSON payload must decode to an object")
        return cls.from_dict(data)


def plan_matches_dataset(plan: FixPlan, dataset: Any, path: str | None = None) -> bool:
    matcher = plan.match
    if matcher is None:
        return True

    attrs_ok = True
    if matcher.attrs:
        dataset_attrs = getattr(dataset, "attrs", None)
        if not isinstance(dataset_attrs, dict):
            dataset_attrs = dict(dataset_attrs or {})
        attrs_ok = all(dataset_attrs.get(key) == value for key, value in matcher.attrs.items())

    path_ok = True
    if matcher.path_patterns:
        if path is None:
            path_ok = False
        else:
            path_text = str(path)
            path_ok = any(fnmatch(path_text, pattern) for pattern in matcher.path_patterns)

    return attrs_ok and path_ok


class FixPlanStore(ABC):
    @abstractmethod
    def lookup(self, dataset: Any, path: str | None = None) -> list[FixPlan]:
        raise NotImplementedError

    @abstractmethod
    def list_plans(self) -> list[FixPlan]:
        raise NotImplementedError

    @abstractmethod
    def save_plan(self, plan: FixPlan) -> None:
        raise NotImplementedError


class JsonFixPlanStore(FixPlanStore):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _read_raw(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        payload = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        if isinstance(payload, dict):
            plans = payload.get("plans", [])
        else:
            plans = payload

        if not isinstance(plans, list):
            raise ValueError("JSON fix-plan store file must contain a list or {'plans': [...]} payload")
        return [item for item in plans if isinstance(item, dict)]

    def _write_raw(self, plans: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(plans, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def list_plans(self) -> list[FixPlan]:
        return [FixPlan.from_dict(item) for item in self._read_raw()]

    def save_plan(self, plan: FixPlan) -> None:
        plans = self._read_raw()
        replaced = False
        for idx, existing in enumerate(plans):
            if str(existing.get("id", "")).strip() == plan.id:
                plans[idx] = plan.to_dict()
                replaced = True
                break
        if not replaced:
            plans.append(plan.to_dict())
        self._write_raw(plans)

    def lookup(self, dataset: Any, path: str | None = None) -> list[FixPlan]:
        return [plan for plan in self.list_plans() if plan_matches_dataset(plan, dataset, path=path)]


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
