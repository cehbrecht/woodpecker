import pytest

from woodpecker.fixes.registry import Fix, FixRegistry, GroupFix, register_fix


def test_registry_discovers_builtins():
    fixes = FixRegistry.discover()
    codes = {fix.code for fix in fixes}

    # Common non-project fix family (always available in core package).
    assert "COMMON_0001" in codes
    assert "COMMON_0002" in codes
    assert "COMMON_0003" in codes


def test_group_fix_is_group_fix_instance():
    fixes = FixRegistry.discover()
    maybe_group = [f for f in fixes if isinstance(f, GroupFix)]
    if maybe_group:
        assert isinstance(maybe_group[0], GroupFix)


def test_registry_rejects_invalid_code_pattern():
    with pytest.raises(ValueError, match="invalid code"):

        class _InvalidCodeFix:
            code = "bad-code"
            name = "Invalid code"
            description = ""
            categories = ["metadata"]
            priority = 10
            dataset = None

        FixRegistry.register(_InvalidCodeFix)


def test_registry_rejects_missing_name():
    with pytest.raises(ValueError, match="non-empty 'name'"):

        class _MissingNameFix:
            code = "ABCD01"
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
        code = "ALIAS_0001"
        name = "Alias decorator fix"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    try:
        registered = register_fix(_AliasFix)
        assert registered is _AliasFix
        assert "ALIAS_0001" in FixRegistry.registered_codes()
        assert FixRegistry.resolve_identifier("alias.0001") == "ALIAS_0001"
    finally:
        FixRegistry._registry = registry_snapshot
        FixRegistry._identifier_index = identifier_snapshot
        FixRegistry._ambiguous_identifiers = ambiguous_snapshot


def test_registry_resolves_canonical_and_legacy_aliases_for_known_fixes():
    assert FixRegistry.resolve_identifier("COMMON_0001") == "COMMON_0001"
    assert FixRegistry.resolve_identifier("common.0001") == "COMMON_0001"


def test_registry_rejects_ambiguous_local_identifier():
    registry_snapshot = dict(FixRegistry._registry)
    identifier_snapshot = dict(FixRegistry._identifier_index)
    ambiguous_snapshot = set(FixRegistry._ambiguous_identifiers)

    class _AmbiguousOne(Fix):
        code = "ALIAS_0010"
        namespace_prefix = "alpha"
        local_id = "shared"
        name = "Ambiguous One"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    class _AmbiguousTwo(Fix):
        code = "ALIAS_0020"
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
