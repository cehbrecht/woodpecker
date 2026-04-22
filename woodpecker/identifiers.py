from __future__ import annotations

import re
from dataclasses import dataclass

_IDENTIFIER_PART_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


@dataclass(frozen=True)
class IdentifierSet:
    prefix: str
    local_id: str
    canonical_id: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScopedIdentifierResolution:
    canonical_id: str
    local_id: str
    namespace_prefix: str
    identifier_set: IdentifierSet | None


class IdentifierRules:
    @staticmethod
    def normalize(value: object) -> str:
        return str(value).strip().lower()

    @classmethod
    def validate_local_id(cls, label: str, value: str) -> None:
        if not _IDENTIFIER_PART_PATTERN.fullmatch(value):
            raise ValueError(
                f"Invalid {label} '{value}'. Expected lowercase snake_case identifier."
            )

    @classmethod
    def validate_canonical_id(cls, label: str, value: str) -> None:
        parts = value.split(".")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid {label} '{value}'. Expected '<prefix>.<local_id>' with snake_case tokens."
            )
        prefix, local_id = parts
        cls.validate_local_id(f"{label} prefix", prefix)
        cls.validate_local_id(f"{label} local_id", local_id)

    @staticmethod
    def derive_local_id_from_name(name: str) -> str:
        class_name = str(name or "")
        for suffix in ("Fix", "Plan"):
            if class_name.endswith(suffix):
                class_name = class_name[: -len(suffix)]
                break

        first = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", class_name)
        second = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first)
        return re.sub(r"__+", "_", second).strip("_").lower()

    @classmethod
    def expand_aliases(
        cls,
        prefix: str,
        canonical_id: str,
        declared_aliases: object,
    ) -> tuple[str, ...]:
        if declared_aliases is None:
            raw_aliases: list[object] = []
        elif isinstance(declared_aliases, str):
            raw_aliases = [declared_aliases]
        elif isinstance(declared_aliases, (list, tuple, set)):
            raw_aliases = list(declared_aliases)
        else:
            raise ValueError("Invalid aliases declaration. Expected a string or list of strings.")

        out_aliases: list[str] = []
        seen: set[str] = set()
        for item in raw_aliases:
            alias = cls.normalize(item)
            if not alias:
                continue

            if "." in alias:
                cls.validate_canonical_id("alias", alias)
                candidates = [alias]
            else:
                cls.validate_local_id("alias", alias)
                candidates = [alias, f"{prefix}.{alias}"]

            for candidate in candidates:
                if candidate == canonical_id or candidate in seen:
                    continue
                seen.add(candidate)
                out_aliases.append(candidate)

        return tuple(out_aliases)

    @classmethod
    def build(
        cls,
        prefix: object,
        local_id: object,
        aliases: object = None,
    ) -> IdentifierSet:
        normalized_prefix = cls.normalize(prefix)
        normalized_local_id = cls.normalize(local_id)

        cls.validate_local_id("namespace prefix", normalized_prefix)
        cls.validate_local_id("local_id", normalized_local_id)

        canonical_id = f"{normalized_prefix}.{normalized_local_id}"
        expanded_aliases = cls.expand_aliases(normalized_prefix, canonical_id, aliases)

        return IdentifierSet(
            prefix=normalized_prefix,
            local_id=normalized_local_id,
            canonical_id=canonical_id,
            aliases=expanded_aliases,
        )


class IdentifierResolver:
    def __init__(
        self,
        index: dict[str, str] | None = None,
        ambiguous_identifiers: set[str] | None = None,
    ) -> None:
        self._identifier_index: dict[str, str] = index if index is not None else {}
        self._ambiguous_identifiers: set[str] = (
            ambiguous_identifiers if ambiguous_identifiers is not None else set()
        )

    def _register_one(self, identifier: str, canonical_id: str) -> None:
        token = IdentifierRules.normalize(identifier)
        if not token:
            return
        if token in self._ambiguous_identifiers:
            return

        existing = self._identifier_index.get(token)
        if existing is None:
            self._identifier_index[token] = canonical_id
            return
        if existing == canonical_id:
            return

        self._identifier_index.pop(token, None)
        self._ambiguous_identifiers.add(token)

    def register(self, identifier_set: IdentifierSet, include_local_id: bool = True) -> None:
        self._register_one(identifier_set.canonical_id, identifier_set.canonical_id)
        if include_local_id:
            self._register_one(identifier_set.local_id, identifier_set.canonical_id)
        for alias in identifier_set.aliases:
            self._register_one(alias, identifier_set.canonical_id)

    def resolve(self, identifier: str) -> str:
        token = IdentifierRules.normalize(identifier)
        if token in self._ambiguous_identifiers:
            raise ValueError(
                f"Ambiguous identifier '{identifier}'. Use canonical '<prefix>.<local_id>' form."
            )

        canonical_id = self._identifier_index.get(token)
        if canonical_id is None:
            raise KeyError(identifier)
        return canonical_id


def coerce_scoped_identifier(
    *,
    canonical_id: object,
    local_id: object,
    namespace_prefix: object,
    canonical_label: str,
) -> ScopedIdentifierResolution:
    normalized_canonical_id = IdentifierRules.normalize(canonical_id)
    normalized_local_id = IdentifierRules.normalize(local_id)
    normalized_prefix = IdentifierRules.normalize(namespace_prefix)

    if normalized_canonical_id and "." in normalized_canonical_id:
        IdentifierRules.validate_canonical_id(canonical_label, normalized_canonical_id)
        parsed_prefix, parsed_local_id = normalized_canonical_id.split(".", 1)
        if not normalized_prefix:
            normalized_prefix = parsed_prefix
        if not normalized_local_id:
            normalized_local_id = parsed_local_id
    elif normalized_canonical_id and not normalized_local_id:
        normalized_local_id = normalized_canonical_id

    identifier_set: IdentifierSet | None = None
    if normalized_prefix and normalized_local_id:
        identifier_set = IdentifierRules.build(normalized_prefix, normalized_local_id)
        normalized_prefix = identifier_set.prefix
        normalized_local_id = identifier_set.local_id
        normalized_canonical_id = identifier_set.canonical_id

    return ScopedIdentifierResolution(
        canonical_id=normalized_canonical_id,
        local_id=normalized_local_id,
        namespace_prefix=normalized_prefix,
        identifier_set=identifier_set,
    )


def build_identifier_resolver(
    identifier_sets: list[IdentifierSet], include_local_id: bool = True
) -> IdentifierResolver:
    """Build a resolver pre-populated from identifier sets.

    This utility is useful for stores that need duplicate detection, shorthand
    lookups, and canonical identifier resolution via one shared resolver model.
    """

    resolver = IdentifierResolver()
    for identifier_set in identifier_sets:
        resolver.register(identifier_set, include_local_id=include_local_id)
    return resolver
