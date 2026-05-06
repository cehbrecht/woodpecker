import pytest

from woodpecker.fixes.identifiers import (
    IdentifierResolver,
    IdentifierRules,
    IdentifierSet,
    build_identifier_resolver,
    coerce_scoped_identifier,
)


def test_identifier_rules_build_creates_canonical_identifier_set():
    identifiers = IdentifierRules.build(prefix="cmip7", suffix="configurable_reformat_bridge")

    assert identifiers == IdentifierSet(
        prefix="cmip7",
        suffix="configurable_reformat_bridge",
        id="cmip7.configurable_reformat_bridge",
        aliases=(),
    )


def test_identifier_rules_build_uses_suffix_field():
    identifiers = IdentifierRules.build(prefix="cmip7", suffix="bridge")

    assert identifiers.suffix == "bridge"
    assert identifiers.id == "cmip7.bridge"


def test_identifier_rules_derive_suffix_from_name_strips_fix_and_plan_suffixes():
    assert (
        IdentifierRules.derive_suffix_from_name("NormalizeTasUnitsToKelvinFix")
        == "normalize_tas_units_to_kelvin"
    )
    assert IdentifierRules.derive_suffix_from_name("AtlasMonitoringPlan") == "atlas_monitoring"


def test_identifier_rules_expand_aliases_for_suffix_and_qualified_values():
    aliases = IdentifierRules.expand_aliases(
        prefix="atlas",
        id="atlas.encoding_cleanup",
        declared_aliases=["cleanup", "atlas.cleanup2"],
    )

    assert aliases == ("atlas.cleanup", "atlas.cleanup2")


def test_identifier_rules_reject_invalid_alias_syntax():
    with pytest.raises(ValueError, match="Invalid alias"):
        IdentifierRules.expand_aliases(
            prefix="atlas",
            id="atlas.encoding_cleanup",
            declared_aliases=["bad-alias"],
        )


def test_identifier_rules_reject_non_ascii_identifier_parts():
    with pytest.raises(ValueError, match="ASCII characters only"):
        IdentifierRules.build(prefix="cmip6", suffix="temperatür")


def test_identifier_rules_reject_spaces_and_special_chars_in_id_parts():
    with pytest.raises(ValueError, match="no spaces or special characters"):
        IdentifierRules.build(prefix="cmip6", suffix="bad id")

    with pytest.raises(ValueError, match="no spaces or special characters"):
        IdentifierRules.validate_canonical_id("fix id", "cmip6.bad-id")


def test_identifier_resolver_registers_and_resolves_canonical_and_alias_forms():
    resolver = IdentifierResolver()
    resolver.register(
        IdentifierSet(
            prefix="cmip7",
            suffix="bridge",
            id="cmip7.bridge",
            aliases=("cmip7.bridge_alias",),
        )
    )

    assert resolver.resolve("cmip7.bridge") == "cmip7.bridge"
    assert resolver.resolve("cmip7.bridge_alias") == "cmip7.bridge"

    with pytest.raises(KeyError):
        resolver.resolve("bridge")


def test_identifier_resolver_rejects_unqualified_suffix_lookup():
    resolver = IdentifierResolver()

    resolver.register(
        IdentifierSet(
            prefix="alpha",
            suffix="shared",
            id="alpha.shared",
            aliases=(),
        )
    )
    resolver.register(
        IdentifierSet(
            prefix="beta",
            suffix="shared",
            id="beta.shared",
            aliases=(),
        )
    )

    with pytest.raises(KeyError):
        resolver.resolve("shared")


def test_coerce_scoped_identifier_builds_identifier_set_from_id():
    resolved = coerce_scoped_identifier(
        id="atlas.basic",
        suffix="",
        prefix="",
        canonical_label="FixPlan.id",
    )

    assert resolved.id == "atlas.basic"
    assert resolved.prefix == "atlas"
    assert resolved.suffix == "basic"
    assert resolved.identifier_set == IdentifierSet(
        prefix="atlas",
        suffix="basic",
        id="atlas.basic",
        aliases=(),
    )


def test_build_identifier_resolver_registers_identifier_sets():
    resolver = build_identifier_resolver(
        [
            IdentifierSet(
                prefix="atlas",
                suffix="cleanup",
                id="atlas.cleanup",
                aliases=("atlas.encoding_cleanup",),
            )
        ]
    )

    assert resolver.resolve("atlas.cleanup") == "atlas.cleanup"
    assert resolver.resolve("atlas.encoding_cleanup") == "atlas.cleanup"

    with pytest.raises(KeyError):
        resolver.resolve("cleanup")
