| Code | Name | Description | Categories | Dataset | Priority |
|------|------|-------------|------------|---------|---------|
| CMIP6D01 | Decadal time metadata | Ensures CMIP6-decadal time coordinate has long_name='valid_time'. | metadata | CMIP6-decadal | 10 |
| CMIP6D02 | Decadal calendar normalization | Normalizes CMIP6-decadal time calendar from proleptic_gregorian to standard. | metadata, calendar | CMIP6-decadal | 11 |
| CMIP6D03 | Decadal realization variable | Adds realization data variable from realization_index for CMIP6-decadal datasets. | metadata | CMIP6-decadal | 12 |
| CMIP6D04 | Decadal coordinates encoding cleanup | Removes stale 'coordinates' encoding entries from realization and bounds variables in CMIP6-decadal datasets. | encoding, metadata | CMIP6-decadal | 13 |
| CMIP6D05 | Decadal realization comment normalization | Normalizes realization comment to the full CMIP6-decadal ripf guidance text. | metadata | CMIP6-decadal | 14 |
| CMIP6D06 | Decadal realization dtype normalization | Normalizes realization data variable dtype to int32 for CMIP6-decadal datasets. | metadata, structure | CMIP6-decadal | 15 |
| CMIP6D07 | Decadal _FillValue encoding cleanup | Removes stale '_FillValue' encoding entries from realization and bounds variables in CMIP6-decadal datasets. | encoding, metadata | CMIP6-decadal | 16 |
| CMIP6D08 | Decadal further_info_url normalization | Normalizes malformed CMIP6-decadal further_info_url variant separators from '-' to '.'. | metadata | CMIP6-decadal | 17 |
| CMIP6D09 | Decadal start token normalization | Normalizes CMIP6-decadal startdate and sub_experiment_id to the canonical sYYYY11 token. | metadata | CMIP6-decadal | 18 |
| CMIP6D10 | Decadal realization long_name normalization | Normalizes realization long_name metadata to 'realization' for CMIP6-decadal datasets. | metadata | CMIP6-decadal | 19 |
| ATLAS01 | ATLAS encoding cleanup | Applies rook-equivalent ATLAS deflation/encoding cleanup. | encoding | ATLAS | 20 |
| CMIP6D11 | Decadal realization_index normalization | Normalizes CMIP6-decadal realization_index global attribute to integer type. | metadata | CMIP6-decadal | 20 |
| ATLAS02 | ATLAS project_id normalization | Adds or normalizes ATLAS project_id from dataset identifier prefix. | metadata | ATLAS | 21 |
| CMIP6D12 | Decadal leadtime metadata normalization | Normalizes CMIP6-decadal leadtime metadata (units, long_name, standard_name). | metadata | CMIP6-decadal | 21 |
| CMIP6D13 | Decadal model global attributes | Normalizes model-specific global metadata fields for CMIP6-decadal datasets. | metadata | CMIP6-decadal | 22 |
| CMIP6D14 | Decadal reftime coordinate | Adds or normalizes CMIP6-decadal scalar reftime coordinate and metadata. | metadata, structure | CMIP6-decadal | 23 |
| CMIP6D15 | Decadal leadtime coordinate | Adds or normalizes CMIP6-decadal leadtime coordinate values from time and reftime. | metadata, structure | CMIP6-decadal | 24 |
| CMIP601 | CMIP6 dummy placeholder | Dummy placeholder for future non-decadal CMIP6 fixes. | metadata | cmip6 | 40 |
| ESMVAL01 | Normalize tas-like units to Kelvin | Prototype ESMVal-style fix: converts tas/temp from Celsius-like units to Kelvin. | metadata, units | ESMVal | 40 |
| ESMVAL02 | Ensure project_id is present | Sets project_id from dataset identifier metadata when missing. | metadata | ESMVal | 41 |
| ESMVAL03 | Rename temp variable to tas | Renames data variable temp to tas when tas is missing. | structure, metadata | ESMVal | 42 |
| ESMVAL04 | Ensure latitude is increasing | Flips datasets with decreasing latitude coordinates to increasing order. | structure | ESMVal | 43 |
| ESMVAL05 | Remove coordinate FillValue encodings | Removes _FillValue encoding entries from common coordinate variables. | metadata, structure | ESMVal | 44 |
| CMIP6DG01 | CMIP6 Decadal: full fix suite | Applies all CMIP6-decadal fixes (CMIP6D01–CMIP6D15) in sequence: calendar, encoding, realization metadata, start-token normalisation, model-specific global attributes, and leadtime/reftime coordinates. | metadata, calendar, encoding, structure | CMIP6-decadal | 99 |