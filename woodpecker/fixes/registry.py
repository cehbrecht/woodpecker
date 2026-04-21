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
    _identifier_index: Dict[str, str] = {}
    _ambiguous_identifiers: set[str] = set()

    @staticmethod
    def _normalize_identifier(identifier: str) -> str:
        return str(identifier).strip().upper()

    @classmethod
    def _derive_namespace_and_local_id(
        cls, fix: Any, fix_cls: Type[Any]
    ) -> tuple[str, str, str, list[str]]:
        raw_code = cls._normalize_identifier(str(getattr(fix, "code", "") or ""))
        explicit_prefix = cls._normalize_identifier(str(getattr(fix, "namespace_prefix", "") or ""))
        explicit_local = cls._normalize_identifier(str(getattr(fix, "local_id", "") or ""))

        prefix = explicit_prefix
        local_id = explicit_local
        aliases = [cls._normalize_identifier(item) for item in (getattr(fix, "aliases", []) or [])]

        if prefix and local_id:
            pass
        elif "." in raw_code:
            prefix, local_id = raw_code.split(".", 1)
        elif "_" in raw_code:
            prefix, local_id = raw_code.split("_", 1)
        elif raw_code and prefix:
            local_id = raw_code
        elif raw_code:
            # Fallback for simple direct-use fixes without explicit namespace metadata.
            prefix = "CORE"
            local_id = raw_code
        else:
            auto = cls._normalize_identifier(fix_cls.__name__)
            match = re.search(r"(?:_|)(\d{3,})$", auto)
            local_id = match.group(1) if match else auto
            prefix = explicit_prefix or "CORE"

        canonical_id = f"{prefix}.{local_id}"
        if raw_code:
            aliases.append(raw_code)
        if canonical_id != raw_code:
            aliases.append(canonical_id)
            aliases.append(f"{prefix}_{local_id}")
        aliases.append(local_id)

        out_aliases: list[str] = []
        seen: set[str] = set()
        for alias in aliases:
            norm = cls._normalize_identifier(alias)
            if not norm or norm == canonical_id or norm in seen:
                continue
            seen.add(norm)
            out_aliases.append(norm)

        return prefix, local_id, canonical_id, out_aliases

    @classmethod
    def _register_identifier(cls, identifier: str, code: str) -> None:
        token = cls._normalize_identifier(identifier)
        if not token:
            return
        if token in cls._ambiguous_identifiers:
            return
        existing = cls._identifier_index.get(token)
        if existing is None:
            cls._identifier_index[token] = code
            return
        if existing == code:
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
        code = cls._identifier_index.get(token)
        if code is None:
            raise KeyError(identifier)
        return code

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
        code = cls._normalize_identifier(getattr(fix, "code", None) or "")

        if code in cls._registry:
            raise ValueError(f"Duplicate fix code '{code}' (already registered)")

        prefix, local_id, canonical_id, aliases = cls._derive_namespace_and_local_id(fix, fix_cls)
        setattr(fix_cls, "namespace_prefix", prefix)
        setattr(fix_cls, "local_id", local_id)
        setattr(fix_cls, "canonical_id", canonical_id)
        setattr(fix_cls, "aliases", aliases)

        cls._registry[code] = fix_cls
        cls._register_identifier(code, code)
        cls._register_identifier(canonical_id, code)
        cls._register_identifier(local_id, code)
        for alias in aliases:
            cls._register_identifier(alias, code)
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
