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

    namespace_prefix: str
    local_id: str
    canonical_id: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScopedIdentifierResolution:
    """Result of resolving a possibly-partial identifier within a namespace scope.

    Produced by ``coerce_scoped_identifier()``.  ``identifier_set`` is ``None``
    when only a bare (non-qualified) id was available and no namespace prefix
    could be inferred.
    """

    canonical_id: str
    local_id: str
    namespace_prefix: str
    identifier_set: IdentifierSet | None


class IdentifierRules:
    """Stateless helpers for normalizing, validating, and building identifiers."""

    @staticmethod
    def normalize(value: object) -> str:
        """Return a stripped, lowercase string representation of *value*."""
        return str(value).strip().lower()

    @classmethod
    def validate_local_id(cls, label: str, value: str) -> None:
        """Raise ``ValueError`` if *value* is not a valid snake_case token."""
        if not _IDENTIFIER_PART_PATTERN.fullmatch(value):
            raise ValueError(
                f"Invalid {label} '{value}'. Expected lowercase snake_case identifier."
            )

    @classmethod
    def validate_canonical_id(cls, label: str, value: str) -> None:
        """Raise ``ValueError`` if *value* is not a valid ``<prefix>.<local_id>`` string."""
        parts = value.split(".")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid {label} '{value}'. Expected '<prefix>.<local_id>' with snake_case tokens."
            )
        namespace_prefix, local_id = parts
        cls.validate_local_id(f"{label} prefix", namespace_prefix)
        cls.validate_local_id(f"{label} local_id", local_id)

    @staticmethod
    def derive_local_id_from_name(name: str) -> str:
        """Convert a CamelCase class name to a snake_case local identifier.

        Strips trailing ``Fix`` or ``Plan`` suffixes before converting.
        """
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
        namespace_prefix: str,
        canonical_id: str,
        declared_aliases: object,
    ) -> tuple[str, ...]:
        """Expand *declared_aliases* into a deduplicated tuple of alias strings.

        Unqualified aliases are expanded to both the bare form and the
        ``<namespace_prefix>.<alias>`` qualified form.  Qualified aliases are
        validated but kept as-is.
        """
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
                candidates = [alias, f"{namespace_prefix}.{alias}"]

            for candidate in candidates:
                if candidate == canonical_id or candidate in seen:
                    continue
                seen.add(candidate)
                out_aliases.append(candidate)

        return tuple(out_aliases)

    @classmethod
    def build(
        cls,
        namespace_prefix: object,
        local_id: object,
        aliases: object = None,
    ) -> IdentifierSet:
        """Build a validated, normalized ``IdentifierSet``.

        Both *namespace_prefix* and *local_id* are normalized and validated
        as lowercase snake_case tokens before the canonical id is assembled.
        """
        normalized_prefix = cls.normalize(namespace_prefix)
        normalized_local_id = cls.normalize(local_id)

        cls.validate_local_id("namespace prefix", normalized_prefix)
        cls.validate_local_id("local_id", normalized_local_id)

        canonical_id = f"{normalized_prefix}.{normalized_local_id}"
        expanded_aliases = cls.expand_aliases(normalized_prefix, canonical_id, aliases)

        return IdentifierSet(
            namespace_prefix=normalized_prefix,
            local_id=normalized_local_id,
            canonical_id=canonical_id,
            aliases=expanded_aliases,
        )


class IdentifierResolver:
    """Bidirectional map from identifier tokens to canonical ids.

    Registration is incremental: call ``register()`` for each ``IdentifierSet``.
    Tokens that collide across different canonical ids are marked ambiguous and
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
        """Register all tokens from *identifier_set* (canonical id, local id, aliases)."""
        self._register_one(identifier_set.canonical_id, identifier_set.canonical_id)
        if include_local_id:
            self._register_one(identifier_set.local_id, identifier_set.canonical_id)
        for alias in identifier_set.aliases:
            self._register_one(alias, identifier_set.canonical_id)

    def resolve(self, identifier: str) -> str:
        """Return the canonical id for *identifier*.

        Raises ``ValueError`` if the token is ambiguous, or ``KeyError`` if
        it is not registered.
        """
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
    """Normalize and resolve a possibly-partial identifier within a namespace scope.

    Accepts any combination of *canonical_id*, *local_id*, and *namespace_prefix*
    and returns a fully populated ``ScopedIdentifierResolution``.  When both a
    namespace prefix and a local id are available, a validated ``IdentifierSet``
    is constructed and attached to the result.

    Precedence for inferring missing pieces:
    - A dotted *canonical_id* is split to fill in missing prefix / local_id.
    - A plain *canonical_id* with no dots is treated as a bare local_id when
      *local_id* is not provided.
    """
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
        normalized_prefix = identifier_set.namespace_prefix
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
    """Build a resolver pre-populated from a list of identifier sets.

    Useful for stores that need duplicate detection, shorthand lookups, and
    canonical identifier resolution via a single shared resolver.
    """
    resolver = IdentifierResolver()
    for identifier_set in identifier_sets:
        resolver.register(identifier_set, include_local_id=include_local_id)
    return resolver
