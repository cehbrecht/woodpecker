import pytest

from woodpecker.fixes.registry import Fix, FixRegistry, GroupFix, register_fix
from woodpecker.identifiers import IdentifierResolver


def _snapshot_registry_state():
    return (
        dict(FixRegistry._registry),
        dict(FixRegistry._resolver._identifier_index),
        set(FixRegistry._resolver._ambiguous_identifiers),
    )


def _restore_registry_state(snapshot):
    registry_snapshot, index_snapshot, ambiguous_snapshot = snapshot
    FixRegistry._registry = registry_snapshot
    FixRegistry._resolver = IdentifierResolver(
        index=index_snapshot,
        ambiguous_identifiers=ambiguous_snapshot,
    )


def test_registry_discovers_builtins():
    fixes = FixRegistry.discover()
    ids = {fix.canonical_id for fix in fixes}

    # Common non-project fix family (always available in core package).
    assert "woodpecker.normalize_tas_units_to_kelvin" in ids
    assert "woodpecker.ensure_latitude_is_increasing" in ids
    assert "woodpecker.remove_coordinate_fill_value_encodings" in ids


def test_group_fix_is_group_fix_instance():
    fixes = FixRegistry.discover()
    maybe_group = [f for f in fixes if isinstance(f, GroupFix)]
    if maybe_group:
        assert isinstance(maybe_group[0], GroupFix)


def test_registry_rejects_invalid_local_identifier_pattern():
    with pytest.raises(ValueError, match="Invalid local_id"):

        class _InvalidCodeFix:
            local_id = "bad-id"
            name = "Invalid code"
            description = ""
            categories = ["metadata"]
            priority = 10
            dataset = None

        FixRegistry.register(_InvalidCodeFix)


def test_registry_rejects_missing_name():
    with pytest.raises(ValueError, match="non-empty 'name'"):

        class _MissingNameFix:
            name = ""
            description = ""
            categories = ["metadata"]
            priority = 10
            dataset = None

        FixRegistry.register(_MissingNameFix)


def test_register_fix_decorator_alias_registers_class():
    snapshot = _snapshot_registry_state()

    class _AliasFix(Fix):
        namespace_prefix = "test"
        local_id = "alias_fix"
        aliases = ["alias_lookup"]
        name = "Alias decorator fix"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    try:
        registered = register_fix(_AliasFix)
        assert registered is _AliasFix
        assert "test.alias_fix" in FixRegistry.registered_ids()
        assert FixRegistry.resolve_identifier("alias_lookup") == "test.alias_fix"
        assert FixRegistry.resolve_identifier("test.alias_lookup") == "test.alias_fix"
    finally:
        _restore_registry_state(snapshot)


def test_registry_supports_fully_qualified_aliases_without_local_expansion():
    snapshot = _snapshot_registry_state()

    class _QualifiedAliasFix(Fix):
        namespace_prefix = "test"
        local_id = "qualified_alias_fix"
        aliases = ["other.explicit_lookup"]
        name = "Qualified alias fix"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    try:
        register_fix(_QualifiedAliasFix)
        assert FixRegistry.resolve_identifier("other.explicit_lookup") == "test.qualified_alias_fix"
        with pytest.raises(KeyError):
            FixRegistry.resolve_identifier("explicit_lookup")
    finally:
        _restore_registry_state(snapshot)


def test_registry_rejects_invalid_alias_syntax():
    with pytest.raises(ValueError, match="Invalid alias"):

        class _InvalidAliasFix(Fix):
            namespace_prefix = "test"
            local_id = "invalid_alias_fix"
            aliases = ["bad-alias"]
            name = "Invalid alias fix"
            description = ""
            categories = ["metadata"]
            priority = 10
            dataset = None

        FixRegistry.register(_InvalidAliasFix)


def test_registry_local_id_derivation_precedence_explicit_over_derived():
    snapshot = _snapshot_registry_state()

    class _ExplicitLocalIdWinsFix(Fix):
        namespace_prefix = "test"
        local_id = "explicit_local"
        name = "Explicit local id wins"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

        @staticmethod
        def derived_local_id() -> str:
            return "derived_local"

    try:
        register_fix(_ExplicitLocalIdWinsFix)
        assert _ExplicitLocalIdWinsFix.canonical_id == "test.explicit_local"
    finally:
        _restore_registry_state(snapshot)


def test_registry_local_id_derivation_uses_derived_when_local_missing():
    snapshot = _snapshot_registry_state()

    class _DerivedLocalIdFix(Fix):
        namespace_prefix = "test"
        name = "Derived local id"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

        @staticmethod
        def derived_local_id() -> str:
            return "derived_local"

    try:
        register_fix(_DerivedLocalIdFix)
        assert _DerivedLocalIdFix.canonical_id == "test.derived_local"
    finally:
        _restore_registry_state(snapshot)


def test_registry_local_id_derivation_falls_back_to_class_name_snake_case():
    snapshot = _snapshot_registry_state()

    class FallbackFromClassNameFix:
        namespace_prefix = "test"
        name = "Fallback local id"

        def matches(self, dataset):
            return True

        def check(self, dataset):
            return []

        def apply(self, dataset, dry_run=True):
            return False

        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    try:
        register_fix(FallbackFromClassNameFix)
        assert FallbackFromClassNameFix.canonical_id == "test.fallback_from_class_name"
    finally:
        _restore_registry_state(snapshot)


def test_registry_resolves_canonical_and_local_aliases_for_known_fixes():
    assert (
        FixRegistry.resolve_identifier("woodpecker.normalize_tas_units_to_kelvin")
        == "woodpecker.normalize_tas_units_to_kelvin"
    )
    assert (
        FixRegistry.resolve_identifier("normalize_tas_units_to_kelvin")
        == "woodpecker.normalize_tas_units_to_kelvin"
    )


def test_registry_rejects_ambiguous_local_identifier():
    snapshot = _snapshot_registry_state()

    class _AmbiguousOne(Fix):
        namespace_prefix = "alpha"
        local_id = "shared"
        name = "Ambiguous One"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    class _AmbiguousTwo(Fix):
        namespace_prefix = "beta"
        local_id = "shared"
        name = "Ambiguous Two"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    try:
        register_fix(_AmbiguousOne)
        register_fix(_AmbiguousTwo)
        with pytest.raises(ValueError, match="Ambiguous identifier"):
            FixRegistry.resolve_identifier("shared")
    finally:
        _restore_registry_state(snapshot)
