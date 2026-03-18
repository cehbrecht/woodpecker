| Code | Name | Description | Categories | Dataset | Priority |
|------|------|-------------|------------|---------|---------|
| CMIP6D01 | Decadal time metadata | Ensures CMIP6-decadal time coordinate has long_name='valid_time'. | metadata | CMIP6-decadal | 10 |
| CMIP6D02 | Decadal calendar normalization | Normalizes CMIP6-decadal time calendar from proleptic_gregorian to standard. | metadata, calendar | CMIP6-decadal | 11 |
| CMIP6D03 | Decadal realization variable | Adds realization data variable from realization_index for CMIP6-decadal datasets. | metadata | CMIP6-decadal | 12 |
| CMIP6D04 | Decadal coordinates encoding cleanup | Removes stale 'coordinates' encoding entries from realization and bounds variables in CMIP6-decadal datasets. | encoding, metadata | CMIP6-decadal | 13 |
| ATLAS01 | ATLAS encoding cleanup | Applies rook-equivalent ATLAS deflation/encoding cleanup. | encoding | ATLAS | 20 |
| ATLAS02 | ATLAS project_id normalization | Adds or normalizes ATLAS project_id from dataset identifier prefix. | metadata | ATLAS | 21 |
| CMIP601 | CMIP6 dummy placeholder | Dummy placeholder for future non-decadal CMIP6 fixes. | metadata | cmip6 | 40 |