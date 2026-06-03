import pytest

from woodpecker.fixes.labels import FixLabelRegistry, RiskLabels, register_fix_label


def test_builtin_risk_labels_have_stable_ids_and_titles():
    label = FixLabelRegistry.get(RiskLabels.VALUE_TRANSFORMATION)

    assert label is not None
    assert label.id == "risk.careful.value_transformation"
    assert label.title == "careful: value transformation"


def test_plugins_can_register_custom_labels():
    label = register_fix_label(
        "plugin.example.experimental",
        "experimental",
        description="Plugin-defined informational label.",
        group="tag",
    )

    assert label.title == "experimental"
    assert FixLabelRegistry.title("plugin.example.experimental") == "experimental"


def test_duplicate_custom_labels_require_override():
    register_fix_label("plugin.example.override_me", "first")

    with pytest.raises(ValueError, match="Duplicate label id"):
        register_fix_label("plugin.example.override_me", "second")

    label = register_fix_label("plugin.example.override_me", "second", override=True)
    assert label.title == "second"


def test_unknown_labels_display_as_raw_ids():
    assert FixLabelRegistry.title("plugin.unknown.label") == "plugin.unknown.label"
