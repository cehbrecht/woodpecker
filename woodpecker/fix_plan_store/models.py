from __future__ import annotations

import json
from dataclasses import dataclass, field
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
