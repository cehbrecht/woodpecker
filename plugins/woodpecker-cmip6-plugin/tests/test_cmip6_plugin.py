import woodpecker_cmip6_plugin  # noqa: F401

from woodpecker.fixes.registry import FixRegistry
from woodpecker.testing import make_cmip6

EXPECTED_FIX_IDS = {
    "cmip6.dummy_placeholder",
}


def test_plugin_registers_expected_fixes():
    fix_ids = {fix.id for fix in FixRegistry.discover()}

    assert EXPECTED_FIX_IDS.issubset(fix_ids)


def test_plugin_fixes_work_with_public_api():
    import woodpecker

    dataset = make_cmip6(overrides={"source_name": "c3s-cmip6.member.tas.nc"})
    findings = woodpecker.check(dataset, fixes=sorted(EXPECTED_FIX_IDS))

    assert findings
    assert set(findings.fix_ids) == EXPECTED_FIX_IDS
