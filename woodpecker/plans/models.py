from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from woodpecker.identifiers import IdentifierSet, IdentifierRules


def _validate_links(field_name: str, value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")

    validated: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict) or not item.get("rel") or not item.get("href"):
            raise ValueError(f"{field_name} entries must contain rel and href")
        validated.append(dict(item))
    return validated


def _resolve_plan_identifier_set(
    *,
    plan_id: object,
    local_id: object,
    namespace_prefix: object,
) -> tuple[str, str, str, IdentifierSet | None]:
    normalized_id = IdentifierRules.normalize(plan_id)
    normalized_local_id = IdentifierRules.normalize(local_id)
    normalized_prefix = IdentifierRules.normalize(namespace_prefix)

    if normalized_id and "." in normalized_id:
        IdentifierRules.validate_canonical_id("FixPlan.id", normalized_id)
        parsed_prefix, parsed_local_id = normalized_id.split(".", 1)
        if not normalized_prefix:
            normalized_prefix = parsed_prefix
        if not normalized_local_id:
            normalized_local_id = parsed_local_id
    elif normalized_id and not normalized_local_id:
        normalized_local_id = normalized_id

    identifier_set: IdentifierSet | None = None
    if normalized_prefix and normalized_local_id:
        identifier_set = IdentifierRules.build(normalized_prefix, normalized_local_id)
        normalized_prefix = identifier_set.prefix
        normalized_local_id = identifier_set.local_id
        normalized_id = identifier_set.canonical_id

    return normalized_id, normalized_local_id, normalized_prefix, identifier_set


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
        self.links = _validate_links("FixRef.links", self.links)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"id": self.id, "options": dict(self.options)}
        if self.links:
            payload["links"] = [dict(item) for item in self.links]
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> FixRef:
        return cls(
            id=str(payload.get("id", "")),
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
    fix_id = item.get("id", "")
    return FixRef(
        id=str(fix_id),
        options=dict(item.get("options", {}) or {}),
        links=[dict(link) for link in list(item.get("links", []) or [])],
    )


@dataclass
class FixPlan:
    id: str = ""
    local_id: str = ""
    namespace_prefix: str = ""
    description: str = ""
    match: DatasetMatcher | None = None
    fixes: list[FixRef] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    _identifier_set: IdentifierSet | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.id, self.local_id, self.namespace_prefix, self._identifier_set = (
            _resolve_plan_identifier_set(
                plan_id=self.id,
                local_id=self.local_id,
                namespace_prefix=self.namespace_prefix,
            )
        )
        self.description = str(self.description)
        self.links = _validate_links("FixPlan.links", self.links)

        # Keep canonical IDs as primary plan identity for fixes.
        self.fixes = [
            FixRef(id=self.resolve_fix_identifier(ref), options=ref.options, links=ref.links)
            for ref in self.fixes
        ]

    @property
    def identifier_set(self) -> IdentifierSet | None:
        """Resolved identifier model for plan identity when prefix + local id are known."""

        return self._identifier_set

    def resolve_fix_identifier(self, ref: FixRef) -> str:
        token = IdentifierRules.normalize(ref.id)
        if not token:
            return token
        if "." in token:
            return token
        if self.namespace_prefix:
            return f"{self.namespace_prefix}.{token}"
        return token

    def to_dict(self) -> dict[str, Any]:
        fix_entries: list[dict[str, Any]] = []
        for fix in self.fixes:
            row: dict[str, Any] = {
                "id": fix.id,
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
        if self.namespace_prefix:
            payload["namespace"] = self.namespace_prefix
        if self.links:
            payload["links"] = [dict(item) for item in self.links]
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> FixPlan:
        raw_match = payload.get("match")
        return cls(
            id=str(payload.get("id", "")),
            local_id=str(payload.get("local_id", "")),
            namespace_prefix=str(payload.get("namespace", "")),
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
