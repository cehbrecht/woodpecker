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

    @property
    def local_id(self) -> str:
        """Compatibility alias for ``suffix``."""
        return self.suffix

    @property
    def namespace_prefix(self) -> str:
        """Compatibility alias for ``prefix``."""
        return self.prefix

    @property
    def canonical_id(self) -> str:
        """Compatibility alias for canonical ``id``."""
        return self.id


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

    @property
    def local_id(self) -> str:
        """Compatibility alias for ``suffix``."""
        return self.suffix

    @property
    def canonical_id(self) -> str:
        """Compatibility alias for canonical ``id``."""
        return self.id

    @property
    def namespace_prefix(self) -> str:
        """Compatibility alias for ``prefix``."""
        return self.prefix


class IdentifierRules:
    """Stateless helpers for normalizing, validating, and building identifiers."""

    @staticmethod
    def normalize(value: object) -> str:
        """Return a stripped, lowercase string representation of *value*."""
        return str(value).strip().lower()

    @classmethod
    def validate_suffix(cls, label: str, value: str) -> None:
        """Raise ``ValueError`` if *value* is not a valid snake_case token."""
        if not _IDENTIFIER_PART_PATTERN.fullmatch(value):
            raise ValueError(
                f"Invalid {label} '{value}'. Expected lowercase snake_case identifier."
            )

    validate_local_id = validate_suffix

    @classmethod
    def validate_canonical_id(cls, label: str, value: str) -> None:
        """Raise ``ValueError`` if *value* is not a valid ``<prefix>.<suffix>`` string."""
        parts = value.split(".")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid {label} '{value}'. Expected '<prefix>.<suffix>' with snake_case tokens."
            )
        namespace_prefix, suffix = parts
        cls.validate_suffix(f"{label} prefix", namespace_prefix)
        cls.validate_suffix(f"{label} suffix", suffix)

    @staticmethod
    def derive_suffix_from_name(name: str) -> str:
        """Convert a CamelCase class name to a snake_case suffix.

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

    derive_local_id_from_name = derive_suffix_from_name

    @classmethod
    def expand_aliases(
        cls,
        prefix: str | None = None,
        id: str | None = None,
        declared_aliases: object = None,
        **kwargs: object,
    ) -> tuple[str, ...]:
        """Expand *declared_aliases* into a deduplicated tuple of alias strings.

        Unqualified aliases are expanded to both the bare form and the
        ``<prefix>.<alias>`` qualified form.  Qualified aliases are
        validated but kept as-is.
        """
        if prefix is None and "namespace_prefix" in kwargs:
            prefix = str(kwargs.pop("namespace_prefix"))
        if id is None and "canonical_id" in kwargs:
            id = str(kwargs.pop("canonical_id"))
        if kwargs:
            unknown = ", ".join(sorted(kwargs))
            raise TypeError(f"Unknown alias field(s): {unknown}")

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
                cls.validate_canonical_id("alias", alias)
                candidates = [alias]
            else:
                cls.validate_suffix("alias", alias)
                candidates = [alias, f"{normalized_prefix}.{alias}"]

            for candidate in candidates:
                if candidate == normalized_id or candidate in seen:
                    continue
                seen.add(candidate)
                out_aliases.append(candidate)

        return tuple(out_aliases)

    @classmethod
    def build(
        cls,
        prefix: object = None,
        suffix: object = None,
        aliases: object = None,
        **kwargs: object,
    ) -> IdentifierSet:
        """Build a validated, normalized ``IdentifierSet``.

        Both *prefix* and *suffix* are normalized and validated
        as lowercase snake_case tokens before the canonical id is assembled.
        """
        if prefix is None and "namespace_prefix" in kwargs:
            prefix = kwargs.pop("namespace_prefix")
        if suffix is None and "local_id" in kwargs:
            suffix = kwargs.pop("local_id")
        if kwargs:
            unknown = ", ".join(sorted(kwargs))
            raise TypeError(f"Unknown identifier field(s): {unknown}")

        normalized_prefix = cls.normalize(prefix)
        normalized_suffix = cls.normalize(suffix)

        cls.validate_suffix("prefix", normalized_prefix)
        cls.validate_suffix("suffix", normalized_suffix)

        canonical_id = f"{normalized_prefix}.{normalized_suffix}"
        expanded_aliases = cls.expand_aliases(normalized_prefix, canonical_id, aliases)

        return IdentifierSet(
            prefix=normalized_prefix,
            suffix=normalized_suffix,
            id=canonical_id,
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

    def register(self, identifier_set: IdentifierSet, include_suffix: bool = True) -> None:
        """Register all tokens from *identifier_set* (id, suffix, aliases)."""
        self._register_one(identifier_set.id, identifier_set.id)
        if include_suffix:
            self._register_one(identifier_set.suffix, identifier_set.id)
        for alias in identifier_set.aliases:
            self._register_one(alias, identifier_set.id)

    def resolve(self, identifier: str) -> str:
        """Return the canonical id for *identifier*.

        Raises ``ValueError`` if the token is ambiguous, or ``KeyError`` if
        it is not registered.
        """
        token = IdentifierRules.normalize(identifier)
        if token in self._ambiguous_identifiers:
            raise ValueError(
                f"Ambiguous identifier '{identifier}'. Use canonical '<prefix>.<suffix>' form."
            )

        canonical_id = self._identifier_index.get(token)
        if canonical_id is None:
            raise KeyError(identifier)
        return canonical_id


def coerce_scoped_identifier(
    *,
    suffix: object = None,
    id: object = None,
    prefix: object = None,
    canonical_label: str,
    local_id: object = None,
    canonical_id: object = None,
    namespace_prefix: object = None,
) -> ScopedIdentifierResolution:
    """Normalize and resolve a possibly-partial identifier within a prefix scope.

    Accepts any combination of canonical *id*, *suffix*, and *prefix*
    and returns a fully populated ``ScopedIdentifierResolution``.  When both a
    prefix and suffix are available, a validated ``IdentifierSet`` is attached.

    Precedence for inferring missing pieces:
    - A dotted *id* is split to fill in missing prefix / suffix.
    - A plain *id* with no dots is treated as a bare suffix when *suffix* is not provided.
    """
    raw_id = id if id is not None else canonical_id
    raw_prefix = prefix if prefix is not None else namespace_prefix
    raw_suffix = suffix if suffix is not None else local_id

    normalized_canonical_id = IdentifierRules.normalize(raw_id)
    normalized_suffix = IdentifierRules.normalize(raw_suffix)
    normalized_prefix = IdentifierRules.normalize(raw_prefix)

    if normalized_canonical_id and "." in normalized_canonical_id:
        IdentifierRules.validate_canonical_id(canonical_label, normalized_canonical_id)
        parsed_prefix, parsed_suffix = normalized_canonical_id.split(".", 1)
        if not normalized_prefix:
            normalized_prefix = parsed_prefix
        if not normalized_suffix:
            normalized_suffix = parsed_suffix
    elif normalized_canonical_id and not normalized_suffix:
        normalized_suffix = normalized_canonical_id

    identifier_set: IdentifierSet | None = None
    if normalized_prefix and normalized_suffix:
        identifier_set = IdentifierRules.build(normalized_prefix, normalized_suffix)
        normalized_prefix = identifier_set.prefix
        normalized_suffix = identifier_set.suffix
        normalized_canonical_id = identifier_set.id

    return ScopedIdentifierResolution(
        id=normalized_canonical_id,
        suffix=normalized_suffix,
        prefix=normalized_prefix,
        identifier_set=identifier_set,
    )


def build_identifier_resolver(
    identifier_sets: list[IdentifierSet], include_suffix: bool = True
) -> IdentifierResolver:
    """Build a resolver pre-populated from a list of identifier sets.

    Useful for stores that need duplicate detection, shorthand lookups, and
    canonical identifier resolution via a single shared resolver.
    """
    resolver = IdentifierResolver()
    for identifier_set in identifier_sets:
        resolver.register(identifier_set, include_suffix=include_suffix)
    return resolver
