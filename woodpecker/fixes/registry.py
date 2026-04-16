from __future__ import annotations

import json
import re
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Type

from .base import Fix, GroupFix


class FixRegistry:
    """Simple in-memory registry with a pluggy-ready public API.

    - Simple today: decorator registration + in-memory discovery.
    - Future-proof: register/discover/to_json can later be backed by pluggy
      entry points or a DB/index without changing callers.
    """

    _registry: Dict[str, Type[Any]] = {}
    _code_pattern = re.compile(r"^[A-Z0-9_]{4,16}$")

    @staticmethod
    def _instantiate_fix(fix_cls: Type[Any]) -> Any:
        try:
            fix = fix_cls()
        except Exception as exc:  # pragma: no cover - defensive guard
            raise ValueError(
                f"Fix {fix_cls.__name__} could not be instantiated. "
                "Ensure default metadata values are provided on the class."
            ) from exc
        if isinstance(fix, Fix):
            for attr in ("code", "name", "description", "categories", "priority", "dataset"):
                if hasattr(fix_cls, attr):
                    setattr(fix, attr, getattr(fix_cls, attr))
            fix.categories = list(getattr(fix, "categories", []) or [])
        return fix

    @classmethod
    def _validate_fix_definition(cls, fix: Any, fix_cls: Type[Any]) -> None:
        code = str(getattr(fix, "code", "") or "").strip()
        name = str(getattr(fix, "name", "") or "").strip()
        categories = getattr(fix, "categories", []) or []
        priority = getattr(fix, "priority", 10)

        if not code:
            raise ValueError(f"Fix {fix_cls.__name__} must define a non-empty 'code'")
        if not cls._code_pattern.fullmatch(code):
            raise ValueError(
                f"Fix {fix_cls.__name__} has invalid code '{code}'. "
                "Expected pattern: ^[A-Z0-9_]{4,16}$"
            )
        if not name:
            raise ValueError(f"Fix {fix_cls.__name__} must define a non-empty 'name'")
        if not isinstance(priority, int):
            raise ValueError(f"Fix {fix_cls.__name__} must define 'priority' as an integer")
        if not isinstance(categories, list) or any(
            (not isinstance(item, str) or not item.strip()) for item in categories
        ):
            raise ValueError(
                f"Fix {fix_cls.__name__} must define 'categories' as a list of non-empty strings"
            )

    @classmethod
    def registered_codes(cls) -> List[str]:
        return sorted(cls._registry.keys())

    @classmethod
    def register(cls, fix_cls: Type[Any]):
        fix = cls._instantiate_fix(fix_cls)
        cls._validate_fix_definition(fix, fix_cls)
        code = getattr(fix, "code", None)

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

    @staticmethod
    def source_label(fix: Any) -> str:
        """Return a human-readable source label for a fix.

        Built-in fixes are labeled as "core". Third-party fixes are labeled
        as "plugin:<package>" where package is derived from the fix class
        module root.
        """

        module = getattr(type(fix), "__module__", "")
        if module.startswith("woodpecker.fixes."):
            return "core"

        package = module.split(".", 1)[0] if module else "unknown"
        return f"plugin:{package}"

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


def register_fix(fix_cls: Type[Any]) -> Type[Any]:
    """Decorator alias for registering fixes.

    This keeps the plugin author API minimal:

        from woodpecker.fixes.registry import Fix, register_fix

        @register_fix
        class MY_FIX(Fix):
            ...
    """

    return FixRegistry.register(fix_cls)


__all__ = ["Fix", "GroupFix", "FixRegistry", "register_fix"]
