import xarray as xr

from woodpecker.fixes.base import Fix, GroupFix


class _BaseMetadataFix(Fix):
    namespace_prefix = "test"
    local_id = "base_metadata"
    canonical_id = "test.base_metadata"
    aliases = ["base_metadata_alias"]
    links = [{"rel": "docs", "href": "https://example.invalid/fix"}]
    name = "Base metadata fix"
    description = "Metadata is class-level by default"
    categories = ["metadata"]
    priority = 7
    dataset = "cmip6"


class _MemberFix(Fix):
    namespace_prefix = "group"
    local_id = "member_fix"
    canonical_id = "group.member_fix"
    aliases = []
    links = []
    name = "Member fix"
    description = ""
    categories = ["metadata"]
    priority = 10
    dataset = None

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        marker = self.config.get("marker")
        if marker:
            dataset.attrs["marker"] = marker
            return True
        return False


class _ContainerGroupFix(GroupFix):
    namespace_prefix = "group"
    local_id = "container"
    canonical_id = "group.container"
    aliases = []
    links = []
    name = "Container"
    description = ""
    categories = ["metadata"]
    priority = 10
    dataset = None
    members = [_MemberFix]


def test_fix_metadata_is_class_level_and_config_is_instance_runtime_state():
    fix = _BaseMetadataFix()

    assert fix.name == "Base metadata fix"
    assert fix.local_id == "base_metadata"
    assert fix.canonical_id == "test.base_metadata"
    assert fix.config == {}

    fix.configure({"mode": "strict"})

    assert fix.config == {"mode": "strict"}
    assert _BaseMetadataFix.categories == ["metadata"]



def test_fix_metadata_accessor_returns_copied_mutable_fields():
    meta = _BaseMetadataFix.class_metadata()

    assert meta["canonical_id"] == "test.base_metadata"
    assert meta["aliases"] == ["base_metadata_alias"]

    meta["aliases"].append("new_alias")
    assert _BaseMetadataFix.aliases == ["base_metadata_alias"]



def test_group_fix_member_config_accepts_canonical_or_local_member_keys():
    ds = xr.Dataset(attrs={"source_name": "dummy.nc"})

    group_local = _ContainerGroupFix().configure(
        {"members": {"member_fix": {"marker": "local"}}}
    )
    changed_local = group_local.apply(ds, dry_run=False)

    assert changed_local is True
    assert ds.attrs["marker"] == "local"

    ds2 = xr.Dataset(attrs={"source_name": "dummy.nc"})
    group_canonical = _ContainerGroupFix().configure(
        {"members": {"group.member_fix": {"marker": "canonical"}}}
    )
    changed_canonical = group_canonical.apply(ds2, dry_run=False)

    assert changed_canonical is True
    assert ds2.attrs["marker"] == "canonical"
