#!/usr/bin/env python3
"""
Table 3: Pearson correlations between LC% and LST metrics (mean, max, top-10%) for 2020.
Outputs: table_03_correlations_2020.csv
Data required: city_year_lst_lc.csv
"""

import pandas as pd
from scipy import stats

df = pd.read_csv("../data/city_year_lst_lc.csv")
df_2020 = df[df['year'] == 2020].copy()

LC_MAP = {1: 'Impervious', 2: 'Vegetation', 3: 'Cropland', 4: 'Water', 5: 'Bare'}

rows = []
for lc, name in LC_MAP.items():
    sub = df_2020[df_2020['LC_class'] == lc].dropna(
        subset=['LC_percent', 'mean_LST', 'max_LST', 'mean_top10_LST'])
    n = len(sub)
    for metric, col in [('LST', 'mean_LST'), ('LSTMax', 'max_LST'), ('LSTMax10', 'mean_top10_LST')]:
        r, p = stats.pearsonr(sub['LC_percent'], sub[col])
        rows.append({'LC Class': name, 'Metric': metric,
                     'r': round(r, 4), 'R²': round(r**2, 4),
                     'p': round(p, 4), 'n': n})

table = pd.DataFrame(rows)
table_wide = table.pivot_table(index='LC Class', columns='Metric',
                               values=['r', 'R²', 'p'], aggfunc='first')
table_wide.columns = [f'{m} {v}' for v, m in table_wide.columns]
col_order = (['LST r', 'LST R²', 'LST p'] +
             ['LSTMax r', 'LSTMax R²', 'LSTMax p'] +
             ['LSTMax10 r', 'LSTMax10 R²', 'LSTMax10 p'])
table_wide = table_wide.reindex(['Impervious', 'Vegetation', 'Cropland', 'Water', 'Bare'])[col_order]

table_wide.to_csv("../outputs/tables/table_03_correlations_2020.csv")
print(table_wide.to_string())