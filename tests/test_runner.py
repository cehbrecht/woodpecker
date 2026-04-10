import xarray as xr

from woodpecker.inout import DataInput
from woodpecker.runner import run_fix, select_fixes


class DummyInput(DataInput):
    def __init__(self, dataset: xr.Dataset, save_ok: bool):
        super().__init__(name="dummy")
        self._dataset = dataset
        self._save_ok = save_ok

    def load(self) -> xr.Dataset:
        return self._dataset

    def save(self, dataset: xr.Dataset, dry_run: bool = True, output_adapter=None) -> bool:
        if dry_run:
            return False
        return self._save_ok


class DummyFix:
    code = "DUMMY01"
    name = "Dummy fix"

    def matches(self, dataset: xr.Dataset) -> bool:
        return True

    def check(self, dataset: xr.Dataset) -> list[str]:
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        return True


class DeclaredCmipFix:
    code = "CMIPX"
    name = "Declared cmip fix"
    dataset = "cmip6"

    def matches(self, dataset: xr.Dataset) -> bool:
        return True

    def check(self, dataset: xr.Dataset) -> list[str]:
        return ["should not run for atlas"]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        return True


def test_run_fix_reports_failed_persistence():
    ds = xr.Dataset(attrs={"source_name": "dummy.nc"})
    data_input = DummyInput(dataset=ds, save_ok=False)

    stats = run_fix([data_input], [DummyFix()], dry_run=False, output_format="auto")

    assert stats["attempted"] == 1
    assert stats["changed"] == 1
    assert stats["persist_attempted"] == 1
    assert stats["persisted"] == 0
    assert stats["persist_failed"] == 1


def test_run_fix_skips_fixes_for_other_dataset_types():
    ds = xr.Dataset(attrs={"source_name": "c3s-ipcc-atlas.dataset.tas.nc"})
    data_input = DummyInput(dataset=ds, save_ok=True)

    stats = run_fix([data_input], [DeclaredCmipFix()], dry_run=False, output_format="auto")

    assert stats["attempted"] == 0
    assert stats["changed"] == 0


def test_select_fixes_respects_ordered_codes_sequence():
    fixes = select_fixes(ordered_codes=["CMIP601", "ATLAS01"], strict_codes=True)
    ordered = [fix.code for fix in fixes]

    assert ordered[:2] == ["CMIP601", "ATLAS01"]
