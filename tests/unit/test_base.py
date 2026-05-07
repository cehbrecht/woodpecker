from woodpecker.fixes.base import Fix


class _BaseMetadataFix(Fix):
    prefix = "test"
    suffix = "base_metadata"
    id = "test.base_metadata"
    aliases = ["base_metadata_alias"]
    links = [{"rel": "docs", "href": "https://example.invalid/fix"}]
    name = "Base metadata fix"
    description = "Metadata is class-level by default"
    categories = ["metadata"]
    priority = 7
    dataset = "cmip6"


def test_fix_metadata_is_class_level_and_config_is_instance_runtime_state():
    fix = _BaseMetadataFix()

    assert fix.name == "Base metadata fix"
    assert fix.suffix == "base_metadata"
    assert fix.id == "test.base_metadata"
    assert fix.config == {}

    fix.configure({"mode": "strict"})

    assert fix.config == {"mode": "strict"}
    assert _BaseMetadataFix.categories == ["metadata"]


def test_fix_metadata_accessor_returns_copied_mutable_fields():
    meta = _BaseMetadataFix.class_metadata()

    assert meta["id"] == "test.base_metadata"
    assert meta["aliases"] == ["base_metadata_alias"]

    meta["aliases"].append("new_alias")
    assert _BaseMetadataFix.aliases == ["base_metadata_alias"]
