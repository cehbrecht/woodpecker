from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Type

from woodpecker.identifiers import IdentifierResolver, IdentifierRules

from .base import Fix, GroupFix


class FixRegistry:
    """Simple in-memory registry with a pluggy-ready public API.

    - Simple today: decorator registration + in-memory discovery.
    - Future-proof: register/discover/to_json can later be backed by pluggy
      entry points or a DB/index without changing callers.
    """

    _registry: Dict[str, Type[Any]] = {}
    _resolver: IdentifierResolver = IdentifierResolver()

    @classmethod
    def _infer_namespace_prefix_from_module(cls, fix_cls: Type[Any]) -> str:
        """Infer a namespace prefix from the fix module path.

        This is intentionally isolated so registry-level prefix ownership can
        replace module inference later without touching caller flow.
        """

        module = getattr(fix_cls, "__module__", "")
        if module.startswith("woodpecker.fixes.") or module == "woodpecker.fixes":
            return "woodpecker"

        package = module.split(".", 1)[0]
        package = IdentifierRules.normalize(package)
        if package.startswith("woodpecker_"):
            package = package[len("woodpecker_") :]
        if package.endswith("_plugin"):
            package = package[: -len("_plugin")]
        return package or "woodpecker"

    @classmethod
    def _derive_namespace_prefix(cls, fix_cls: Type[Any], explicit: str) -> str:
        token = IdentifierRules.normalize(explicit)
        if token:
            return token
        return cls._infer_namespace_prefix_from_module(fix_cls)

    @classmethod
    def _derive_fix_local_id(cls, fix_cls: Type[Any], explicit: str) -> str:
        """Derive local_id with precedence:

        1) explicit class/local `local_id`
        2) optional `derived_local_id()`
        3) class name transformed to snake_case
        """

        token = IdentifierRules.normalize(explicit)
        if token:
            return token

        derived = getattr(fix_cls, "derived_local_id", None)
        if callable(derived):
            return IdentifierRules.normalize(str(derived()))

        return IdentifierRules.derive_local_id_from_name(
            str(getattr(fix_cls, "__name__", "") or "")
        )

    @classmethod
    def _derive_identifiers(cls, fix_cls: Type[Any]):
        prefix = cls._derive_namespace_prefix(
            fix_cls, str(getattr(fix_cls, "namespace_prefix", "") or "")
        )
        local_id = cls._derive_fix_local_id(fix_cls, str(getattr(fix_cls, "local_id", "") or ""))

        return IdentifierRules.build(
            prefix=prefix,
            local_id=local_id,
            aliases=getattr(fix_cls, "aliases", None),
        )

    @classmethod
    def resolve_identifier(cls, identifier: str) -> str:
        return cls._resolver.resolve(identifier)

    @staticmethod
    def _instantiate_fix(fix_cls: Type[Any]) -> Any:
        try:
            fix = fix_cls()
        except Exception as exc:  # pragma: no cover - defensive guard
            raise ValueError(
                f"Fix {fix_cls.__name__} could not be instantiated. "
                "Ensure default metadata values are provided on the class."
            ) from exc
        return fix

    @classmethod
    def _validate_fix_definition(cls, fix: Any, fix_cls: Type[Any]) -> None:
        name = str(getattr(fix, "name", "") or "").strip()
        categories = getattr(fix, "categories", []) or []
        priority = getattr(fix, "priority", 10)

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
    def registered_canonical_ids(cls) -> List[str]:
        return sorted(cls._registry.keys())

    @classmethod
    def registered_ids(cls) -> List[str]:
        return cls.registered_canonical_ids()

    @classmethod
    def register(cls, fix_cls: Type[Any]):
        fix = cls._instantiate_fix(fix_cls)
        cls._validate_fix_definition(fix, fix_cls)

        identifier_set = cls._derive_identifiers(fix_cls)
        if identifier_set.canonical_id in cls._registry:
            raise ValueError(
                f"Duplicate fix canonical id '{identifier_set.canonical_id}' (already registered)"
            )

        setattr(fix_cls, "namespace_prefix", identifier_set.prefix)
        setattr(fix_cls, "local_id", identifier_set.local_id)
        setattr(fix_cls, "canonical_id", identifier_set.canonical_id)
        setattr(fix_cls, "aliases", list(identifier_set.aliases))

        cls._registry[identifier_set.canonical_id] = fix_cls
        cls._resolver.register(identifier_set, include_local_id=True)
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
            data.append(
                {
                    "id": getattr(f, "canonical_id", ""),
                    "local_id": getattr(f, "local_id", ""),
                    "namespace": getattr(f, "namespace_prefix", ""),
                    "aliases": list(getattr(f, "aliases", []) or []),
                    "links": list(getattr(f, "links", []) or []),
                    "name": getattr(f, "name", ""),
                    "description": getattr(f, "description", ""),
                    "categories": list(getattr(f, "categories", []) or []),
                    "dataset": getattr(f, "dataset", None),
                    "priority": getattr(f, "priority", 10),
                }
            )

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
