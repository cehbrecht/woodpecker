Source values: core (built-in) or plugin:<package> (discovered plugin fix).

## Core

| ID | Name | Description | Categories | Dataset | Priority | Source |
|----|------|-------------|------------|---------|---------|--------|
| woodpecker.normalize_tas_units_to_kelvin | Normalize tas-like units to Kelvin | Converts tas/temp from Celsius-like units to Kelvin. | metadata, units |  | 30 | core |
| woodpecker.merge_equivalent_dimensions | Merge equivalent dimensions | Merges two or more same-sized dimensions into the first configured dimension. | structure |  | 32 | core |
| woodpecker.ensure_latitude_is_increasing | Ensure latitude is increasing | Flips datasets with decreasing latitude coordinates to increasing order. | structure |  | 33 | core |
| woodpecker.rename_variables | Rename variables and dimensions | Renames variables, coordinates, and dimensions from configured candidate names. | structure |  | 33 | core |
| woodpecker.remove_coordinate_fill_value_encodings | Remove coordinate FillValue encodings | Removes _FillValue encoding entries from common coordinate variables. | metadata, structure |  | 34 | core |
| woodpecker.promote_missing_dimension_coords | Promote missing dimension coordinates | Creates coordinate variables for dimensions that have no coordinate. | structure |  | 34 | core |
| woodpecker.set_coordinate_variables | Set coordinate variables | Moves configured variables into the coordinate set. | structure, metadata |  | 35 | core |
| woodpecker.convert_units | Convert variable units | Converts configured variables or coordinates to target units. | metadata, units |  | 36 | core |
| woodpecker.normalize_longitude_convention | Normalize longitude convention | Wraps configured longitude coordinates to a target convention. | coordinates |  | 37 | core |
| woodpecker.drop_variables | Drop variables | Drops configured variables or coordinates. | structure |  | 38 | core |

## Plugin: woodpecker_atlas_plugin

| ID | Name | Description | Categories | Dataset | Priority | Source |
|----|------|-------------|------------|---------|---------|--------|
| atlas.encoding_cleanup | ATLAS encoding cleanup | Applies rook-equivalent ATLAS deflation/encoding cleanup. | encoding | ATLAS | 20 | plugin:woodpecker_atlas_plugin |
| atlas.project_id_normalization | ATLAS project_id normalization | Adds or normalizes ATLAS project_id from dataset identifier prefix. | metadata | ATLAS | 21 | plugin:woodpecker_atlas_plugin |

## Plugin: woodpecker_cmip6_decadal_plugin

| ID | Name | Description | Categories | Dataset | Priority | Source |
|----|------|-------------|------------|---------|---------|--------|
| cmip6_decadal.time_metadata | Decadal time metadata | Ensures CMIP6-decadal time coordinate has long_name='valid_time'. | metadata | CMIP6-decadal | 10 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.calendar_normalization | Decadal calendar normalization | Normalizes CMIP6-decadal time calendar from proleptic_gregorian to standard. | metadata, calendar | CMIP6-decadal | 11 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.realization_variable | Decadal realization variable | Adds realization data variable from realization_index for CMIP6-decadal datasets. | metadata | CMIP6-decadal | 12 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.coordinates_encoding_cleanup | Decadal coordinates encoding cleanup | Removes stale 'coordinates' encoding entries from realization and bounds variables in CMIP6-decadal datasets. | encoding, metadata | CMIP6-decadal | 13 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.realization_comment_normalization | Decadal realization comment normalization | Normalizes realization comment to the full CMIP6-decadal ripf guidance text. | metadata | CMIP6-decadal | 14 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.realization_dtype_normalization | Decadal realization dtype normalization | Normalizes realization data variable dtype to int32 for CMIP6-decadal datasets. | metadata, structure | CMIP6-decadal | 15 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.fillvalue_encoding_cleanup | Decadal _FillValue encoding cleanup | Removes stale '_FillValue' encoding entries from realization and bounds variables in CMIP6-decadal datasets. | encoding, metadata | CMIP6-decadal | 16 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.further_info_url_normalization | Decadal further_info_url normalization | Normalizes malformed CMIP6-decadal further_info_url variant separators from '-' to '.'. | metadata | CMIP6-decadal | 17 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.start_token_normalization | Decadal start token normalization | Normalizes CMIP6-decadal startdate and sub_experiment_id to the canonical sYYYY11 token. | metadata | CMIP6-decadal | 18 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.realization_long_name_normalization | Decadal realization long_name normalization | Normalizes realization long_name metadata to 'realization' for CMIP6-decadal datasets. | metadata | CMIP6-decadal | 19 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.realization_index_normalization | Decadal realization_index normalization | Normalizes CMIP6-decadal realization_index global attribute to integer type. | metadata | CMIP6-decadal | 20 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.leadtime_metadata_normalization | Decadal leadtime metadata normalization | Normalizes CMIP6-decadal leadtime metadata (units, long_name, standard_name). | metadata | CMIP6-decadal | 21 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.model_global_attributes | Decadal model global attributes | Normalizes model-specific global metadata fields for CMIP6-decadal datasets. | metadata | CMIP6-decadal | 22 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.reftime_coordinate | Decadal reftime coordinate | Adds or normalizes CMIP6-decadal scalar reftime coordinate and metadata. | metadata, structure | CMIP6-decadal | 23 | plugin:woodpecker_cmip6_decadal_plugin |
| cmip6_decadal.leadtime_coordinate | Decadal leadtime coordinate | Adds or normalizes CMIP6-decadal leadtime coordinate values from time and reftime. | metadata, structure | CMIP6-decadal | 24 | plugin:woodpecker_cmip6_decadal_plugin |

## Plugin: woodpecker_cmip6_plugin

| ID | Name | Description | Categories | Dataset | Priority | Source |
|----|------|-------------|------------|---------|---------|--------|
| cmip6.dummy_placeholder | CMIP6 dummy placeholder | Dummy placeholder for future non-decadal CMIP6 fixes. | metadata | cmip6 | 40 | plugin:woodpecker_cmip6_plugin |

## Plugin: woodpecker_cmip7_plugin

| ID | Name | Description | Categories | Dataset | Priority | Source |
|----|------|-------------|------------|---------|---------|--------|
| cmip7.ensure_project_id_present | Ensure project_id is present (plugin) | Sets project_id from dataset identifier metadata when missing. | metadata | CMIP7 | 41 | plugin:woodpecker_cmip7_plugin |
| cmip7.rename_temp_variable_to_tas | Rename temp variable to tas (plugin) | Renames data variable temp to tas when tas is missing. | structure, metadata | CMIP7 | 42 | plugin:woodpecker_cmip7_plugin |
| cmip7.configurable_reformat_bridge | Configurable CMIP7 reformat bridge (plugin) | Applies workflow-driven variable/dimension remapping and selected metadata updates. | structure, metadata | CMIP7 | 43 | plugin:woodpecker_cmip7_plugin |

## Plugin: woodpecker_xmip_plugin

| ID | Name | Description | Categories | Dataset | Priority | Source |
|----|------|-------------|------------|---------|---------|--------|
| xmip.rename_cmip6_axes | Rename CMIP6 axes | Normalizes common CMIP6 dimension and coordinate names to x, y, lev, lon, lat, and bounds names. | structure | CMIP6 | 42 | plugin:woodpecker_xmip_plugin |
| xmip.mark_spatial_coords | Mark spatial coordinates | Moves known spatial, vertical, and bounds variables into the coordinate set. | structure, metadata | CMIP6 | 42 | plugin:woodpecker_xmip_plugin |
| xmip.broadcast_lon_lat | Broadcast lon/lat coordinates | Ensures lon and lat coordinates are available as two-dimensional grid coordinates when possible. | structure | CMIP6 | 42 | plugin:woodpecker_xmip_plugin |
| xmip.normalize_coordinate_units | Normalize coordinate units | Converts supported CMIP6 coordinate units to xMIP target units, currently lev to meters. | metadata, coordinates | CMIP6 | 42 | plugin:woodpecker_xmip_plugin |
| xmip.replace_xy_with_nominal_lon_lat | Replace x/y with nominal lon/lat | Approximates x and y coordinate values from representative lon/lat slices and sorts the grid. | coordinates | CMIP6 | 42 | plugin:woodpecker_xmip_plugin |
| xmip.normalize_lon_lat_bounds | Normalize lon/lat bounds | Normalizes lon/lat bounds shape and naming, including vertex-style bounds. | structure, coordinates | CMIP6 | 42 | plugin:woodpecker_xmip_plugin |
| xmip.sort_vertex_order | Sort vertex order | Sorts grid-cell vertices into a consistent lower-left, upper-left, upper-right, lower-right order. | coordinates | CMIP6 | 42 | plugin:woodpecker_xmip_plugin |
| xmip.convert_bounds_to_vertices | Convert bounds to vertices | Creates rectangular lon/lat vertex coordinates from lon/lat bounds when vertices are missing. | structure, coordinates | CMIP6 | 42 | plugin:woodpecker_xmip_plugin |
| xmip.convert_vertices_to_bounds | Convert vertices to bounds | Creates lon/lat bounds from vertex-style lon/lat coordinates when bounds are missing. | structure, coordinates | CMIP6 | 42 | plugin:woodpecker_xmip_plugin |
| xmip.fix_known_cmip6_metadata | Fix known CMIP6 metadata | Applies selected known CMIP6 metadata corrections from xMIP preprocessing. | metadata | CMIP6 | 42 | plugin:woodpecker_xmip_plugin |
| xmip.drop_helper_grid_coords | Drop helper grid coordinates | Drops helper bnds and vertex coordinate variables after bounds and vertices are normalized. | structure | CMIP6 | 42 | plugin:woodpecker_xmip_plugin |
