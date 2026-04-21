import pytest

from woodpecker.fixes.registry import Fix, FixRegistry, GroupFix, register_fix


def test_registry_discovers_builtins():
    fixes = FixRegistry.discover()
    codes = {fix.code for fix in fixes}

    # CMIP6 (non-decadal) plugin family
    assert "CMIP6_0001" in codes

    # CMIP6-decadal plugin family
    assert "CMIP6D_0001" in codes
    assert "CMIP6D_0002" in codes
    assert "CMIP6D_0003" in codes
    assert "CMIP6D_0004" in codes
    assert "CMIP6D_0005" in codes
    assert "CMIP6D_0006" in codes
    assert "CMIP6D_0007" in codes
    assert "CMIP6D_0008" in codes
    assert "CMIP6D_0009" in codes
    assert "CMIP6D_0010" in codes
    assert "CMIP6D_0011" in codes
    assert "CMIP6D_0012" in codes
    assert "CMIP6D_0013" in codes
    assert "CMIP6D_0014" in codes
    assert "CMIP6D_0015" in codes

    # Atlas plugin family
    assert "ATLAS_0001" in codes
    assert "ATLAS_0002" in codes

    # Common non-project fix family
    assert "COMMON_0001" in codes
    assert "COMMON_0002" in codes
    assert "COMMON_0003" in codes

    # CMIP7 fixes are provided via external plugin.
    assert "CMIP7_0001" in codes
    assert "CMIP7_0002" in codes

    # Group fix
    assert "CMIP6D_0999" in codes


def test_group_fix_is_group_fix_instance():
    fixes = FixRegistry.discover()
    group = next(f for f in fixes if f.code == "CMIP6D_0999")
    assert isinstance(group, GroupFix)
    assert group.member_codes == [
        "CMIP6D_0001",
        "CMIP6D_0002",
        "CMIP6D_0003",
        "CMIP6D_0004",
        "CMIP6D_0005",
        "CMIP6D_0006",
        "CMIP6D_0007",
        "CMIP6D_0008",
        "CMIP6D_0009",
        "CMIP6D_0010",
        "CMIP6D_0011",
        "CMIP6D_0012",
        "CMIP6D_0013",
        "CMIP6D_0014",
        "CMIP6D_0015",
    ]


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
    class _AliasFix(Fix):
        code = "ALIAS_0001"
        name = "Alias decorator fix"
        description = ""
        categories = ["metadata"]
        priority = 10
        dataset = None

    registered = register_fix(_AliasFix)
    assert registered is _AliasFix
    assert "ALIAS_0001" in FixRegistry.registered_codes()
    FixRegistry._registry.pop("ALIAS_0001", None)


def test_registry_resolves_canonical_and_legacy_aliases_for_known_fixes():
    assert FixRegistry.resolve_identifier("ATLAS_0001") == "ATLAS_0001"
    assert FixRegistry.resolve_identifier("ATLAS.0001") == "ATLAS_0001"


def test_registry_rejects_ambiguous_local_identifier():
    with pytest.raises(ValueError, match="Ambiguous fix identifier"):
        FixRegistry.resolve_identifier("0001")
