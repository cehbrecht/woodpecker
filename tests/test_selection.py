from woodpecker.selection import select_fixes


def test_select_fixes_respects_ordered_identifiers_sequence():
    fixes = select_fixes(
        ordered_identifiers=[
            "woodpecker.normalize_tas_units_to_kelvin",
            "woodpecker.ensure_latitude_is_increasing",
        ],
        strict_identifiers=True,
    )
    ordered = [fix.canonical_id for fix in fixes]

    assert ordered[:2] == [
        "woodpecker.normalize_tas_units_to_kelvin",
        "woodpecker.ensure_latitude_is_increasing",
    ]
