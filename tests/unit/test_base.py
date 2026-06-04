from woodpecker.fixes.base import FixFunction
from woodpecker.fixes.labels import LabelCategories, Labels


class _BaseMetadata(FixFunction):
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
    labels = [Labels.RISK_METADATA_ONLY]


def test_fix_metadata_is_class_level_and_config_is_instance_runtime_state():
    fix = _BaseMetadata()

    assert fix.name == "Base metadata fix"
    assert fix.suffix == "base_metadata"
    assert fix.id == "test.base_metadata"
    assert fix.config == {}

    fix.configure({"mode": "strict"})

    assert fix.config == {"mode": "strict"}
    assert _BaseMetadata.categories == ["metadata"]


def test_fix_metadata_accessor_returns_copied_mutable_fields():
    meta = _BaseMetadata.class_metadata()

    assert meta["id"] == "test.base_metadata"
    assert meta["aliases"] == ["base_metadata_alias"]
    assert meta["labels"] == [Labels.RISK_METADATA_ONLY]
    assert meta["label_titles"] == ["safe: metadata only"]
    assert meta["label_metadata"][0]["category"] == LabelCategories.RISK_LOW

    meta["aliases"].append("new_alias")
    assert _BaseMetadata.aliases == ["base_metadata_alias"]


def test_fix_function_suffix_derivation_uses_domain_class_name():
    class ExampleMetadata(FixFunction):
        pass

    assert ExampleMetadata.derived_suffix() == "example_metadata"


def test_fix_function_default_priority_is_unprioritized():
    class ExampleMetadata(FixFunction):
        pass

    assert ExampleMetadata.priority == -1


def test_fix_function_default_labels_require_review():
    class ExampleMetadata(FixFunction):
        pass

    assert ExampleMetadata.labels == [Labels.RISK_REVIEW_BEFORE_APPLYING]


def test_fix_metadata_includes_general_labels():
    class ExampleMetadata(FixFunction):
        labels = ["user.visible"]

    meta = ExampleMetadata.class_metadata()

    assert meta["labels"] == ["user.visible"]
    assert meta["label_titles"] == ["user.visible"]
    assert meta["label_metadata"][0]["category"] == LabelCategories.INFO
