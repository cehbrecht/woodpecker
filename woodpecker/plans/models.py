from __future__ import annotations

import json
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator

from woodpecker.identifiers import IdentifierRules, IdentifierSet, coerce_scoped_identifier


class Link(BaseModel):
    """A typed hyperlink reference used in fix plans and fix refs."""

    model_config = ConfigDict(extra="forbid")

    rel: str
    href: str
    title: str | None = None


class FixRef(BaseModel):
    """Reference to a fix within a plan, carrying an identifier and optional options."""

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
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("FixRef.options must be a mapping/object")
        return dict(v)

    @field_validator("links", mode="before")
    @classmethod
    def _coerce_links(cls, v: object) -> list[Any]:
        return [] if v is None else v

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"id": self.id, "options": dict(self.options)}
        if self.links:
            payload["links"] = [link.model_dump(exclude_none=True) for link in self.links]
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> FixRef:
        return cls.model_validate(dict(payload))


class DatasetMatcher(BaseModel):
    """Criteria for matching datasets by attributes or path patterns."""

    model_config = ConfigDict(extra="forbid")

    attrs: dict[str, Any] = Field(default_factory=dict)
    path_patterns: list[str] = Field(default_factory=list)

    @field_validator("attrs", mode="before")
    @classmethod
    def _coerce_attrs(cls, v: object) -> dict[str, Any]:
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("DatasetMatcher.attrs must be a mapping/object")
        return dict(v)

    @field_validator("path_patterns", mode="before")
    @classmethod
    def _coerce_path_patterns(cls, v: object) -> list[str]:
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("DatasetMatcher.path_patterns must be a list")
        return [str(p) for p in v]

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> DatasetMatcher:
        return cls.model_validate(dict(payload))


class ProviderMetadata(BaseModel):
    """Optional runtime provider metadata for provenance and output annotations."""

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

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> ProviderMetadata:
        return cls.model_validate(dict(payload))


class FixPlanRuntimeMetadata(BaseModel):
    """Optional runtime metadata that is intentionally not part of persisted plans."""

    model_config = ConfigDict(frozen=True)

    provider: ProviderMetadata | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.provider is not None and self.provider.name:
            payload["provider"] = self.provider.to_dict()
        return payload

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> FixPlanRuntimeMetadata:
        return cls.model_validate(dict(payload))


def parse_fix_ref(item: Any) -> FixRef:
    if isinstance(item, str):
        return FixRef(id=item)
    if not isinstance(item, Mapping):
        raise ValueError("Each fix entry must be a string or object")
    return FixRef.model_validate(dict(item))


class FixPlan(BaseModel):
    """A fix plan: an optionally scoped set of fix references with dataset matching rules.

    The ``id`` field accepts either a canonical ``<namespace>.<local_id>`` form or a
    bare local id.  When a ``namespace_prefix`` is provided alongside a bare id, the
    canonical id is assembled and an ``IdentifierSet`` is attached.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = ""
    local_id: str = ""
    namespace_prefix: str = ""
    description: str = ""
    match: DatasetMatcher | None = None
    fixes: list[FixRef] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)
    runtime_metadata: FixPlanRuntimeMetadata | None = Field(default=None, repr=False)

    _identifier_set: IdentifierSet | None = PrivateAttr(default=None)

    @field_validator("id", "local_id", "namespace_prefix", "description", mode="before")
    @classmethod
    def _coerce_str_fields(cls, v: object) -> str:
        return str(v) if v is not None else ""

    @field_validator("fixes", mode="before")
    @classmethod
    def _parse_fix_refs(cls, v: object) -> list[Any]:
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("FixPlan 'fixes' must be a list")
        return [parse_fix_ref(item) if not isinstance(item, FixRef) else item for item in v]

    @field_validator("links", mode="before")
    @classmethod
    def _coerce_links(cls, v: object) -> list[Any]:
        return [] if v is None else v

    @model_validator(mode="after")
    def _resolve_and_scope(self) -> FixPlan:
        """Resolve identifiers and scope unqualified fix refs to the plan namespace."""
        resolved = coerce_scoped_identifier(
            canonical_id=self.id,
            local_id=self.local_id,
            namespace_prefix=self.namespace_prefix,
            canonical_label="FixPlan.id",
        )
        self.id = resolved.canonical_id
        self.local_id = resolved.local_id
        self.namespace_prefix = resolved.namespace_prefix
        self._identifier_set = resolved.identifier_set

        # Re-scope fix refs using the resolved namespace prefix.
        self.fixes = [
            FixRef(id=self.resolve_fix_identifier(ref), options=ref.options, links=ref.links)
            for ref in self.fixes
        ]
        return self

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
        payload: dict[str, Any] = {
            "id": self.id,
            "description": self.description,
            "match": self.match.to_dict() if self.match is not None else None,
            "fixes": [fix.to_dict() for fix in self.fixes],
        }
        if self.links:
            payload["links"] = [link.model_dump(exclude_none=True) for link in self.links]
        return payload

    def runtime_metadata_dict(self) -> dict[str, Any] | None:
        """Return optional runtime metadata for provenance/output contexts."""
        if self.runtime_metadata is None:
            return None
        payload = self.runtime_metadata.to_dict()
        return payload or None

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> FixPlan:
        """Deserialize a ``FixPlan`` from a plain mapping.

        Fix entries may be plain id strings or ``{id, options, links}`` objects.
        """
        return cls.model_validate(dict(payload))

    @classmethod
    def from_json(cls, payload: str) -> FixPlan:
        return cls.model_validate_json(payload)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> FixPlan:
        """Parse a ``FixPlan`` from an external mapping (alias for ``from_dict``)."""
        return cls.from_dict(payload)


class FixPlanDocument(BaseModel):
    """A versioned collection of fix plans."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    plans: list[FixPlan] = Field(default_factory=list)

    @staticmethod
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

    @field_validator("schema_version", mode="before")
    @classmethod
    def _validate_schema_version(cls, v: object) -> int:
        return cls._coerce_schema_version(v)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "plans": [plan.to_dict() for plan in self.plans],
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> FixPlanDocument:
        schema_version = cls._coerce_schema_version(payload.get("schema_version", 1))
        raw_plans = payload.get("plans")
        if raw_plans is None:
            # Single-plan shorthand: strip document-level keys before constructing FixPlan.
            plan_payload = {k: v for k, v in payload.items() if k != "schema_version"}
            return cls(schema_version=schema_version, plans=[FixPlan.from_mapping(plan_payload)])
        if not isinstance(raw_plans, list):
            raise ValueError("FixPlanDocument 'plans' must be a list")
        return cls(
            schema_version=schema_version,
            plans=[FixPlan.from_mapping(item) for item in raw_plans if isinstance(item, Mapping)],
        )

    @classmethod
    def from_json(cls, payload: str) -> FixPlanDocument:
        data = json.loads(payload)
        if isinstance(data, list):
            return cls(
                schema_version=1,
                plans=[FixPlan.from_mapping(item) for item in data if isinstance(item, Mapping)],
            )
        if not isinstance(data, Mapping):
            raise ValueError("FixPlanDocument JSON payload must decode to an object or list")
        return cls.from_mapping(data)
