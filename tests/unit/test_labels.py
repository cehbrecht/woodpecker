import pytest

from woodpecker.fixes.labels import FixLabelRegistry, RiskLabels, register_fix_label


def test_builtin_risk_labels_have_stable_ids_and_titles():
    label = FixLabelRegistry.get(RiskLabels.VALUE_TRANSFORMATION)

    assert label is not None
    assert label.id == "risk.careful.value_transformation"
    assert label.title == "careful: value transformation"
    assert label.category == "risk"


def test_plugins_can_register_custom_labels():
    label = register_fix_label(
        "plugin.example.experimental",
        "experimental",
        description="Plugin-defined informational label.",
        category="info",
    )

    assert label.title == "experimental"
    assert label.category == "info"
    assert FixLabelRegistry.title("plugin.example.experimental") == "experimental"


def test_plugins_can_register_warning_labels():
    label = register_fix_label(
        "plugin.example.requires_domain_review",
        "requires domain review",
        category="warning",
    )

    assert label.category == "warning"


def test_labels_can_be_filtered_by_category():
    register_fix_label("plugin.example.filterable", "filterable", category="info")

    info_ids = {label.id for label in FixLabelRegistry.list_labels(category="info")}
    risk_ids = {label.id for label in FixLabelRegistry.list_labels(category="risk")}

    assert "plugin.example.filterable" in info_ids
    assert RiskLabels.VALUE_TRANSFORMATION in risk_ids


def test_duplicate_custom_labels_require_override():
    register_fix_label("plugin.example.override_me", "first")

    with pytest.raises(ValueError, match="Duplicate label id"):
        register_fix_label("plugin.example.override_me", "second")

    label = register_fix_label("plugin.example.override_me", "second", override=True)
    assert label.title == "second"


def test_unknown_labels_display_as_raw_ids():
    assert FixLabelRegistry.title("plugin.unknown.label") == "plugin.unknown.label"
    assert FixLabelRegistry.metadata("plugin.unknown.label")["category"] == "info"
