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
