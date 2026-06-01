from woodpecker.selection import select_fixes


def test_select_fixes_respects_ordered_identifiers_sequence():
    fixes = select_fixes(
        ordered_identifiers=[
            "woodpecker.normalize_tas_units_to_kelvin",
            "woodpecker.ensure_latitude_is_increasing",
        ],
        strict_identifiers=True,
    )
    ordered = [fix.id for fix in fixes]

    assert ordered[:2] == [
        "woodpecker.normalize_tas_units_to_kelvin",
        "woodpecker.ensure_latitude_is_increasing",
    ]


def test_select_fixes_uses_configure_return_value(monkeypatch):
    class ReplacementFunction:
        id = "woodpecker.test"
        configured = True

    class ConfigurableFunction:
        id = "woodpecker.test"
        configured = False

        def configure(self, options):
            _ = options
            return ReplacementFunction()

    monkeypatch.setattr(
        "woodpecker.selection.FixFunctionRegistry.discover", lambda filters=None: [ConfigurableFunction()]
    )
    monkeypatch.setattr(
        "woodpecker.selection.FixFunctionRegistry.resolve_identifier", lambda identifier: identifier
    )

    fixes = select_fixes(
        identifiers=["woodpecker.test"],
        strict_identifiers=True,
        fix_options={"woodpecker.test": {"mode": "x"}},
    )

    assert len(fixes) == 1
    assert getattr(fixes[0], "configured", False) is True
