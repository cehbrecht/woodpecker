Source values: core (built-in) or plugin:<package> (discovered plugin fix).

## Core

| ID | Name | Description | Categories | Dataset | Priority | Source |
|----|------|-------------|------------|---------|---------|--------|
| woodpecker.normalize_tas_units_to_kelvin | Normalize tas-like units to Kelvin | Converts tas/temp from Celsius-like units to Kelvin. | metadata, units |  | 30 | core |
| woodpecker.merge_equivalent_dimensions | Merge equivalent dimensions | Merges two or more same-sized dimensions into the first configured dimension. | structure |  | 32 | core |
| woodpecker.ensure_latitude_is_increasing | Ensure latitude is increasing | Flips datasets with decreasing latitude coordinates to increasing order. | structure |  | 33 | core |
| woodpecker.remove_coordinate_fill_value_encodings | Remove coordinate FillValue encodings | Removes _FillValue encoding entries from common coordinate variables. | metadata, structure |  | 34 | core |
