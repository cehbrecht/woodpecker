import pytest

from woodpecker.identifiers import (
    IdentifierResolver,
    IdentifierRules,
    IdentifierSet,
    build_identifier_resolver,
    coerce_scoped_identifier,
)


def test_identifier_rules_build_creates_canonical_identifier_set():
    identifiers = IdentifierRules.build(
        namespace_prefix="cmip7", local_id="configurable_reformat_bridge"
    )

    assert identifiers == IdentifierSet(
        namespace_prefix="cmip7",
        local_id="configurable_reformat_bridge",
        canonical_id="cmip7.configurable_reformat_bridge",
        aliases=(),
    )


def test_identifier_rules_derive_local_id_from_name_strips_fix_and_plan_suffixes():
    assert (
        IdentifierRules.derive_local_id_from_name("NormalizeTasUnitsToKelvinFix")
        == "normalize_tas_units_to_kelvin"
    )
    assert IdentifierRules.derive_local_id_from_name("AtlasMonitoringPlan") == "atlas_monitoring"


def test_identifier_rules_expand_aliases_for_local_and_qualified_values():
    aliases = IdentifierRules.expand_aliases(
        namespace_prefix="atlas",
        canonical_id="atlas.encoding_cleanup",
        declared_aliases=["cleanup", "atlas.cleanup2"],
    )

    assert aliases == ("cleanup", "atlas.cleanup", "atlas.cleanup2")


def test_identifier_rules_reject_invalid_alias_syntax():
    with pytest.raises(ValueError, match="Invalid alias"):
        IdentifierRules.expand_aliases(
            namespace_prefix="atlas",
            canonical_id="atlas.encoding_cleanup",
            declared_aliases=["bad-alias"],
        )


def test_identifier_resolver_registers_and_resolves_canonical_and_alias_forms():
    resolver = IdentifierResolver()
    resolver.register(
        IdentifierSet(
            namespace_prefix="cmip7",
            local_id="bridge",
            canonical_id="cmip7.bridge",
            aliases=("bridge_alias", "cmip7.bridge_alias"),
        )
    )

    assert resolver.resolve("cmip7.bridge") == "cmip7.bridge"
    assert resolver.resolve("bridge") == "cmip7.bridge"
    assert resolver.resolve("bridge_alias") == "cmip7.bridge"
    assert resolver.resolve("cmip7.bridge_alias") == "cmip7.bridge"


def test_identifier_resolver_rejects_ambiguous_identifiers():
    resolver = IdentifierResolver()

    resolver.register(
        IdentifierSet(
            namespace_prefix="alpha",
            local_id="shared",
            canonical_id="alpha.shared",
            aliases=(),
        )
    )
    resolver.register(
        IdentifierSet(
            namespace_prefix="beta",
            local_id="shared",
            canonical_id="beta.shared",
            aliases=(),
        )
    )

    with pytest.raises(ValueError, match="Ambiguous identifier"):
        resolver.resolve("shared")


def test_coerce_scoped_identifier_builds_identifier_set_from_canonical_id():
    resolved = coerce_scoped_identifier(
        canonical_id="atlas.basic",
        local_id="",
        namespace_prefix="",
        canonical_label="FixPlan.id",
    )

    assert resolved.canonical_id == "atlas.basic"
    assert resolved.namespace_prefix == "atlas"
    assert resolved.local_id == "basic"
    assert resolved.identifier_set == IdentifierSet(
        namespace_prefix="atlas",
        local_id="basic",
        canonical_id="atlas.basic",
        aliases=(),
    )


def test_build_identifier_resolver_registers_identifier_sets():
    resolver = build_identifier_resolver(
        [
            IdentifierSet(
                namespace_prefix="atlas",
                local_id="cleanup",
                canonical_id="atlas.cleanup",
                aliases=("encoding_cleanup",),
            )
        ]
    )

    assert resolver.resolve("atlas.cleanup") == "atlas.cleanup"
    assert resolver.resolve("cleanup") == "atlas.cleanup"
    assert resolver.resolve("encoding_cleanup") == "atlas.cleanup"
