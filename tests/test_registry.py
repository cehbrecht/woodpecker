import pytest

from woodpecker.fixes.registry import Fix, FixRegistry, GroupFix, register_fix


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
    with pytest.raises(ValueError, match="Invalid fix local_id"):

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
    registry_snapshot = dict(FixRegistry._registry)
    identifier_snapshot = dict(FixRegistry._identifier_index)
    ambiguous_snapshot = set(FixRegistry._ambiguous_identifiers)

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
    finally:
        FixRegistry._registry = registry_snapshot
        FixRegistry._identifier_index = identifier_snapshot
        FixRegistry._ambiguous_identifiers = ambiguous_snapshot


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
    registry_snapshot = dict(FixRegistry._registry)
    identifier_snapshot = dict(FixRegistry._identifier_index)
    ambiguous_snapshot = set(FixRegistry._ambiguous_identifiers)

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
        with pytest.raises(ValueError, match="Ambiguous fix identifier"):
            FixRegistry.resolve_identifier("shared")
    finally:
        FixRegistry._registry = registry_snapshot
        FixRegistry._identifier_index = identifier_snapshot
        FixRegistry._ambiguous_identifiers = ambiguous_snapshot
