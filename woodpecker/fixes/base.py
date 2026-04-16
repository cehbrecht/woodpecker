from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar, List, Optional, Type

import xarray as xr


@dataclass
class Fix:
    """Catalog metadata about a fix plus check/apply behavior hooks."""

    code: str = ""
    name: str = ""
    description: str = ""
    categories: List[str] = field(default_factory=list)
    priority: int = 10
    dataset: Optional[str] = None

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


@dataclass
class GroupFix(Fix):
    """A Fix that chains multiple member fixes, applying them in sequence."""

    members: ClassVar[List[Type[Any]]] = []
    member_codes: List[str] = field(default_factory=list)

    def _member_config(self, code: str) -> dict[str, Any]:
        config = getattr(self, "config", {}) or {}
        members = config.get("members", {}) if isinstance(config, dict) else {}
        if not isinstance(members, dict):
            return {}
        value = members.get(code, {})
        return value if isinstance(value, dict) else {}

    def __post_init__(self) -> None:
        if not self.members:
            raise ValueError(
                f"GroupFix '{self.code or self.__class__.__name__}' must define non-empty members"
            )
        if not self.member_codes and self.members:
            self.member_codes = [getattr(cls, "code", "") for cls in self.members]

    def matches(self, dataset: xr.Dataset) -> bool:
        return any(cls().matches(dataset) for cls in self.members)

    def check(self, dataset: xr.Dataset, **options: Any) -> list[str]:
        issues: list[str] = []
        for cls in self.members:
            fix = cls().configure(self._member_config(getattr(cls, "code", "")))
            if fix.matches(dataset):
                findings = fix.check(dataset, **options)
                if isinstance(findings, list):
                    issues.extend([str(item) for item in findings])
        return issues

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        applied = False
        for cls in sorted(self.members, key=lambda c: getattr(c, "priority", 10)):
            fix = cls().configure(self._member_config(getattr(cls, "code", "")))
            if fix.apply(dataset, dry_run=dry_run):
                applied = True
        return applied
