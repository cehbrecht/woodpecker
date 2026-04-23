from __future__ import annotations

from functools import cached_property
import json
from typing import Any, Mapping

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from woodpecker.identifiers import IdentifierRules, IdentifierSet


def _string_or_empty(value: object) -> str:
    return "" if value is None else str(value)


def _dict_or_empty(value: object, *, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping/object")
    return dict(value)


def _list_or_empty(value: object, *, label: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return list(value)


def _coerce_schema_version(value: object) -> int:
    if value in (None, ""):
        return 1
    try:
        schema_version = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("FixPlanDocument 'schema_version' must be an integer") from exc
    if schema_version < 1:
        raise ValueError("FixPlanDocument 'schema_version' must be >= 1")
    return schema_version


class Link(BaseModel):
    """Link metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rel: str
    href: str
    title: str | None = None


class FixRef(BaseModel):
    """Fix reference with optional options and links."""

    model_config = ConfigDict(extra="forbid")

    id: str
    options: dict[str, Any] = Field(default_factory=dict)
    links: list[Link] = Field(default_factory=list)

    @field_validator("id", mode="before")
    @classmethod
    def _normalize_and_validate_id(cls, v: object) -> str:
        normalized = IdentifierRules.normalize(v)
        if not normalized:
            raise ValueError("FixRef.id must be a non-empty string")
        if "." in normalized:
            IdentifierRules.validate_canonical_id("FixRef.id", normalized)
        else:
            IdentifierRules.validate_local_id("FixRef.id", normalized)
        return normalized

    @field_validator("options", mode="before")
    @classmethod
    def _coerce_options(cls, v: object) -> dict[str, Any]:
        return _dict_or_empty(v, label="FixRef.options")

    @field_validator("links", mode="before")
    @classmethod
    def _coerce_links(cls, v: object) -> list[Any]:
        return _list_or_empty(v, label="FixRef.links")


class DatasetMatcher(BaseModel):
    """Dataset match criteria."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    attrs: dict[str, Any] = Field(default_factory=dict)
    path_patterns: list[str] = Field(default_factory=list)

    @field_validator("attrs", mode="before")
    @classmethod
    def _coerce_attrs(cls, v: object) -> dict[str, Any]:
        return _dict_or_empty(v, label="DatasetMatcher.attrs")

    @field_validator("path_patterns", mode="before")
    @classmethod
    def _coerce_path_patterns(cls, v: object) -> list[str]:
        return [str(item) for item in _list_or_empty(v, label="DatasetMatcher.path_patterns")]


class ProviderMetadata(BaseModel):
    """Runtime provider metadata."""

    model_config = ConfigDict(frozen=True)

    name: str
    version: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _coerce_name(cls, v: object) -> str:
        return str(v or "").strip()

    @field_validator("version", mode="before")
    @classmethod
    def _coerce_version(cls, v: object) -> str | None:
        if v is None:
            return None
        stripped = str(v).strip()
        return stripped or None


class FixPlanRuntimeMetadata(BaseModel):
    """Runtime-only plan metadata."""

    model_config = ConfigDict(frozen=True)

    provider: ProviderMetadata | None = None


def parse_fix_ref(item: Any) -> FixRef:
    if isinstance(item, str):
        return FixRef(id=item)
    if not isinstance(item, Mapping):
        raise ValueError("Each fix entry must be a string or object")
    return FixRef.model_validate(dict(item))


class FixPlan(BaseModel):
    """Fix plan with scoped fix references."""

    model_config = ConfigDict(extra="forbid")

    id: str
    description: str = ""
    match: DatasetMatcher | None = None
    fixes: list[FixRef] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)
    runtime_metadata: FixPlanRuntimeMetadata | None = Field(default=None, repr=False, exclude=True)

    @field_validator("description", mode="before")
    @classmethod
    def _coerce_description(cls, v: object) -> str:
        return _string_or_empty(v)

    @field_validator("id", mode="before")
    @classmethod
    def _normalize_and_validate_id(cls, v: object) -> str:
        normalized = IdentifierRules.normalize(v)
        if not normalized:
            raise ValueError("FixPlan.id must be a non-empty canonical identifier")
        IdentifierRules.validate_canonical_id("FixPlan.id", normalized)
        return normalized

    @field_validator("fixes", mode="before")
    @classmethod
    def _parse_fix_refs(cls, v: object) -> list[Any]:
        items = _list_or_empty(v, label="FixPlan 'fixes'")
        return [parse_fix_ref(item) if not isinstance(item, FixRef) else item for item in items]

    @field_validator("links", mode="before")
    @classmethod
    def _coerce_links(cls, v: object) -> list[Any]:
        return _list_or_empty(v, label="FixPlan.links")

    @model_validator(mode="after")
    def _scope_fix_refs(self) -> FixPlan:
        """Scope local fix refs to this plan namespace."""
        self.fixes = [
            FixRef(id=self.resolve_fix_identifier(ref), options=ref.options, links=ref.links)
            for ref in self.fixes
        ]
        return self

    @property
    def namespace_prefix(self) -> str:
        return self.id.split(".", 1)[0]

    @property
    def local_id(self) -> str:
        return self.id.split(".", 1)[1]

    @cached_property
    def identifier_set(self) -> IdentifierSet:
        """Cached identifier set for plan identity."""
        return IdentifierRules.build(self.namespace_prefix, self.local_id)

    def resolve_fix_identifier(self, ref: FixRef) -> str:
        token = IdentifierRules.normalize(ref.id)
        if not token:
            return token
        if "." in token:
            return token
        return f"{self.namespace_prefix}.{token}"

    def runtime_metadata_dump(self) -> dict[str, Any] | None:
        """Return optional runtime metadata for provenance/output contexts."""
        if self.runtime_metadata is None:
            return None
        payload: dict[str, Any] = {}
        provider = self.runtime_metadata.provider
        if provider is not None and provider.name:
            payload["provider"] = provider.model_dump(exclude_none=True)
        return payload or None


class FixPlanDocument(BaseModel):
    """Versioned collection of fix plans."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    plans: list[FixPlan] = Field(default_factory=list)

    @field_validator("schema_version", mode="before")
    @classmethod
    def _validate_schema_version(cls, v: object) -> int:
        return _coerce_schema_version(v)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> FixPlanDocument:
        schema_version = _coerce_schema_version(payload.get("schema_version", 1))
        raw_plans = payload.get("plans")
        if raw_plans is None:
            plan_payload = {key: value for key, value in payload.items() if key != "schema_version"}
            return cls(schema_version=schema_version, plans=[FixPlan.model_validate(plan_payload)])
        raw_plans = _list_or_empty(raw_plans, label="FixPlanDocument 'plans'")
        return cls(
            schema_version=schema_version,
            plans=[FixPlan.model_validate(item) for item in raw_plans if isinstance(item, Mapping)],
        )

    @classmethod
    def from_json(cls, payload: str) -> FixPlanDocument:
        data = json.loads(payload)
        if isinstance(data, list):
            return cls(
                schema_version=1,
                plans=[FixPlan.model_validate(item) for item in data if isinstance(item, Mapping)],
            )
        if not isinstance(data, Mapping):
            raise ValueError("FixPlanDocument JSON payload must decode to an object or list")
        return cls.from_payload(data)
