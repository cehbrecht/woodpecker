from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except Exception:  # pragma: no cover - optional import guard
    yaml = None


@dataclass
class FixRef:
    """Reference to one fix and its optional options payload."""

    id: str
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.id = str(self.id).strip()
        if not self.id:
            raise ValueError("FixRef.id must be a non-empty string")
        if not isinstance(self.options, dict):
            raise ValueError("FixRef.options must be a mapping/object")


@dataclass
class FixPlan:
    """A lightweight data structure describing fixes to execute."""

    fixes: list[FixRef] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> FixPlan:
        items = payload.get("fixes", [])
        if not isinstance(items, list):
            raise ValueError("FixPlan 'fixes' must be a list")
        return cls(fixes=[_parse_fix_ref(item) for item in items])


def _parse_fix_ref(item: Any) -> FixRef:
    if isinstance(item, str):
        return FixRef(id=item)
    if not isinstance(item, Mapping):
        raise ValueError("Each fix entry must be a string or object")
    return FixRef(id=str(item.get("id", "")), options=dict(item.get("options", {}) or {}))


def _resolve_fix(registry: Any, fix_id: str) -> Any:
    source: Any | None = None
    if isinstance(registry, Mapping):
        source = registry.get(fix_id)
    elif hasattr(registry, "_registry"):
        source = getattr(registry, "_registry", {}).get(fix_id)
    elif hasattr(registry, "get"):
        source = registry.get(fix_id)

    if source is None:
        raise KeyError(f"Unknown fix id: {fix_id}")

    if isinstance(source, type):
        return source()
    if callable(source) and not hasattr(source, "check"):
        return source()
    return source


def apply_plan(ds: Any, plan: FixPlan, registry: Any) -> Any:
    """Resolve plan fix ids from a registry and execute check then fix/apply."""

    for ref in plan.fixes:
        fix = _resolve_fix(registry, ref.id)

        if hasattr(fix, "configure"):
            fix = fix.configure(ref.options)

        if not hasattr(fix, "check"):
            raise TypeError(f"Fix '{ref.id}' does not implement check()")
        fix.check(ds)

        if hasattr(fix, "fix"):
            fix.fix(ds)
        elif hasattr(fix, "apply"):
            fix.apply(ds, dry_run=False)
        else:
            raise TypeError(f"Fix '{ref.id}' does not implement fix() or apply()")

    return ds


def load_fix_plan(path: str | Path) -> FixPlan:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".json":
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    elif suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise ValueError("YAML support requires PyYAML")
        payload = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    else:
        raise ValueError("Unsupported fix plan file extension; use .json, .yaml, or .yml")

    if payload is None:
        payload = {"fixes": []}
    if isinstance(payload, list):
        return FixPlan(fixes=[_parse_fix_ref(item) for item in payload])
    if not isinstance(payload, Mapping):
        raise ValueError("Fix plan file must contain an object or list")

    return FixPlan.from_mapping(payload)
