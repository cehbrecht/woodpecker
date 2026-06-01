import woodpecker_cmip6_plugin  # noqa: F401
from _cmip6_helpers import (
    assert_fix_dry_run_reports_change,
    assert_fix_write_reports_change,
    check_finding_ids,
)

from woodpecker.fixes.registry import FixFunctionRegistry
from woodpecker.testing import make_cmip6

EXPECTED_FIX_IDS = {
    "cmip6.dummy_placeholder",
}
CMIP6_SOURCE_NAME = "c3s-cmip6.member.tas.nc"


def _cmip6_dataset(**overrides):
    return make_cmip6(overrides={"source_name": CMIP6_SOURCE_NAME, **overrides})


def test_plugin_registers_expected_fixes():
    fix_ids = {fix.id for fix in FixFunctionRegistry.discover()}

    assert EXPECTED_FIX_IDS.issubset(fix_ids)


def test_plugin_fixes_work_with_public_api():
    import woodpecker

    dataset = make_cmip6(overrides={"source_name": "c3s-cmip6.member.tas.nc"})
    findings = woodpecker.check(dataset, fixes=sorted(EXPECTED_FIX_IDS))

    assert findings
    assert set(findings.fix_ids) == EXPECTED_FIX_IDS


def test_cmip6_dummy_placeholder_fix_is_detected_and_applied():
    dataset = _cmip6_dataset()

    assert check_finding_ids(dataset, "cmip6.dummy_placeholder") == {"cmip6.dummy_placeholder"}
    assert_fix_dry_run_reports_change(dataset, "cmip6.dummy_placeholder")
    assert "woodpecker_fix_cmip6_0001" not in dataset.attrs

    assert_fix_write_reports_change(dataset, "cmip6.dummy_placeholder")
    assert dataset.attrs["woodpecker_fix_cmip6_0001"] == "applied"
