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
    assert identity.dataset_type == "cmip6"
    assert identity.confidence is not None


def test_dataset_type_resolver_can_override_defaults():
    ds = xr.Dataset(attrs={"source_name": "unit-test-type.dataset.nc"})

    @register_dataset_identity("unit-test-type", override=True)
    class _Resolver(DatasetIdentityResolver):
        dataset_type = "unit-test-type"
        priority = 5

        def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity | None:
            source = str(dataset.attrs.get("source_name", "")).lower()
            if not (source.endswith(".nc") and "unit-test-type" in source):
                return None
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
    assert identity.evidence


def test_identity_uses_detected_cmip6_dataset_type():
    ds = xr.Dataset(attrs={"source_name": "c3s-cmip6.member.tas.nc"})

    identity = resolve_dataset_identity(ds)

    assert identity.dataset_type == "cmip6"
    assert identity.dataset_id == "c3s-cmip6.member.tas.nc"
    assert identity.project_id == "c3s-cmip6"
    assert identity.metadata.get("resolver")


def test_dataset_type_resolver_can_register_with_decorator():
    ds = xr.Dataset(attrs={"source_name": "decorator-type.dataset.nc"})

    @register_dataset_identity("decorator-type", override=True)
    class _Resolver(DatasetIdentityResolver):
        dataset_type = "decorator-type"
        priority = 4

        def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity | None:
            source = str(dataset.attrs.get("source_name", "")).lower()
            if not (source.endswith(".nc") and "decorator-type" in source):
                return None
            return DatasetIdentity(
                dataset_id="decorator.ds", project_id="decorator", dataset_type="decorator-type"
            )

    identity = resolve_dataset_identity(ds)

    assert identity.dataset_type == "decorator-type"
    assert identity.dataset_id == "decorator.ds"
    assert identity.project_id == "decorator"


def test_fallback_identity_keeps_dataset_type_none_for_unknown_datasets():
    ds = xr.Dataset(attrs={"dataset_id": "custom.foo", "project_id": "custom"})

    identity = resolve_dataset_identity(ds)

    assert identity.dataset_type is None
    assert identity.dataset_id == "custom.foo"
    assert identity.project_id == "custom"
    assert identity.confidence == 0.0
    assert isinstance(identity.evidence, tuple)
