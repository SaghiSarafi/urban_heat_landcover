# Python Analysis Scripts

This folder contains all Python scripts used to generate the figures and tables in the paper.

## Run order
1. 00_fetch_berkeley_land.py → downloads global land-only temperature data (required before step 8)
2. 00_fetch_noaa_oni.py → downloads NOAA ONI data and classifies El Niño/La Niña years (required before step 8)
3. table_03_correlations_2020.py → Table 3
4. table_04_correlations_delta.py → Table 4
5. table_05_net_change_regression.py → Table 5
6. table_06_transition_analysis.py → Tables 6
7. table_07_rti_statistics.py → Table 7
8. figure_02_lst_temporal_trends.py → Figure 2 (requires steps 1 and 2's output)
9. figure_03_lc_composition_trends.py → Figure 3
10. figure_04_lc_vs_lst_scatter_2020.py → Figure 4
11. figure_05_delta_lc_vs_delta_lst.py → Figure 5

## Setup
pip install -r requirements.txt
Place city_year_lst_lc.csv and pixel_transitions_thermal_2000_2020.csv
in the same directory as the scripts, or update the file paths.

## Outputs
Figures saved as PNG (300 dpi) in outputs/figures/
Tables saved as CSV in outputs/tables/
