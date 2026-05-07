Fix plans are curated recipes for selecting and applying fixes to matching datasets.

Source values currently point to integration-test plans used by the examples.

| ID | Description | Match | Steps | Source Files |
|----|-------------|-------|-------|--------------|
| atlas.basic | Concrete Atlas plan for atlas*.nc files | paths: *atlas*.nc | atlas.encoding_cleanup<br>atlas.project_id_normalization | tests/integration/plans/atlas_basic_plan.json |
| cmip6.core_units |  | attrs: project_id=CMIP6 | woodpecker.normalize_tas_units_to_kelvin | tests/integration/plans/cmip6_core_plan.json<br>tests/integration/plans/cmip6_core_plan.yaml |
| cmip7.esa_cci_water_vapour_dotname | CMIP7/ESA CCI dot-name inputs | paths: esacci.WATERVAPOUR.* | woodpecker.merge_equivalent_dimensions<br>cmip7.configurable_reformat_bridge<br>woodpecker.ensure_latitude_is_increasing | tests/integration/plans/esa_cci_water_vapour_plan.json |
| cmip7.esa_cci_water_vapour_zarr | CMIP7/ESA CCI zarr-style inputs | paths: *ESACCI-WATERVAPOUR-*.zarr | cmip7.configurable_reformat_bridge<br>woodpecker.ensure_latitude_is_increasing | tests/integration/plans/esa_cci_water_vapour_plan.json |
