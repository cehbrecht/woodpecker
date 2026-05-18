import woodpecker_cmip6_decadal_plugin  # noqa: F401

from woodpecker.fixes.registry import FixRegistry
from woodpecker.testing import make_cmip6_decadal

EXPECTED_FIX_IDS = {
    "cmip6_decadal.calendar_normalization",
    "cmip6_decadal.coordinates_encoding_cleanup",
    "cmip6_decadal.fillvalue_encoding_cleanup",
    "cmip6_decadal.further_info_url_normalization",
    "cmip6_decadal.leadtime_coordinate",
    "cmip6_decadal.leadtime_metadata_normalization",
    "cmip6_decadal.model_global_attributes",
    "cmip6_decadal.realization_comment_normalization",
    "cmip6_decadal.realization_dtype_normalization",
    "cmip6_decadal.realization_index_normalization",
    "cmip6_decadal.realization_long_name_normalization",
    "cmip6_decadal.realization_variable",
    "cmip6_decadal.reftime_coordinate",
    "cmip6_decadal.start_token_normalization",
    "cmip6_decadal.time_metadata",
}


def test_plugin_registers_expected_fixes():
    fix_ids = {fix.id for fix in FixRegistry.discover()}

    assert EXPECTED_FIX_IDS.issubset(fix_ids)


def test_plugin_fixes_work_with_public_api():
    import woodpecker

    dataset = make_cmip6_decadal(
        overrides={"source_name": "c3s-cmip6-decadal.member.tos.nc"}
    )
    dataset["time"].attrs.pop("long_name", None)
    findings = woodpecker.check(dataset, fixes=sorted(EXPECTED_FIX_IDS))

    assert findings
    assert set(findings.fix_ids).issubset(EXPECTED_FIX_IDS)
