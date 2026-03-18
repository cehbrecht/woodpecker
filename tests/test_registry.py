from woodpecker.fixes.registry import FixRegistry


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

    # Atlas fix family
    assert "ATLAS01" in codes
    assert "ATLAS02" in codes
