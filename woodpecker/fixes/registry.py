from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
import json


@dataclass
class Fix:
    """Catalog metadata about a fix.

    This object is intentionally JSON-friendly. Transformation logic can live
    elsewhere (e.g., WPS operator or future fix-engine modules).
    """

    code: str = ""
    name: str = ""
    description: str = ""
    categories: List[str] = field(default_factory=list)  # e.g. ["metadata", "calendar", "structure"]
    priority: int = 10            # lower runs earlier
    dataset: Optional[str] = None # e.g. "CMIP6-decadal", "CORDEX", "ATLAS"

    def matches(self, path: Path) -> bool:
        return path.suffix.lower() == ".nc"

    def check(self, path: Path) -> List[str]:
        return []

    def apply(self, path: Path, dry_run: bool = True) -> bool:
        return False


class FixRegistry:
    """Simple in-memory registry with a pluggy-ready public API.

    - Simple today: decorator registration + in-memory discovery.
    - Future-proof: register/discover/to_json can later be backed by pluggy
      entry points or a DB/index without changing callers.
    """

    _registry: Dict[str, Type[Any]] = {}

    @staticmethod
    def _instantiate_fix(fix_cls: Type[Any]) -> Any:
        fix = fix_cls()
        if isinstance(fix, Fix):
            for attr in ("code", "name", "description", "categories", "priority", "dataset"):
                if hasattr(fix_cls, attr):
                    setattr(fix, attr, getattr(fix_cls, attr))
            fix.categories = list(getattr(fix, "categories", []) or [])
        return fix

    @classmethod
    def register(cls, fix_cls: Type[Any]):
        code = getattr(fix_cls, "code", None)
        if not code:
            raise ValueError(f"Fix {fix_cls.__name__} must define a non-empty 'code'")

        if code in cls._registry:
            raise ValueError(f"Duplicate fix code '{code}' (already registered)")

        cls._registry[code] = fix_cls
        return fix_cls  # decorator-friendly

    @classmethod
    def discover(cls, filters: Optional[Dict[str, Any]] = None) -> List[Fix]:
        """Return instantiated Fix objects, optionally filtered.

        Example:
            FixRegistry.discover(filters={"dataset": "CMIP6-decadal"})
            FixRegistry.discover(filters={"categories": "metadata"})
        """
        fixes = [cls._instantiate_fix(fix_cls) for fix_cls in cls._registry.values()]

        if not filters:
            return sorted(fixes, key=lambda f: getattr(f, "priority", 10))

        def match(f: Fix) -> bool:
            for key, val in filters.items():
                attr = getattr(f, key, None)
                if attr is None:
                    return False
                if isinstance(attr, list):
                    if isinstance(val, str):
                        if val not in attr:
                            return False
                    else:
                        if not any(v in attr for v in val):
                            return False
                else:
                    if attr != val:
                        return False
            return True

        out = [f for f in fixes if match(f)]
        return sorted(out, key=lambda f: getattr(f, "priority", 10))

    @classmethod
    def to_json(cls, path: str):
        """Export all fixes to a JSON catalog."""
        fixes = cls.discover()
        data = []
        for f in fixes:
            # Support future Pydantic v2 models transparently
            if hasattr(f, "model_dump"):
                data.append(f.model_dump())
            else:
                data.append(asdict(f))

        with open(path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)
