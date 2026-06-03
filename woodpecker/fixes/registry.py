from __future__ import annotations

import json
from typing import Any, Optional, Type

from woodpecker.fixes.identifiers import IdentifierResolver, IdentifierRules

from .base import FixFunction

UNPRIORITIZED = -1


class FixFunctionRegistry:
    """Simple in-memory registry with a pluggy-ready public API.

    - Simple today: decorator registration + in-memory discovery.
    - Future-proof: register/discover/to_json can later be backed by pluggy
      entry points or a DB/index without changing callers.
    """

    _registry: dict[str, Type[Any]] = {}
    _resolver: IdentifierResolver = IdentifierResolver()

    @classmethod
    def _infer_prefix_from_module(cls, fix_cls: Type[Any]) -> str:
        """Infer a prefix from the fix module path.

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
    def _derive_prefix(cls, fix_cls: Type[Any], explicit: str) -> str:
        token = IdentifierRules.normalize(explicit)
        if token:
            return token
        return cls._infer_prefix_from_module(fix_cls)

    @classmethod
    def _derive_fix_suffix(cls, fix_cls: Type[Any], explicit: str) -> str:
        """Derive suffix with precedence:

        1) explicit class `suffix`
        2) optional `derived_suffix()`
        3) class name transformed to snake_case
        """

        token = IdentifierRules.normalize(explicit)
        if token:
            return token

        derived = getattr(fix_cls, "derived_suffix", None)
        if callable(derived):
            return IdentifierRules.normalize(str(derived()))

        return IdentifierRules.derive_suffix_from_name(str(getattr(fix_cls, "__name__", "") or ""))

    @classmethod
    def _derive_identifiers(cls, fix_cls: Type[Any]):
        explicit_id = IdentifierRules.normalize(getattr(fix_cls, "id", "") or "")
        explicit_prefix = str(getattr(fix_cls, "prefix", "") or "")
        prefix = cls._derive_prefix(fix_cls, explicit_prefix)
        explicit_suffix = str(getattr(fix_cls, "suffix", "") or "")
        suffix = cls._derive_fix_suffix(fix_cls, explicit_suffix)

        if explicit_id:
            IdentifierRules.validate_id("fix id", explicit_id)
            parsed_prefix, parsed_suffix = explicit_id.split(".", 1)
            if explicit_prefix and prefix != parsed_prefix:
                raise ValueError("Fix function prefix does not match id prefix")
            if explicit_suffix and suffix != parsed_suffix:
                raise ValueError("Fix function suffix does not match id suffix")
            prefix = parsed_prefix
            suffix = parsed_suffix

        return IdentifierRules.build(
            prefix=prefix,
            suffix=suffix,
            aliases=getattr(fix_cls, "aliases", None),
        )

    @classmethod
    def resolve_identifier(cls, identifier: str) -> str:
        return cls._resolver.resolve(identifier)

    @classmethod
    def get_fix_function(cls, id: str) -> Type[Any]:
        """Return the registered fix function class for an id.

        The input must be an id in the form
        "<prefix>.<suffix>".
        """

        key = str(id).strip()
        fix_cls = cls._registry.get(key)
        if fix_cls is None:
            raise KeyError(f"Unknown fix id: {key}")
        return fix_cls

    @classmethod
    def instantiate(cls, id: str) -> Any:
        """Instantiate and return a fresh fix function instance from an id."""

        return cls._instantiate_fix(cls.get_fix_function(id))

    @staticmethod
    def _instantiate_fix(fix_cls: Type[Any]) -> Any:
        try:
            fix = fix_cls()
        except Exception as exc:  # pragma: no cover - defensive guard
            raise ValueError(
                f"Fix function {fix_cls.__name__} could not be instantiated. "
                "Ensure default metadata values are provided on the class."
            ) from exc
        return fix

    @classmethod
    def _validate_fix_definition(cls, fix: Any, fix_cls: Type[Any]) -> None:
        name = str(getattr(fix, "name", "") or "").strip()
        categories = getattr(fix, "categories", []) or []
        priority = getattr(fix, "priority", UNPRIORITIZED)
        risk = str(getattr(fix, "risk", "") or "").strip()

        if not name:
            raise ValueError(f"Fix function {fix_cls.__name__} must define a non-empty 'name'")
        if not risk:
            raise ValueError(f"Fix function {fix_cls.__name__} must define a non-empty 'risk'")
        if not isinstance(priority, int):
            raise ValueError(
                f"Fix function {fix_cls.__name__} must define 'priority' as an integer"
            )
        if priority < UNPRIORITIZED:
            raise ValueError(
                f"Fix function {fix_cls.__name__} must define 'priority' >= {UNPRIORITIZED}"
            )
        if not isinstance(categories, list) or any(
            (not isinstance(item, str) or not item.strip()) for item in categories
        ):
            raise ValueError(
                f"Fix function {fix_cls.__name__} must define "
                "'categories' as a list of non-empty strings"
            )

    @classmethod
    def registered_ids(cls) -> list[str]:
        return sorted(cls._registry.keys())

    @classmethod
    def register(cls, fix_cls: Type[Any]):
        fix = cls._instantiate_fix(fix_cls)
        cls._validate_fix_definition(fix, fix_cls)

        identifier_set = cls._derive_identifiers(fix_cls)
        if identifier_set.id in cls._registry:
            raise ValueError(f"Duplicate fix id '{identifier_set.id}' (already registered)")

        setattr(fix_cls, "prefix", identifier_set.prefix)
        setattr(fix_cls, "suffix", identifier_set.suffix)
        setattr(fix_cls, "id", identifier_set.id)
        setattr(fix_cls, "aliases", list(identifier_set.aliases))

        cls._registry[identifier_set.id] = fix_cls
        cls._resolver.register(identifier_set)
        return fix_cls  # decorator-friendly

    @staticmethod
    def _priority_sort_key(fix: FixFunction) -> tuple[bool, int, str]:
        priority = int(getattr(fix, "priority", UNPRIORITIZED))
        prioritized = priority >= 0
        return (not prioritized, priority if prioritized else 0, getattr(fix, "id", ""))

    @classmethod
    def discover(cls, filters: Optional[dict[str, Any]] = None) -> list[FixFunction]:
        """Return instantiated fix function objects, optionally filtered.

        Example:
            FixFunctionRegistry.discover(filters={"dataset": "CMIP6-decadal"})
            FixFunctionRegistry.discover(filters={"categories": "metadata"})
        """
        fixes = [cls._instantiate_fix(fix_cls) for fix_cls in cls._registry.values()]

        if not filters:
            return sorted(fixes, key=cls._priority_sort_key)

        def match(f: FixFunction) -> bool:
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
        return sorted(out, key=cls._priority_sort_key)

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
                    "id": getattr(f, "id", ""),
                    "suffix": getattr(f, "suffix", ""),
                    "prefix": getattr(f, "prefix", ""),
                    "aliases": list(getattr(f, "aliases", []) or []),
                    "links": list(getattr(f, "links", []) or []),
                    "name": getattr(f, "name", ""),
                    "description": getattr(f, "description", ""),
                    "categories": list(getattr(f, "categories", []) or []),
                    "dataset": getattr(f, "dataset", None),
                    "priority": getattr(f, "priority", UNPRIORITIZED),
                    "risk": getattr(f, "risk", ""),
                }
            )

        with open(path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)


def register_fix_function(fix_cls: Type[Any]) -> Type[Any]:
    """Decorator for registering fix functions.

    This keeps the plugin author API minimal:

        from woodpecker.fixes.registry import FixFunction, register_fix_function

        @register_fix_function
        class MyRepair(FixFunction):
            ...
    """

    return FixFunctionRegistry.register(fix_cls)


__all__ = ["FixFunction", "FixFunctionRegistry", "UNPRIORITIZED", "register_fix_function"]
