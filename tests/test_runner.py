import xarray as xr

from woodpecker.data_input import DataInput
from woodpecker.runner import run_fix


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


def test_run_fix_reports_failed_persistence():
    ds = xr.Dataset(attrs={"source_name": "dummy.nc"})
    data_input = DummyInput(dataset=ds, save_ok=False)

    stats = run_fix([data_input], [DummyFix()], dry_run=False, output_format="auto")

    assert stats["attempted"] == 1
    assert stats["changed"] == 1
    assert stats["persist_attempted"] == 1
    assert stats["persisted"] == 0
    assert stats["persist_failed"] == 1
