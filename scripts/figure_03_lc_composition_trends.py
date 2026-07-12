#!/usr/bin/env python3
"""
Figure 3: Land cover composition trends across 100 global cities (2000-2020).
Outputs: figure_03_lc_composition_trends.png
Data required: city_year_lst_lc.csv

"""

import matplotlib
import pandas as pd
import matplotlib.pyplot as plt

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']

df = pd.read_csv("../data/city_year_lst_lc.csv")

lc_class_map = {1: 'Impervious', 2: 'Vegetation', 3: 'Cropland', 4: 'Water', 5: 'Bare'}
df['LC_class_name'] = df['LC_class'].map(lc_class_map)

# City-level LC percent by year
city_year_lc = df.groupby(['year', 'city', 'LC_class_name'])['LC_percent'].mean().reset_index()

# Sample average (mean across cities)
sample_avg = city_year_lc.groupby(['year', 'LC_class_name'])['LC_percent'].mean().reset_index()

color_map = {
    'Impervious': '#D62728',
    'Vegetation': '#2CA02C',
    'Cropland': '#FF7F0E',
    'Water': '#1F77B4',
    'Bare': '#9467BD'
}

fig, ax = plt.subplots(figsize=(6.7, 4.5))

# Individual city trajectories (thin lines)
for lc_class in color_map.keys():
    lc_data = city_year_lc[city_year_lc['LC_class_name'] == lc_class]
    color = color_map[lc_class]
    for city in lc_data['city'].unique():
        city_data = lc_data[lc_data['city'] == city].sort_values('year')
        if len(city_data) > 1:
            ax.plot(city_data['year'], city_data['LC_percent'],
                    color=color, alpha=0.12, linewidth=0.4, zorder=1)

# Sample average (bold lines)
for lc_class in color_map.keys():
    avg_data = sample_avg[sample_avg['LC_class_name'] == lc_class].sort_values('year')
    ax.plot(avg_data['year'], avg_data['LC_percent'],
            color=color_map[lc_class], linewidth=2.0, label=lc_class,
            marker='o', markersize=3.5, zorder=3)

ax.set_xlabel('Year', fontsize=9, fontweight='bold')
ax.set_ylabel('Percent Land Cover (%)', fontsize=9, fontweight='bold')
ax.tick_params(axis='both', labelsize=7)
ax.legend(loc='best', fontsize=7)
ax.grid(True, alpha=0.3, linestyle='--')
ax.set_xticks(sorted(df['year'].unique()))
ax.set_ylim(0, max(sample_avg['LC_percent'].max() * 1.1, 10))

plt.tight_layout()
plt.savefig("../outputs/figures/figure_03_lc_composition_trends.png",
            dpi=600, bbox_inches='tight')
plt.show()