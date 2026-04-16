import xarray as xr

from woodpecker.inout import DataInput
from woodpecker.plans.runner import run_fix, select_fixes


class DummyInput(DataInput):
    def __init__(self, dataset: xr.Dataset, save_ok: bool):
        super().__init__(name="dummy")
        self._dataset = dataset
        self._save_ok = save_ok
        self.saved_attrs = None

    def load(self) -> xr.Dataset:
        return self._dataset

    def save(self, dataset: xr.Dataset, dry_run: bool = True, output_adapter=None) -> bool:
        if dry_run:
            return False
        self.saved_attrs = dict(dataset.attrs)
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


class NonMatchingFix:
    code = "DUMMY02"
    name = "Non matching fix"

    def matches(self, dataset: xr.Dataset) -> bool:
        return False

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


def test_run_fix_skips_fixes_for_other_dataset_types():
    ds = xr.Dataset(attrs={"source_name": "c3s-ipcc-atlas.dataset.tas.nc"})
    data_input = DummyInput(dataset=ds, save_ok=True)

    stats = run_fix([data_input], [DeclaredCmipFix()], dry_run=False, output_format="auto")

    assert stats["attempted"] == 0
    assert stats["changed"] == 0


def test_select_fixes_respects_ordered_codes_sequence():
    fixes = select_fixes(ordered_codes=["CMIP6_0001", "ATLAS_0001"], strict_codes=True)
    ordered = [fix.code for fix in fixes]

    assert ordered[:2] == ["CMIP6_0001", "ATLAS_0001"]


def test_run_fix_can_embed_provenance_metadata_on_write():
    ds = xr.Dataset(attrs={"source_name": "dummy.nc"})
    data_input = DummyInput(dataset=ds, save_ok=True)

    stats = run_fix(
        [data_input],
        [DummyFix()],
        dry_run=False,
        output_format="auto",
        embed_provenance_metadata=True,
        provenance_run_id="run-123",
    )

    assert stats["changed"] == 1
    assert data_input.saved_attrs is not None
    assert "woodpecker_provenance" in data_input.saved_attrs


def test_run_fix_force_apply_bypasses_matches():
    ds = xr.Dataset(attrs={"source_name": "dummy.nc"})
    data_input = DummyInput(dataset=ds, save_ok=True)

    stats = run_fix(
        [data_input],
        [NonMatchingFix()],
        dry_run=False,
        force_apply=True,
        output_format="auto",
    )

    assert stats["attempted"] == 1
    assert stats["changed"] == 1


def test_run_fix_without_force_apply_respects_matches():
    ds = xr.Dataset(attrs={"source_name": "dummy.nc"})
    data_input = DummyInput(dataset=ds, save_ok=True)

    stats = run_fix(
        [data_input],
        [NonMatchingFix()],
        dry_run=False,
        force_apply=False,
        output_format="auto",
    )

    assert stats["attempted"] == 0
    assert stats["changed"] == 0
