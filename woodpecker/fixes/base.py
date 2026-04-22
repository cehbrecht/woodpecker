from __future__ import annotations

import re
from typing import Any, ClassVar, Optional, Type

import xarray as xr


class Fix:
    """Catalog metadata about a fix plus check/apply behavior hooks.

    Fix definitions are class-based: metadata is declared on the class.
    Runtime mutable state (such as config) lives on instances.
    """

    namespace_prefix: ClassVar[str] = ""
    local_id: ClassVar[str] = ""
    canonical_id: ClassVar[str] = ""
    aliases: ClassVar[list[str]] = []
    links: ClassVar[list[dict[str, str]]] = []
    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    categories: ClassVar[list[str]] = []
    priority: ClassVar[int] = 10
    dataset: ClassVar[Optional[str]] = None
    metadata_fields: ClassVar[tuple[str, ...]] = (
        "namespace_prefix",
        "local_id",
        "canonical_id",
        "aliases",
        "links",
        "name",
        "description",
        "categories",
        "priority",
        "dataset",
    )

    def __init__(self) -> None:
        self.config: dict[str, Any] = {}

    @classmethod
    def derived_local_id(cls) -> str:
        class_name = cls.__name__
        if class_name.endswith("Fix"):
            class_name = class_name[: -len("Fix")]
        first = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", class_name)
        second = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first)
        return re.sub(r"__+", "_", second).strip("_").lower()

    def matches(self, dataset: xr.Dataset) -> bool:
        return isinstance(dataset, xr.Dataset)

    def configure(self, config: dict[str, Any] | None = None) -> Fix:
        self.config = dict(config or {})
        return self

    def check(self, dataset: xr.Dataset, **options: Any) -> Any:
        return []

    def fix(self, dataset: xr.Dataset, **options: Any) -> Any:
        return dataset

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        return False

    @classmethod
    def class_metadata(cls) -> dict[str, Any]:
        """Return metadata from class-level declarations.

        Mutable fields are copied to avoid accidental cross-instance mutation.
        """

        payload: dict[str, Any] = {}
        for field in cls.metadata_fields:
            value = getattr(cls, field, None)
            if isinstance(value, list):
                payload[field] = list(value)
            elif isinstance(value, dict):
                payload[field] = dict(value)
            else:
                payload[field] = value
        return payload

    def metadata(self) -> dict[str, Any]:
        """Return instance-visible metadata backed by class defaults."""

        return type(self).class_metadata()


class GroupFix(Fix):
    """A Fix that chains multiple member fixes, applying them in sequence."""

    members: ClassVar[list[Type[Any]]] = []

    @classmethod
    def _validate_members(cls) -> None:
        if not cls.members:
            raise ValueError(f"GroupFix '{cls.__name__}' must define non-empty members")

    @staticmethod
    def _member_keys(member_cls: Type[Any]) -> list[str]:
        keys: list[str] = []
        seen: set[str] = set()

        def _add(token: str) -> None:
            value = str(token or "").strip().lower()
            if not value or value in seen:
                return
            seen.add(value)
            keys.append(value)

        canonical_id = str(getattr(member_cls, "canonical_id", "") or "").strip().lower()
        local_id = str(getattr(member_cls, "local_id", "") or "").strip().lower()
        namespace_prefix = str(getattr(member_cls, "namespace_prefix", "") or "").strip().lower()
        aliases = list(getattr(member_cls, "aliases", []) or [])

        _add(canonical_id)
        _add(local_id)
        for alias in aliases:
            alias_token = str(alias or "").strip().lower()
            if not alias_token:
                continue
            if "." in alias_token:
                _add(alias_token)
            else:
                _add(alias_token)
                if namespace_prefix:
                    _add(f"{namespace_prefix}.{alias_token}")
        return keys

    def _member_config(self, member_cls: Type[Any]) -> dict[str, Any]:
        config = getattr(self, "config", {}) or {}
        members = config.get("members", {}) if isinstance(config, dict) else {}
        if not isinstance(members, dict):
            return {}
        for key in self._member_keys(member_cls):
            value = members.get(key)
            if isinstance(value, dict):
                return value
        return {}

    def matches(self, dataset: xr.Dataset) -> bool:
        self._validate_members()
        return any(cls().matches(dataset) for cls in self.members)

    def check(self, dataset: xr.Dataset, **options: Any) -> list[str]:
        self._validate_members()
        issues: list[str] = []
        for cls in self.members:
            fix = cls().configure(self._member_config(cls))
            if fix.matches(dataset):
                findings = fix.check(dataset, **options)
                if isinstance(findings, list):
                    issues.extend([str(item) for item in findings])
        return issues

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        self._validate_members()
        applied = False
        for cls in sorted(self.members, key=lambda c: getattr(c, "priority", 10)):
            fix = cls().configure(self._member_config(cls))
            if fix.apply(dataset, dry_run=dry_run):
                applied = True
        return applied
