from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from woodpecker.identifiers import IdentifierRules


@dataclass
class FixRef:
    id: str
    options: dict[str, Any] = field(default_factory=dict)
    links: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.id = IdentifierRules.normalize(self.id)
        if not self.id:
            raise ValueError("FixRef.id must be a non-empty string")
        if "." in self.id:
            IdentifierRules.validate_canonical_id("FixRef.id", self.id)
        else:
            IdentifierRules.validate_local_id("FixRef.id", self.id)
        if not isinstance(self.options, dict):
            raise ValueError("FixRef.options must be a mapping/object")
        if not isinstance(self.links, list):
            raise ValueError("FixRef.links must be a list")
        for item in self.links:
            if not isinstance(item, dict) or not item.get("rel") or not item.get("href"):
                raise ValueError("FixRef.links entries must contain rel and href")

    @property
    def id(self) -> str:
        """Backward-compatible alias for legacy code paths."""

        return self._id

    @id.setter
    def id(self, value: str) -> None:
        self._id = IdentifierRules.normalize(value)

    @property
    def fix(self) -> str:
        return self.id

    @fix.setter
    def fix(self, value: str) -> None:
        self.id = value

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"fix": self.id, "options": dict(self.options)}
        if self.links:
            payload["links"] = [dict(item) for item in self.links]
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> FixRef:
        return cls(
            id=str(payload.get("fix", payload.get("id", ""))),
            options=dict(payload.get("options", {}) or {}),
            links=[dict(item) for item in list(payload.get("links", []) or [])],
        )


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
    def from_dict(cls, payload: Mapping[str, Any]) -> DatasetMatcher:
        return cls(
            attrs=dict(payload.get("attrs", {}) or {}),
            path_patterns=list(payload.get("path_patterns", []) or []),
        )


def parse_fix_ref(item: Any) -> FixRef:
    if isinstance(item, str):
        return FixRef(id=item)
    if not isinstance(item, Mapping):
        raise ValueError("Each fix entry must be a string or object")
    fix_id = item.get("fix", item.get("id", ""))
    return FixRef(
        id=str(fix_id),
        options=dict(item.get("options", {}) or {}),
        links=[dict(link) for link in list(item.get("links", []) or [])],
    )


@dataclass
class FixPlan:
    id: str = ""
    local_id: str = ""
    namespace: str = ""
    description: str = ""
    match: DatasetMatcher | None = None
    fixes: list[FixRef] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.id = IdentifierRules.normalize(self.id)
        self.local_id = IdentifierRules.normalize(self.local_id) or self.id
        self.namespace = IdentifierRules.normalize(self.namespace)
        self.description = str(self.description)
        if not isinstance(self.links, list):
            raise ValueError("FixPlan.links must be a list")
        for item in self.links:
            if not isinstance(item, dict) or not item.get("rel") or not item.get("href"):
                raise ValueError("FixPlan.links entries must contain rel and href")

        if self.namespace and self.local_id:
            self.id = f"{self.namespace}.{self.local_id}"
        elif self.id and "." in self.id and not self.namespace:
            self.namespace, self.local_id = self.id.split(".", 1)

        # Keep canonical IDs as primary plan identity for fixes.
        self.fixes = [
            FixRef(id=self.resolve_fix_identifier(ref), options=ref.options, links=ref.links)
            for ref in self.fixes
        ]

    def resolve_fix_identifier(self, ref: FixRef) -> str:
        token = IdentifierRules.normalize(ref.fix)
        if not token:
            return token
        if "." in token:
            return token
        if self.namespace:
            return f"{self.namespace}.{token}"
        return token

    def to_dict(self) -> dict[str, Any]:
        fix_entries: list[dict[str, Any]] = []
        for fix in self.fixes:
            row: dict[str, Any] = {
                "fix": fix.id,
                "options": dict(fix.options),
            }
            if fix.links:
                row["links"] = [dict(item) for item in fix.links]
            fix_entries.append(row)

        payload: dict[str, Any] = {
            "id": self.id,
            "local_id": self.local_id,
            "description": self.description,
            "match": self.match.to_dict() if self.match is not None else None,
            "fixes": fix_entries,
        }
        if self.namespace:
            payload["namespace"] = self.namespace
        if self.links:
            payload["links"] = [dict(item) for item in self.links]
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> FixPlan:
        raw_match = payload.get("match")
        plan_id = str(payload.get("id", ""))
        namespace = str(payload.get("namespace", payload.get("prefix", "")))
        local_id = str(payload.get("local_id", ""))
        if plan_id and "." in plan_id and not namespace:
            namespace, local_id = plan_id.split(".", 1)
        if not local_id:
            local_id = str(payload.get("id", ""))
        return cls(
            id=plan_id,
            local_id=local_id,
            namespace=namespace,
            description=str(payload.get("description", "")),
            match=DatasetMatcher.from_dict(raw_match) if isinstance(raw_match, Mapping) else None,
            fixes=[parse_fix_ref(item) for item in list(payload.get("fixes", []) or [])],
            links=[dict(item) for item in list(payload.get("links", []) or [])],
        )

    @classmethod
    def from_json(cls, payload: str) -> FixPlan:
        data = json.loads(payload)
        if not isinstance(data, Mapping):
            raise ValueError("FixPlan JSON payload must decode to an object")
        return cls.from_dict(data)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> FixPlan:
        items = payload.get("fixes", [])
        if not isinstance(items, list):
            raise ValueError("FixPlan 'fixes' must be a list")
        return cls.from_dict(payload)


@dataclass
class FixPlanDocument:
    plans: list[FixPlan] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"plans": [plan.to_dict() for plan in self.plans]}

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> FixPlanDocument:
        raw_plans = payload.get("plans")
        if raw_plans is None:
            # Single-plan shorthand: treat top-level object as one FixPlan.
            return cls(plans=[FixPlan.from_mapping(payload)])
        if not isinstance(raw_plans, list):
            raise ValueError("FixPlanDocument 'plans' must be a list")
        return cls(
            plans=[FixPlan.from_mapping(item) for item in raw_plans if isinstance(item, Mapping)]
        )

    @classmethod
    def from_json(cls, payload: str) -> FixPlanDocument:
        data = json.loads(payload)
        if isinstance(data, list):
            return cls(
                plans=[FixPlan.from_mapping(item) for item in data if isinstance(item, Mapping)]
            )
        if not isinstance(data, Mapping):
            raise ValueError("FixPlanDocument JSON payload must decode to an object or list")
        return cls.from_mapping(data)
