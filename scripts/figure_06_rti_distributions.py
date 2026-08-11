#!/usr/bin/env python3
"""
Figure 6: Distribution of Relative Temperature Index (RTI) values by land
cover class across all city-years, shown as boxplots (complements the
summary statistics in Table 7).

Outputs: figure_06_rti_distributions.png
Data required: city_year_lst_lc.csv

PRINT SIZING NOTE: figsize is chosen to match the ~170 mm final print
width required by the journal directly, rather than a larger on-screen
size that gets shrunk later (see figure_02 script for the full rationale).
"""

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']

df = pd.read_csv("../data/city_year_lst_lc.csv")

# Compute RTI exactly as in table_07_rti_statistics.py: class mean LST
# divided by the city-year mean LST across all five classes.
df_pivot = df.pivot_table(index=['city', 'year', 'LC_class'], values='mean_LST', aggfunc='mean')
city_year_means = df_pivot.groupby(['city', 'year']).mean().reset_index().rename(
    columns={'mean_LST': 'city_mean_LST'})
df_rti = df_pivot.reset_index().merge(city_year_means, on=['city', 'year'])
df_rti['RTI'] = df_rti['mean_LST'] / df_rti['city_mean_LST']

class_map = {1: 'Impervious', 2: 'Vegetation', 3: 'Cropland', 4: 'Water', 5: 'Bare'}
df_rti['LC_name'] = df_rti['LC_class'].map(class_map)

order = ['Impervious', 'Vegetation', 'Cropland', 'Water', 'Bare']
colors = {
    'Impervious': '#D62728',
    'Vegetation': '#2CA02C',
    'Cropland': '#FF7F0E',
    'Water': '#1F77B4',
    'Bare': '#9467BD'
    }
data_by_class = [df_rti[df_rti['LC_name'] == c]['RTI'].dropna().values for c in order]

fig, ax = plt.subplots(figsize=(6.7, 4.2))
bp = ax.boxplot(data_by_class, tick_labels=order, patch_artist=True, widths=0.55,
                 medianprops=dict(color='black', linewidth=1.3),
                 flierprops=dict(marker='o', markersize=2.5, alpha=0.35, markeredgecolor='none'))
for patch, cls in zip(bp['boxes'], order):
    patch.set_facecolor(colors[cls])
    patch.set_alpha(0.75)

ax.axhline(1.0, color='black', linestyle='--', linewidth=0.9, alpha=0.6, zorder=1)
ax.set_ylabel('Relative Temperature Index (RTI)', fontsize=9, fontweight='bold')
ax.tick_params(axis='both', labelsize=8)
ax.grid(True, alpha=0.3, axis='y', linestyle='--')

plt.tight_layout()
plt.savefig("../outputs/figures/figure_06_rti_distributions.png", dpi=600, bbox_inches='tight')
plt.show()

print("Figure 6 saved to ../outputs/figures/figure_06_rti_distributions.png")
for cls in order:
    vals = df_rti[df_rti['LC_name'] == cls]['RTI'].dropna()
    print(f"  {cls:12s} median={vals.median():.4f}  IQR=[{vals.quantile(0.25):.4f}, {vals.quantile(0.75):.4f}]")
