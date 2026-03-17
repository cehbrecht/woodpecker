import xarray as xr

from woodpecker.fixes.identity import (
    DatasetIdentity,
    DatasetIdentityResolver,
    register_dataset_identity_resolver,
    resolve_dataset_identity,
)


def test_default_identity_resolver_derives_project_id_from_dataset_id():
    ds = xr.Dataset(attrs={"dataset_id": "c3s-cmip6.foo.bar"})

    identity = resolve_dataset_identity(ds)

    assert identity.dataset_id == "c3s-cmip6.foo.bar"
    assert identity.project_id == "c3s-cmip6"


def test_dataset_type_resolver_can_override_defaults():
    ds = xr.Dataset(attrs={"dataset_id": "ignored.value"})

    class _Resolver(DatasetIdentityResolver):
        def resolve(self, dataset: xr.Dataset) -> DatasetIdentity:
            _ = dataset
            return DatasetIdentity(
                dataset_id="custom.ds", project_id="custom", dataset_type="custom"
            )

    register_dataset_identity_resolver("unit-test-type", _Resolver(), override=True)
    identity = resolve_dataset_identity(ds, dataset_type="unit-test-type")

    assert identity.dataset_id == "custom.ds"
    assert identity.project_id == "custom"
    assert identity.dataset_type == "unit-test-type"
