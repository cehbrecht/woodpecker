import pytest

from woodpecker.fixes.labels import LabelCategories, LabelRegistry, Labels, register_label


def test_builtin_labels_have_stable_ids_titles_and_categories():
    label = LabelRegistry.get(Labels.VALUE_TRANSFORMATION)

    assert label is not None
    assert label.id == "risk.careful.value_transformation"
    assert label.title == "careful: value transformation"
    assert label.category == LabelCategories.RISK_MEDIUM


def test_plugins_can_register_custom_labels():
    label = register_label(
        "plugin.example.experimental",
        "experimental",
        description="Plugin-defined informational label.",
        category=LabelCategories.INFO,
    )

    assert label.title == "experimental"
    assert label.category == LabelCategories.INFO
    assert LabelRegistry.title("plugin.example.experimental") == "experimental"


def test_plugins_can_register_custom_severity_labels():
    label = register_label(
        "plugin.example.requires_domain_review",
        "requires domain review",
        category=LabelCategories.RISK_HIGH,
    )

    assert label.category == LabelCategories.RISK_HIGH


def test_labels_can_be_filtered_by_category():
    register_label("plugin.example.filterable", "filterable", category=LabelCategories.INFO)

    info_ids = {label.id for label in LabelRegistry.list_labels(category=LabelCategories.INFO)}
    severity_ids = {
        label.id for label in LabelRegistry.list_labels(category=LabelCategories.RISK_MEDIUM)
    }

    assert "plugin.example.filterable" in info_ids
    assert Labels.VALUE_TRANSFORMATION in severity_ids


def test_duplicate_custom_labels_require_override():
    register_label("plugin.example.override_me", "first")

    with pytest.raises(ValueError, match="Duplicate label id"):
        register_label("plugin.example.override_me", "second")

    label = register_label("plugin.example.override_me", "second", override=True)
    assert label.title == "second"


def test_unknown_labels_display_as_raw_ids():
    assert LabelRegistry.title("plugin.unknown.label") == "plugin.unknown.label"
    assert LabelRegistry.metadata("plugin.unknown.label")["category"] == LabelCategories.INFO
