import pytest

from woodpecker.fixes.labels import Labels
from woodpecker.fixes.registry import FixFunction, FixFunctionRegistry, register_fix_function


def test_registry_discovers_builtins():
    fixes = FixFunctionRegistry.discover()
    ids = {fix.id for fix in fixes}

    # Common non-project fix family (always available in core package).
    assert "woodpecker.normalize_tas_units_to_kelvin" in ids
    assert "woodpecker.ensure_latitude_is_increasing" in ids
    assert "woodpecker.remove_coordinate_fill_value_encodings" in ids


def test_registry_rejects_invalid_suffix_pattern():
    with pytest.raises(ValueError, match="Invalid suffix"):

        class _InvalidCode:
            suffix = "bad-id"
            name = "Invalid code"
            description = ""
            categories = ["metadata"]
            priority = 10
            dataset = None
            labels = [Labels.RISK_METADATA_ONLY]

        FixFunctionRegistry.register(_InvalidCode)


def test_registry_rejects_missing_name():
    with pytest.raises(ValueError, match="non-empty 'name'"):

        class _MissingName:
            name = ""
            description = ""
            categories = ["metadata"]
            priority = 10
            dataset = None

        FixFunctionRegistry.register(_MissingName)


def test_registry_rejects_missing_severity_label():
    with pytest.raises(ValueError, match="at least one severity label"):

        class _MissingSeverity:
            prefix = "test"
            suffix = "missing_severity"
            name = "Missing severity"
            description = ""
            categories = ["metadata"]
            priority = 10
            dataset = None
            labels = ["plugin.info_only"]

        FixFunctionRegistry.register(_MissingSeverity)


def test_registry_rejects_priority_below_unprioritized_sentinel():
    with pytest.raises(ValueError, match="priority.*>= -1"):

        class _InvalidPriority(FixFunction):
            prefix = "test"
            suffix = "invalid_priority"
            name = "Invalid priority"
            description = ""
            categories = ["metadata"]
            priority = -2
            dataset = None

        FixFunctionRegistry.register(_InvalidPriority)


def test_register_fix_function_decorator_registers_class():
    class _Alias(FixFunction):
        prefix = "test"
        suffix = "alias_fix"
        aliases = ["alias_lookup"]
        name = "Alias decorator fix"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None
        labels = [Labels.RISK_METADATA_ONLY]

    registered = register_fix_function(_Alias)
    assert registered is _Alias
    assert "test.alias_fix" in FixFunctionRegistry.registered_ids()
    assert FixFunctionRegistry.resolve_identifier("test.alias_lookup") == "test.alias_fix"

    with pytest.raises(KeyError):
        FixFunctionRegistry.resolve_identifier("alias_lookup")


def test_registry_supports_fully_qualified_aliases_without_local_expansion():
    class _QualifiedAlias(FixFunction):
        prefix = "test"
        suffix = "qualified_alias_fix"
        aliases = ["other.explicit_lookup"]
        name = "Qualified alias fix"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    register_fix_function(_QualifiedAlias)
    assert (
        FixFunctionRegistry.resolve_identifier("other.explicit_lookup")
        == "test.qualified_alias_fix"
    )
    with pytest.raises(KeyError):
        FixFunctionRegistry.resolve_identifier("explicit_lookup")


def test_registry_rejects_invalid_alias_syntax():
    with pytest.raises(ValueError, match="Invalid alias"):

        class _InvalidAlias(FixFunction):
            prefix = "test"
            suffix = "invalid_alias_fix"
            aliases = ["bad-alias"]
            name = "Invalid alias fix"
            description = ""
            categories = ["metadata"]
            priority = 10
            dataset = None

        FixFunctionRegistry.register(_InvalidAlias)


def test_registry_suffix_derivation_precedence_explicit_over_derived():
    class _ExplicitLocalIdWins(FixFunction):
        prefix = "test"
        suffix = "explicit_local"
        name = "Explicit suffix wins"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

        @staticmethod
        def derived_suffix() -> str:
            return "derived_local"

    register_fix_function(_ExplicitLocalIdWins)
    assert _ExplicitLocalIdWins.id == "test.explicit_local"


def test_registry_uses_suffix_field_for_identifier_derivation():
    class _Suffix(FixFunction):
        prefix = "test"
        suffix = "explicit_suffix"
        name = "Suffix identifier"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    register_fix_function(_Suffix)
    assert _Suffix.suffix == "explicit_suffix"
    assert _Suffix.id == "test.explicit_suffix"


def test_registry_suffix_derivation_uses_derived_when_suffix_missing():
    class _DerivedLocalId(FixFunction):
        prefix = "test"
        name = "Derived suffix"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

        @staticmethod
        def derived_suffix() -> str:
            return "derived_local"

    register_fix_function(_DerivedLocalId)
    assert _DerivedLocalId.id == "test.derived_local"


def test_registry_suffix_derivation_falls_back_to_class_name_snake_case():
    class FallbackFromClassName:
        prefix = "test"
        name = "Fallback suffix"

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
        labels = [Labels.RISK_METADATA_ONLY]

    register_fix_function(FallbackFromClassName)
    assert FallbackFromClassName.id == "test.fallback_from_class_name"


def test_registry_discovers_prioritized_before_unprioritized_then_by_id():
    class _UnprioritizedBeta(FixFunction):
        prefix = "test"
        suffix = "unprioritized_beta"
        name = "Unprioritized beta"
        description = ""
        categories = ["metadata"]
        dataset = None

    class _PriorityTwo(FixFunction):
        prefix = "test"
        suffix = "priority_two"
        name = "Priority two"
        description = ""
        categories = ["metadata"]
        priority = 2
        dataset = None

    class _UnprioritizedAlpha(FixFunction):
        prefix = "test"
        suffix = "unprioritized_alpha"
        name = "Unprioritized alpha"
        description = ""
        categories = ["metadata"]
        dataset = None

    class _PriorityOne(FixFunction):
        prefix = "test"
        suffix = "priority_one"
        name = "Priority one"
        description = ""
        categories = ["metadata"]
        priority = 1
        dataset = None

    register_fix_function(_UnprioritizedBeta)
    register_fix_function(_PriorityTwo)
    register_fix_function(_UnprioritizedAlpha)
    register_fix_function(_PriorityOne)

    discovered_ids = [fix.id for fix in FixFunctionRegistry.discover() if fix.prefix == "test"]

    assert discovered_ids == [
        "test.priority_one",
        "test.priority_two",
        "test.unprioritized_alpha",
        "test.unprioritized_beta",
    ]


def test_registry_resolves_ids_and_aliases_for_known_fixes():
    assert (
        FixFunctionRegistry.resolve_identifier("woodpecker.normalize_tas_units_to_kelvin")
        == "woodpecker.normalize_tas_units_to_kelvin"
    )
    assert (
        FixFunctionRegistry.resolve_identifier("woodpecker.tas_units_to_kelvin")
        == "woodpecker.normalize_tas_units_to_kelvin"
    )

    with pytest.raises(KeyError):
        FixFunctionRegistry.resolve_identifier("normalize_tas_units_to_kelvin")
    with pytest.raises(KeyError):
        FixFunctionRegistry.resolve_identifier("tas_units_to_kelvin")


def test_registry_instantiate_returns_fix_for_id():
    fix = FixFunctionRegistry.instantiate("woodpecker.normalize_tas_units_to_kelvin")
    assert getattr(fix, "id", "") == "woodpecker.normalize_tas_units_to_kelvin"
    assert "risk.value_transformation" in getattr(fix, "labels", [])


def test_registry_instantiate_returns_fresh_instance_each_time():
    first = FixFunctionRegistry.instantiate("woodpecker.normalize_tas_units_to_kelvin")
    second = FixFunctionRegistry.instantiate("woodpecker.normalize_tas_units_to_kelvin")

    assert first is not second


def test_registry_instantiate_unknown_id_raises_clear_error():
    with pytest.raises(KeyError, match="Unknown fix id"):
        FixFunctionRegistry.instantiate("woodpecker.unknown_fix")


def test_registry_does_not_resolve_unqualified_suffix():
    class _AmbiguousOne(FixFunction):
        prefix = "alpha"
        suffix = "shared"
        name = "Ambiguous One"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    class _AmbiguousTwo(FixFunction):
        prefix = "beta"
        suffix = "shared"
        name = "Ambiguous Two"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    register_fix_function(_AmbiguousOne)
    register_fix_function(_AmbiguousTwo)
    with pytest.raises(KeyError):
        FixFunctionRegistry.resolve_identifier("shared")
