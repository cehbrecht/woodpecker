from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Type

from .base import Fix, GroupFix


class FixRegistry:
    """Simple in-memory registry with a pluggy-ready public API.

    - Simple today: decorator registration + in-memory discovery.
    - Future-proof: register/discover/to_json can later be backed by pluggy
      entry points or a DB/index without changing callers.
    """

    _registry: Dict[str, Type[Any]] = {}
    _namespace_pattern = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
    _identifier_index: Dict[str, str] = {}
    _ambiguous_identifiers: set[str] = set()

    @staticmethod
    def _normalize_identifier(identifier: str) -> str:
        return str(identifier).strip().lower()

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
        package = cls._normalize_identifier(package)
        if package.startswith("woodpecker_"):
            package = package[len("woodpecker_") :]
        if package.endswith("_plugin"):
            package = package[: -len("_plugin")]
        return package or "woodpecker"

    @classmethod
    def _derive_namespace_prefix(cls, fix_cls: Type[Any], explicit: str) -> str:
        token = cls._normalize_identifier(explicit)
        if token:
            return token
        return cls._infer_namespace_prefix_from_module(fix_cls)

    @staticmethod
    def _camel_to_snake(name: str) -> str:
        first = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        second = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first)
        return re.sub(r"__+", "_", second).strip("_").lower()

    @classmethod
    def _derive_fix_local_id(cls, fix_cls: Type[Any], explicit: str) -> str:
        """Derive local_id with precedence:

        1) explicit class/local `local_id`
        2) optional `derived_local_id()`
        3) class name transformed to snake_case
        """

        token = cls._normalize_identifier(explicit)
        if token:
            return token

        derived = getattr(fix_cls, "derived_local_id", None)
        if callable(derived):
            return cls._normalize_identifier(str(derived()))

        return cls._camel_to_snake(fix_cls.__name__)

    @classmethod
    def _validate_local_identifier(cls, label: str, value: str) -> None:
        if not cls._namespace_pattern.fullmatch(value):
            raise ValueError(
                f"Invalid {label} '{value}'. Expected lowercase snake_case identifier."
            )

    @classmethod
    def _validate_qualified_identifier(cls, label: str, value: str) -> None:
        parts = value.split(".")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid {label} '{value}'. Expected '<prefix>.<local_id>' with snake_case tokens."
            )

        prefix, local_id = parts
        cls._validate_local_identifier(f"{label} prefix", prefix)
        cls._validate_local_identifier(f"{label} local_id", local_id)

    @classmethod
    def _derive_aliases(
        cls,
        *,
        prefix: str,
        canonical_id: str,
        declared_aliases: Any,
    ) -> list[str]:
        if declared_aliases is None:
            return []
        if isinstance(declared_aliases, str):
            raw_aliases = [declared_aliases]
        elif isinstance(declared_aliases, (list, tuple, set)):
            raw_aliases = list(declared_aliases)
        else:
            raise ValueError("Invalid aliases declaration. Expected a string or list of strings.")

        out_aliases: list[str] = []
        seen: set[str] = set()
        for item in raw_aliases:
            alias = cls._normalize_identifier(str(item))
            if not alias:
                continue

            if "." in alias:
                cls._validate_qualified_identifier("alias", alias)
                candidates = [alias]
            else:
                cls._validate_local_identifier("alias", alias)
                candidates = [alias, f"{prefix}.{alias}"]

            for candidate in candidates:
                if candidate == canonical_id or candidate in seen:
                    continue
                seen.add(candidate)
                out_aliases.append(candidate)

        return out_aliases

    @classmethod
    def _derive_namespace_and_local_id(cls, fix_cls: Type[Any]) -> tuple[str, str, str, list[str]]:
        prefix = cls._derive_namespace_prefix(
            fix_cls, str(getattr(fix_cls, "namespace_prefix", "") or "")
        )
        local_id = cls._derive_fix_local_id(fix_cls, str(getattr(fix_cls, "local_id", "") or ""))

        prefix = cls._normalize_identifier(prefix)
        local_id = cls._normalize_identifier(local_id)
        cls._validate_local_identifier("namespace prefix", prefix)
        cls._validate_local_identifier("fix local_id", local_id)

        canonical_id = f"{prefix}.{local_id}"

        out_aliases = cls._derive_aliases(
            prefix=prefix,
            canonical_id=canonical_id,
            declared_aliases=getattr(fix_cls, "aliases", None),
        )

        return prefix, local_id, canonical_id, out_aliases

    @classmethod
    def _register_identifier(cls, identifier: str, canonical_id: str) -> None:
        token = cls._normalize_identifier(identifier)
        if not token:
            return
        if token in cls._ambiguous_identifiers:
            return
        existing = cls._identifier_index.get(token)
        if existing is None:
            cls._identifier_index[token] = canonical_id
            return
        if existing == canonical_id:
            return
        cls._identifier_index.pop(token, None)
        cls._ambiguous_identifiers.add(token)

    @classmethod
    def resolve_identifier(cls, identifier: str) -> str:
        token = cls._normalize_identifier(identifier)
        if token in cls._ambiguous_identifiers:
            raise ValueError(
                f"Ambiguous fix identifier '{identifier}'. Use canonical '<prefix>.<local_id>' form."
            )
        canonical_id = cls._identifier_index.get(token)
        if canonical_id is None:
            raise KeyError(identifier)
        return canonical_id

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
            for attr in (
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
            ):
                if hasattr(fix_cls, attr):
                    setattr(fix, attr, getattr(fix_cls, attr))
            fix.categories = list(getattr(fix, "categories", []) or [])
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

        prefix, local_id, canonical_id, aliases = cls._derive_namespace_and_local_id(fix_cls)
        if canonical_id in cls._registry:
            raise ValueError(f"Duplicate fix canonical id '{canonical_id}' (already registered)")

        setattr(fix_cls, "namespace_prefix", prefix)
        setattr(fix_cls, "local_id", local_id)
        setattr(fix_cls, "canonical_id", canonical_id)
        setattr(fix_cls, "aliases", aliases)

        cls._registry[canonical_id] = fix_cls
        cls._register_identifier(canonical_id, canonical_id)
        cls._register_identifier(local_id, canonical_id)
        for alias in aliases:
            cls._register_identifier(alias, canonical_id)
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
