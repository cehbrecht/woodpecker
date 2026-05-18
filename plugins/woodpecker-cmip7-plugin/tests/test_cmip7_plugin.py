import woodpecker_cmip7_plugin  # noqa: F401

from woodpecker.fixes.registry import FixRegistry
from woodpecker.testing import make_cmip7

EXPECTED_FIX_IDS = {
    "cmip7.configurable_reformat_bridge",
    "cmip7.ensure_project_id_present",
    "cmip7.rename_temp_variable_to_tas",
}


def test_plugin_registers_expected_fixes():
    fix_ids = {fix.id for fix in FixRegistry.discover()}

    assert EXPECTED_FIX_IDS.issubset(fix_ids)


def test_plugin_fixes_work_with_public_api():
    import woodpecker

    dataset = make_cmip7(missing=["project_id"], rename_vars={"tas": "temp"})
    findings = woodpecker.check(
        dataset,
        fixes=[
            "cmip7.ensure_project_id_present",
            "cmip7.rename_temp_variable_to_tas",
        ],
    )

    assert findings
    assert set(findings.fix_ids).issubset(EXPECTED_FIX_IDS)
