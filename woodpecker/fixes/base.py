from __future__ import annotations

import re
from typing import Any, ClassVar, Optional

import xarray as xr


class FixFunction:
    """Catalog metadata about a fix function plus check/apply behavior hooks.

    Fix function definitions are class-based: metadata is declared on the class.
    Runtime mutable state (such as config) lives on instances.
    """

    prefix: ClassVar[str] = ""
    suffix: ClassVar[str] = ""
    id: ClassVar[str] = ""
    aliases: ClassVar[list[str]] = []
    links: ClassVar[list[dict[str, str]]] = []
    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    categories: ClassVar[list[str]] = []
    priority: ClassVar[int] = 10
    dataset: ClassVar[Optional[str]] = None
    metadata_fields: ClassVar[tuple[str, ...]] = (
        "prefix",
        "suffix",
        "id",
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
    def derived_suffix(cls) -> str:
        class_name = cls.__name__
        first = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", class_name)
        second = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first)
        return re.sub(r"__+", "_", second).strip("_").lower()

    def matches(self, dataset: xr.Dataset) -> bool:
        return isinstance(dataset, xr.Dataset)

    def configure(self, config: dict[str, Any] | None = None) -> FixFunction:
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
