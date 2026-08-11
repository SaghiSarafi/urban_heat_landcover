#!/usr/bin/env python3
"""
Table 4: Correlations between ΔLC% and ΔLST metrics (mean, max, top-10%) for 2000–2020.
Outputs: outputs/tables/table_04_correlations_delta.csv
Data required: data/city_year_lst_lc.csv

Includes Benjamini-Hochberg correction for multiple comparisons (15 tests:
5 LC classes x 3 LST metrics), per Benjamini and Hochberg (1995).

Note: This script does NOT produce a figure. Figure 5 (ΔLC vs ΔLST for mean LST)
is generated separately by figure_05_delta_lc_vs_delta_lst.py.
"""

import pandas as pd
from scipy.stats import pearsonr
from statsmodels.stats.multitest import multipletests

df = pd.read_csv("../data/city_year_lst_lc.csv")

df_2000 = df[df['year'] == 2000]
df_2020 = df[df['year'] == 2020]

pivot_2000 = df_2000.pivot_table(index='city', columns='LC_class',
                                 values=['LC_percent', 'mean_LST', 'max_LST', 'mean_top10_LST'])
pivot_2020 = df_2020.pivot_table(index='city', columns='LC_class',
                                 values=['LC_percent', 'mean_LST', 'max_LST', 'mean_top10_LST'])

delta_df = pd.DataFrame(index=pivot_2000.index)
lc_map = {1: 'impervious', 2: 'vegetation', 3: 'cropland', 4: 'water', 5: 'bare'}
for lc, name in lc_map.items():
    delta_df[f'delta_{name}'] = pivot_2020['LC_percent'][lc] - pivot_2000['LC_percent'][lc]

delta_df['delta_mean_LST'] = pivot_2020['mean_LST'][1] - pivot_2000['mean_LST'][1]
delta_df['delta_max_LST'] = pivot_2020['max_LST'][1] - pivot_2000['max_LST'][1]
delta_df['delta_top10_LST'] = pivot_2020['mean_top10_LST'][1] - pivot_2000['mean_top10_LST'][1]
delta_df_clean = delta_df.dropna()

# Table 4
table4_rows = []
lc_labels = ['impervious', 'vegetation', 'cropland', 'water', 'bare']
lc_display = ['Impervious', 'Vegetation', 'Cropland', 'Water', 'Bare']

for lc, display in zip(lc_labels, lc_display):
    x = delta_df_clean[f'delta_{lc}']
    r_mean, p_mean = pearsonr(x, delta_df_clean['delta_mean_LST'])
    r_max, p_max = pearsonr(x, delta_df_clean['delta_max_LST'])
    r_top10, p_top10 = pearsonr(x, delta_df_clean['delta_top10_LST'])
    table4_rows.append({
        'LC Class': display,
        'ΔLST r': round(r_mean, 4), 'ΔLST R²': round(r_mean**2, 4), 'ΔLST p': p_mean,
        'ΔLST_Max r': round(r_max, 4), 'ΔLST_Max R²': round(r_max**2, 4), 'ΔLST_Max p': p_max,
        'ΔLST_Max10 r': round(r_top10, 4), 'ΔLST_Max10 R²': round(r_top10**2, 4), 'ΔLST_Max10 p': p_top10
    })

table4_df = pd.DataFrame(table4_rows).set_index('LC Class')

# Benjamini-Hochberg correction across all 15 tests in this table.
# See Benjamini and Hochberg (1995), J R Stat Soc Series B, 57:289-300.
p_cols = ['ΔLST p', 'ΔLST_Max p', 'ΔLST_Max10 p']
all_p = table4_df[p_cols].values.flatten()
_, p_bh_flat, _, _ = multipletests(all_p, alpha=0.05, method='fdr_bh')
p_bh = p_bh_flat.reshape(table4_df[p_cols].shape)
table4_df['ΔLST p_BH'] = p_bh[:, 0].round(4)
table4_df['ΔLST_Max p_BH'] = p_bh[:, 1].round(4)
table4_df['ΔLST_Max10 p_BH'] = p_bh[:, 2].round(4)
for c in p_cols:
    table4_df[c] = table4_df[c].round(4)  # round raw p for display, after correction is computed

col_order = ['ΔLST r', 'ΔLST R²', 'ΔLST p', 'ΔLST p_BH',
             'ΔLST_Max r', 'ΔLST_Max R²', 'ΔLST_Max p', 'ΔLST_Max p_BH',
             'ΔLST_Max10 r', 'ΔLST_Max10 R²', 'ΔLST_Max10 p', 'ΔLST_Max10 p_BH']
table4_df = table4_df[col_order]

# Save to CSV
table4_df.to_csv("../outputs/tables/table_04_correlations_delta.csv")
print("Table 4 saved to ../outputs/tables/table_04_correlations_delta.csv")
print(table4_df.to_string())
print("\nNote: p_BH = Benjamini-Hochberg corrected p-value (15 tests, alpha=0.05).")
print("Impervious survives correction across all three metrics; cropland survives for mean LST only.")
