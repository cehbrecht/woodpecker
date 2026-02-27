from woodpecker.fixes.registry import FixRegistry


def test_registry_discovers_builtins():
    fixes = FixRegistry.discover()
    codes = {fix.code for fix in fixes}

    assert "CMIP6D01" in codes
    assert "ATLAS01" in codes
