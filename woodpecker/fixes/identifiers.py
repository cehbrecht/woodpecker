from __future__ import annotations

import re
from dataclasses import dataclass

_IDENTIFIER_PART_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


@dataclass(frozen=True)
class IdentifierSet:
    """Resolved identifier model for a single named entity (fix or plan).

    All fields are normalized to lowercase snake_case at construction time.
    Use ``IdentifierRules.build()`` rather than constructing directly.
    """

    prefix: str
    suffix: str
    id: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScopedIdentifierResolution:
    """Result of resolving a possibly-partial identifier within a prefix scope.

    Produced by ``coerce_scoped_identifier()``.  ``identifier_set`` is ``None``
    when only a bare id was available and no prefix could be inferred.
    """

    id: str
    suffix: str
    prefix: str
    identifier_set: IdentifierSet | None


class IdentifierRules:
    """Stateless helpers for normalizing, validating, and building identifiers."""

    @staticmethod
    def normalize(value: object) -> str:
        """Return a stripped, lowercase string representation of *value*."""
        return str(value).strip().lower()

    @classmethod
    def validate_suffix(cls, label: str, value: str) -> None:
        """Raise ``ValueError`` if *value* is not a valid safe identifier token."""
        if not value.isascii():
            raise ValueError(f"Invalid {label} '{value}'. Expected ASCII characters only.")
        if not _IDENTIFIER_PART_PATTERN.fullmatch(value):
            raise ValueError(
                f"Invalid {label} '{value}'. Expected lowercase snake_case identifier "
                "(ASCII letters/digits/underscore only; no spaces or special characters)."
            )

    @classmethod
    def validate_id(cls, label: str, value: str) -> None:
        """Raise ``ValueError`` if *value* is not a valid ``<prefix>.<suffix>`` string."""
        if not value.isascii():
            raise ValueError(f"Invalid {label} '{value}'. Expected ASCII characters only.")
        parts = value.split(".")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid {label} '{value}'. Expected '<prefix>.<suffix>' with snake_case tokens."
            )
        prefix, suffix = parts
        cls.validate_suffix(f"{label} prefix", prefix)
        cls.validate_suffix(f"{label} suffix", suffix)

    @staticmethod
    def derive_suffix_from_name(name: str) -> str:
        """Convert a CamelCase class name to a snake_case suffix.

        Strips trailing ``Plan`` suffixes before converting.
        """
        class_name = str(name or "")
        if class_name.endswith("Plan"):
            class_name = class_name[: -len("Plan")]

        first = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", class_name)
        second = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first)
        return re.sub(r"__+", "_", second).strip("_").lower()

    @classmethod
    def expand_aliases(
        cls,
        prefix: str,
        id: str,
        declared_aliases: object = None,
    ) -> tuple[str, ...]:
        """Expand *declared_aliases* into a deduplicated tuple of alias strings.

        Unqualified aliases are expanded to ``<prefix>.<alias>``.
        Qualified aliases are validated but kept as-is.
        """
        normalized_prefix = cls.normalize(prefix)
        normalized_id = cls.normalize(id)

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
                cls.validate_id("alias", alias)
                candidates = [alias]
            else:
                cls.validate_suffix("alias", alias)
                candidates = [f"{normalized_prefix}.{alias}"]

            for candidate in candidates:
                if candidate == normalized_id or candidate in seen:
                    continue
                seen.add(candidate)
                out_aliases.append(candidate)

        return tuple(out_aliases)

    @classmethod
    def build(
        cls,
        prefix: object,
        suffix: object,
        aliases: object = None,
    ) -> IdentifierSet:
        """Build a validated, normalized ``IdentifierSet``.

        Both *prefix* and *suffix* are normalized and validated
        as lowercase snake_case tokens before the id is assembled.
        """
        normalized_prefix = cls.normalize(prefix)
        normalized_suffix = cls.normalize(suffix)

        cls.validate_suffix("prefix", normalized_prefix)
        cls.validate_suffix("suffix", normalized_suffix)

        resolved_id = f"{normalized_prefix}.{normalized_suffix}"
        expanded_aliases = cls.expand_aliases(normalized_prefix, resolved_id, aliases)

        return IdentifierSet(
            prefix=normalized_prefix,
            suffix=normalized_suffix,
            id=resolved_id,
            aliases=expanded_aliases,
        )


class IdentifierResolver:
    """Bidirectional map from identifier tokens to ids.

    Registration is incremental: call ``register()`` for each ``IdentifierSet``.
    Tokens that collide across different ids are marked ambiguous and
    will raise ``ValueError`` on ``resolve()``.
    """

    def __init__(
        self,
        index: dict[str, str] | None = None,
        ambiguous_identifiers: set[str] | None = None,
    ) -> None:
        self._identifier_index: dict[str, str] = index if index is not None else {}
        self._ambiguous_identifiers: set[str] = (
            ambiguous_identifiers if ambiguous_identifiers is not None else set()
        )

    def _register_one(self, identifier: str, resolved_id: str) -> None:
        token = IdentifierRules.normalize(identifier)
        if not token:
            return
        if token in self._ambiguous_identifiers:
            return

        existing = self._identifier_index.get(token)
        if existing is None:
            self._identifier_index[token] = resolved_id
            return
        if existing == resolved_id:
            return

        self._identifier_index.pop(token, None)
        self._ambiguous_identifiers.add(token)

    def register(self, identifier_set: IdentifierSet) -> None:
        """Register tokens from *identifier_set* (id and aliases)."""
        self._register_one(identifier_set.id, identifier_set.id)
        for alias in identifier_set.aliases:
            self._register_one(alias, identifier_set.id)

    def resolve(self, identifier: str) -> str:
        """Return the id for *identifier*.

        Raises ``ValueError`` if the token is ambiguous, or ``KeyError`` if
        it is not registered.
        """
        token = IdentifierRules.normalize(identifier)
        if token in self._ambiguous_identifiers:
            raise ValueError(
                f"Ambiguous identifier '{identifier}'. Use complete '<prefix>.<suffix>' form."
            )

        resolved_id = self._identifier_index.get(token)
        if resolved_id is None:
            raise KeyError(identifier)
        return resolved_id


def coerce_scoped_identifier(
    *,
    suffix: object,
    id: object,
    prefix: object,
    id_label: str,
) -> ScopedIdentifierResolution:
    """Normalize and resolve a possibly-partial identifier within a prefix scope.

    Accepts any combination of *id*, *suffix*, and *prefix*
    and returns a fully populated ``ScopedIdentifierResolution``.  When both a
    prefix and suffix are available, a validated ``IdentifierSet`` is attached.

    Rules:
    - When *id* is provided, it must be complete (``prefix.suffix``).
    - Optional *prefix* and *suffix* must match the parsed *id* parts when provided.
    - Without *id*, both *prefix* and *suffix* are required to build an identifier.
    """
    raw_id = id
    raw_prefix = prefix
    raw_suffix = suffix

    normalized_id = IdentifierRules.normalize(raw_id)
    normalized_suffix = IdentifierRules.normalize(raw_suffix)
    normalized_prefix = IdentifierRules.normalize(raw_prefix)

    if normalized_id:
        if "." not in normalized_id:
            raise ValueError(
                f"Invalid {id_label} '{normalized_id}'. "
                "Expected '<prefix>.<suffix>' with snake_case tokens."
            )
        IdentifierRules.validate_id(id_label, normalized_id)
        parsed_prefix, parsed_suffix = normalized_id.split(".", 1)
        if normalized_prefix and normalized_prefix != parsed_prefix:
            raise ValueError(f"{id_label} prefix does not match id prefix")
        if normalized_suffix and normalized_suffix != parsed_suffix:
            raise ValueError(f"{id_label} suffix does not match id suffix")
        normalized_prefix = parsed_prefix
        normalized_suffix = parsed_suffix

    identifier_set: IdentifierSet | None = None
    if normalized_prefix and normalized_suffix:
        identifier_set = IdentifierRules.build(normalized_prefix, normalized_suffix)
        normalized_prefix = identifier_set.prefix
        normalized_suffix = identifier_set.suffix
        normalized_id = identifier_set.id
    elif not normalized_id and (normalized_prefix or normalized_suffix):
        raise ValueError(f"{id_label} requires both prefix and suffix when id is not provided")

    return ScopedIdentifierResolution(
        id=normalized_id,
        suffix=normalized_suffix,
        prefix=normalized_prefix,
        identifier_set=identifier_set,
    )


def build_identifier_resolver(identifier_sets: list[IdentifierSet]) -> IdentifierResolver:
    """Build a resolver pre-populated from a list of identifier sets.

    Useful for stores that need duplicate detection and id/alias resolution
    via a single shared resolver.
    """
    resolver = IdentifierResolver()
    for identifier_set in identifier_sets:
        resolver.register(identifier_set)
    return resolver
