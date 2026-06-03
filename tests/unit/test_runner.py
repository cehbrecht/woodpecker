import pytest
import xarray as xr

from woodpecker.io import DataInput
from woodpecker.runner import run_fix
from woodpecker.testing import make_atlas


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


class DummyFunction:
    code = "DUMMY01"
    name = "Dummy fix"
    risk = "risk.safe.metadata_only"

    def matches(self, dataset: xr.Dataset) -> bool:
        return True

    def check(self, dataset: xr.Dataset) -> list[str]:
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        return True


class DeclaredCmipFunction:
    code = "CMIPX"
    name = "Declared cmip fix"
    dataset = "cmip6"

    def matches(self, dataset: xr.Dataset) -> bool:
        return True

    def check(self, dataset: xr.Dataset) -> list[str]:
        return ["should not run for atlas"]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        return True


class NonMatchingFunction:
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

    stats = run_fix([data_input], [DummyFunction()], dry_run=False, output_format="auto")

    assert stats["attempted"] == 1
    assert stats["changed"] == 1
    assert stats["persist_attempted"] == 1
    assert stats["persisted"] == 0
    assert stats["persist_failed"] == 1
    assert stats["preview"] == [
        {
            "path": "dummy",
            "fix_id": "",
            "name": "Dummy fix",
            "risk": "risk.safe.metadata_only",
            "risk_label": "safe: metadata only",
            "labels": [],
            "label_titles": [],
            "changed": True,
        }
    ]


def test_run_fix_skips_fixes_for_other_dataset_types():
    ds = make_atlas()
    data_input = DummyInput(dataset=ds, save_ok=True)

    stats = run_fix([data_input], [DeclaredCmipFunction()], dry_run=False, output_format="auto")

    assert stats["attempted"] == 0
    assert stats["changed"] == 0


def test_run_fix_can_embed_provenance_metadata_on_write():
    ds = xr.Dataset(attrs={"source_name": "dummy.nc"})
    data_input = DummyInput(dataset=ds, save_ok=True)

    stats = run_fix(
        [data_input],
        [DummyFunction()],
        dry_run=False,
        output_format="auto",
        embed_provenance_metadata=True,
        provenance_run_id="run-123",
    )

    assert stats["changed"] == 1
    assert data_input.saved_attrs is not None
    assert "woodpecker_provenance" in data_input.saved_attrs


@pytest.mark.parametrize(
    ("force_apply", "expected_attempted", "expected_changed"),
    [
        (True, 1, 1),
        (False, 0, 0),
    ],
)
def test_run_fix_force_apply_controls_non_matching_fixes(
    force_apply, expected_attempted, expected_changed
):
    ds = xr.Dataset(attrs={"source_name": "dummy.nc"})
    data_input = DummyInput(dataset=ds, save_ok=True)

    stats = run_fix(
        [data_input],
        [NonMatchingFunction()],
        dry_run=False,
        force_apply=force_apply,
        output_format="auto",
    )

    assert stats["attempted"] == expected_attempted
    assert stats["changed"] == expected_changed


def test_run_fix_preview_omits_nonmatching_fixes():
    ds = xr.Dataset(attrs={"source_name": "dummy.nc"})
    data_input = DummyInput(dataset=ds, save_ok=True)

    stats = run_fix(
        [data_input],
        [NonMatchingFunction()],
        dry_run=True,
        output_format="auto",
    )

    assert stats["preview"] == []
