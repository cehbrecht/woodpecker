import pytest

from woodpecker.fixes.registry import FixRegistry, GroupFix


def test_registry_discovers_builtins():
    fixes = FixRegistry.discover()
    codes = {fix.code for fix in fixes}

    # CMIP6 (non-decadal) placeholder fix family
    assert "CMIP601" in codes

    # CMIP6-decadal fix family
    assert "CMIP6D01" in codes
    assert "CMIP6D02" in codes
    assert "CMIP6D03" in codes
    assert "CMIP6D04" in codes
    assert "CMIP6D05" in codes
    assert "CMIP6D06" in codes
    assert "CMIP6D07" in codes
    assert "CMIP6D08" in codes
    assert "CMIP6D09" in codes
    assert "CMIP6D10" in codes
    assert "CMIP6D11" in codes
    assert "CMIP6D12" in codes
    assert "CMIP6D13" in codes
    assert "CMIP6D14" in codes
    assert "CMIP6D15" in codes

    # Atlas fix family
    assert "ATLAS01" in codes
    assert "ATLAS02" in codes

    # CMIP7 fix family
    assert "CMIP701" in codes
    assert "CMIP702" in codes
    assert "CMIP703" in codes
    assert "CMIP704" in codes
    assert "CMIP705" in codes

    # Group fix
    assert "CMIP6DG01" in codes


def test_group_fix_is_group_fix_instance():
    fixes = FixRegistry.discover()
    group = next(f for f in fixes if f.code == "CMIP6DG01")
    assert isinstance(group, GroupFix)
    assert group.member_codes == [
        "CMIP6D01",
        "CMIP6D02",
        "CMIP6D03",
        "CMIP6D04",
        "CMIP6D05",
        "CMIP6D06",
        "CMIP6D07",
        "CMIP6D08",
        "CMIP6D09",
        "CMIP6D10",
        "CMIP6D11",
        "CMIP6D12",
        "CMIP6D13",
        "CMIP6D14",
        "CMIP6D15",
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
