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
    class _AliasFix(Fix):
        namespace_prefix = "test"
        local_id = "alias_fix"
        aliases = ["alias_lookup"]
        name = "Alias decorator fix"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    registered = register_fix(_AliasFix)
    assert registered is _AliasFix
    assert "test.alias_fix" in FixRegistry.registered_ids()
    assert FixRegistry.resolve_identifier("alias_lookup") == "test.alias_fix"
    assert FixRegistry.resolve_identifier("test.alias_lookup") == "test.alias_fix"


def test_registry_supports_fully_qualified_aliases_without_local_expansion():
    class _QualifiedAliasFix(Fix):
        namespace_prefix = "test"
        local_id = "qualified_alias_fix"
        aliases = ["other.explicit_lookup"]
        name = "Qualified alias fix"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    register_fix(_QualifiedAliasFix)
    assert FixRegistry.resolve_identifier("other.explicit_lookup") == "test.qualified_alias_fix"
    with pytest.raises(KeyError):
        FixRegistry.resolve_identifier("explicit_lookup")


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

    register_fix(_ExplicitLocalIdWinsFix)
    assert _ExplicitLocalIdWinsFix.canonical_id == "test.explicit_local"


def test_registry_local_id_derivation_uses_derived_when_local_missing():
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

    register_fix(_DerivedLocalIdFix)
    assert _DerivedLocalIdFix.canonical_id == "test.derived_local"


def test_registry_local_id_derivation_falls_back_to_class_name_snake_case():
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

    register_fix(FallbackFromClassNameFix)
    assert FallbackFromClassNameFix.canonical_id == "test.fallback_from_class_name"


def test_registry_resolves_canonical_and_local_aliases_for_known_fixes():
    assert (
        FixRegistry.resolve_identifier("woodpecker.normalize_tas_units_to_kelvin")
        == "woodpecker.normalize_tas_units_to_kelvin"
    )
    assert (
        FixRegistry.resolve_identifier("normalize_tas_units_to_kelvin")
        == "woodpecker.normalize_tas_units_to_kelvin"
    )
    assert (
        FixRegistry.resolve_identifier("tas_units_to_kelvin")
        == "woodpecker.normalize_tas_units_to_kelvin"
    )
    assert (
        FixRegistry.resolve_identifier("woodpecker.tas_units_to_kelvin")
        == "woodpecker.normalize_tas_units_to_kelvin"
    )


def test_registry_instantiate_returns_fix_for_canonical_id():
    fix = FixRegistry.instantiate("woodpecker.normalize_tas_units_to_kelvin")
    assert getattr(fix, "canonical_id", "") == "woodpecker.normalize_tas_units_to_kelvin"


def test_registry_instantiate_returns_fresh_instance_each_time():
    first = FixRegistry.instantiate("woodpecker.normalize_tas_units_to_kelvin")
    second = FixRegistry.instantiate("woodpecker.normalize_tas_units_to_kelvin")

    assert first is not second


def test_registry_instantiate_unknown_canonical_id_raises_clear_error():
    with pytest.raises(KeyError, match="Unknown fix canonical_id"):
        FixRegistry.instantiate("woodpecker.unknown_fix")


def test_registry_rejects_ambiguous_local_identifier():
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

    register_fix(_AmbiguousOne)
    register_fix(_AmbiguousTwo)
    with pytest.raises(ValueError, match="Ambiguous identifier"):
        FixRegistry.resolve_identifier("shared")
