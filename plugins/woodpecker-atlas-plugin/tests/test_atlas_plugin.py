import woodpecker_atlas_plugin  # noqa: F401

from woodpecker.fixes.registry import FixRegistry
from woodpecker.testing import make_atlas

EXPECTED_FIX_IDS = {
    "atlas.encoding_cleanup",
    "atlas.project_id_normalization",
}


def test_plugin_registers_expected_fixes():
    fix_ids = {fix.id for fix in FixRegistry.discover()}

    assert EXPECTED_FIX_IDS.issubset(fix_ids)


def test_plugin_fixes_work_with_public_api():
    import woodpecker

    dataset = make_atlas()
    findings = woodpecker.check(dataset, fixes=sorted(EXPECTED_FIX_IDS))

    assert findings
    assert set(findings.fix_ids).issubset(EXPECTED_FIX_IDS)
