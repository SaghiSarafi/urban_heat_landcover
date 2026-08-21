#!/usr/bin/env python3
"""
Figure 6: Scatter plots of ΔLC% vs ΔLST (mean LST) for each LC class (2000-2020).
Includes regression lines and correlation coefficients.
Outputs: figure_06_delta_lc_vs_delta_lst.png
Data required: city_year_lst_lc.csv

"""

import matplotlib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']

df = pd.read_csv("../data/city_year_lst_lc.csv")

df_2000 = df[df['year'] == 2000]
df_2020 = df[df['year'] == 2020]

pivot_2000 = df_2000.pivot_table(index='city', columns='LC_class', values=['LC_percent', 'mean_LST'])
pivot_2020 = df_2020.pivot_table(index='city', columns='LC_class', values=['LC_percent', 'mean_LST'])

delta_df = pd.DataFrame(index=pivot_2000.index)
lc_map = {1: 'impervious', 2: 'vegetation', 3: 'cropland', 4: 'water', 5: 'bare'}
for lc, name in lc_map.items():
    delta_df[f'delta_{name}'] = pivot_2020['LC_percent'][lc] - pivot_2000['LC_percent'][lc]
delta_df['delta_mean_LST'] = pivot_2020['mean_LST'][1] - pivot_2000['mean_LST'][1]
delta_df_clean = delta_df.dropna()

# Taller aspect ratio (3 rows) at the same ~170 mm final print width.
fig, axes = plt.subplots(3, 2, figsize=(6.7, 7.5))
axes = axes.flatten()

lc_labels = ['impervious', 'vegetation', 'cropland', 'water', 'bare']
lc_display = ['Impervious', 'Vegetation', 'Cropland', 'Water', 'Bare']

for i, (lc, display) in enumerate(zip(lc_labels, lc_display)):
    x = delta_df_clean[f'delta_{lc}']
    y = delta_df_clean['delta_mean_LST']
    sns.regplot(x=x, y=y, ax=axes[i],
                scatter_kws={'s': 14}, line_kws={'color': 'red', 'linewidth': 1.2})
    r, p = pearsonr(x, y)
    axes[i].set_title(f'Change in {display} Cover vs \u0394LST (2000-2020)\nr = {r:.3f}, p = {p:.4f}',
                       fontsize=8, fontweight='bold')
    axes[i].set_xlabel(f'Change in {display} Cover (%)', fontsize=7.5)
    axes[i].set_ylabel('Change in Mean LST (K)', fontsize=7.5)
    axes[i].tick_params(axis='both', labelsize=6.5)

axes[5].axis('off')
plt.tight_layout()
plt.savefig("../outputs/figures/figure_06_delta_lc_vs_delta_lst.png",
            dpi=600, bbox_inches='tight')
plt.show()