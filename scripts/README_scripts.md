# Python Analysis Scripts

This folder contains all Python scripts used to generate the figures and tables in the paper.

## Run order
Note: Figures 1 and 2 are introductory (study cities map; area-ratio covariate
distribution) and are not included in this run order.

1. 00_fetch_berkeley_land.py → downloads global land-only temperature data (required before step 8)
2. 00_fetch_noaa_oni.py → downloads NOAA ONI data and classifies El Niño/La Niña years (required before step 8)
3. table_03_correlations_2020.py → Table 3
4. table_04_correlations_delta.py → Table 4
5. table_05_net_change_regression.py → Table 5 (single merged model: 5 LC-class predictors plus two boundary-sensitivity covariates; requires ../data/boundary_covariates_ghsl_compactness.csv, produced by GEE/03_boundary_covariates_ghsl_compactness.js)
6. table_06_transition_analysis.py → Table 6
7. table_07_rti_statistics.py → Table 7
8. figure_03_lst_temporal_trends.py → Figure 3 (requires steps 1 and 2's output)
9. figure_04_lc_composition_trends.py → Figure 4
10. figure_05_lc_vs_lst_scatter_2020.py → Figure 5
11. figure_06_delta_lc_vs_delta_lst.py → Figure 6
12. figure_07_rti_distributions.py → Figure 7 (requires Tables 6-7's underlying data pipeline)
13. figure_08_rti_compositional_sensitivity.py → Figure 8

## Notes
Tables 3 and 4 (table_03_correlations_2020.py, table_04_correlations_delta.py) include
Benjamini-Hochberg correction for multiple comparisons (Benjamini and Hochberg 1995),
computed via statsmodels.stats.multitest. No additional dependencies required —
statsmodels is already listed in requirements.txt.

Table 5 (table_05_net_change_regression.py) runs a single regression with 7 predictors:
the 5 LC-class net-change variables plus two boundary-sensitivity covariates (area ratio,
perimeter-area ratio) computed from GHS-SMOD via GEE/03_boundary_covariates_ghsl_compactness.js.
Baku City is excluded from this model — see that script's header comments for why. One city (Baku) is excluded due to a boundary data-quality issue, reducing the sample to 73 cities; three additional cities (Brasília, Hobart, National Capital District) lack a usable area-ratio value and are also excluded, giving a final sample of 70. The table's reported n reflects this.

## Setup
pip install -r requirements.txt
Place city_year_lst_lc.csv, pixel_transitions_thermal_2000_2020.csv, and
boundary_covariates_ghsl_compactness.csv in the same directory as the scripts,
or update the file paths.

## Outputs
Figures saved as PNG (600 dpi) in outputs/figures/
Tables saved as CSV in outputs/tables/
