import xarray as xr

from woodpecker.identity import (
    DatasetIdentity,
    DatasetIdentityResolver,
    register_dataset_identity,
    resolve_dataset_identity,
)


def test_default_identity_resolver_derives_project_id_from_dataset_id():
    ds = xr.Dataset(attrs={"dataset_id": "c3s-cmip6.foo.bar"})

    identity = resolve_dataset_identity(ds)

    assert identity.dataset_id == "c3s-cmip6.foo.bar"
    assert identity.project_id == "c3s-cmip6"


def test_dataset_type_resolver_can_override_defaults():
    ds = xr.Dataset(attrs={"source_name": "unit-test-type.dataset.nc"})

    @register_dataset_identity("unit-test-type", override=True)
    class _Resolver(DatasetIdentityResolver):
        dataset_type = "unit-test-type"
        priority = 5

        def matches(self, dataset: xr.Dataset) -> bool:
            source = str(dataset.attrs.get("source_name", "")).lower()
            return source.endswith(".nc") and "unit-test-type" in source

        def resolve(self, dataset: xr.Dataset) -> DatasetIdentity:
            _ = dataset
            return DatasetIdentity(
                dataset_id="custom.ds", project_id="custom", dataset_type="custom"
            )

    identity = resolve_dataset_identity(ds)

    assert identity.dataset_id == "custom.ds"
    assert identity.project_id == "custom"
    assert identity.dataset_type == "unit-test-type"


def test_identity_uses_detected_cmip6_decadal_dataset_type():
    ds = xr.Dataset(attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc"})

    identity = resolve_dataset_identity(ds)

    assert identity.dataset_type == "cmip6-decadal"
    assert identity.dataset_id == "c3s-cmip6-decadal.member.tas.nc"
    assert identity.project_id == "c3s-cmip6-decadal"


def test_dataset_type_resolver_can_register_with_decorator():
    ds = xr.Dataset(attrs={"source_name": "decorator-type.dataset.nc"})

    @register_dataset_identity("decorator-type", override=True)
    class _Resolver(DatasetIdentityResolver):
        dataset_type = "decorator-type"
        priority = 4

        def matches(self, dataset: xr.Dataset) -> bool:
            source = str(dataset.attrs.get("source_name", "")).lower()
            return source.endswith(".nc") and "decorator-type" in source

        def resolve(self, dataset: xr.Dataset) -> DatasetIdentity:
            _ = dataset
            return DatasetIdentity(
                dataset_id="decorator.ds", project_id="decorator", dataset_type="decorator-type"
            )

    identity = resolve_dataset_identity(ds)

    assert identity.dataset_type == "decorator-type"
    assert identity.dataset_id == "decorator.ds"
    assert identity.project_id == "decorator"
