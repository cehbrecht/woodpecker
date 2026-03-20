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

    # ESMVal example fix family
    assert "ESMVAL01" in codes
    assert "ESMVAL02" in codes
    assert "ESMVAL03" in codes
    assert "ESMVAL04" in codes
    assert "ESMVAL05" in codes

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
