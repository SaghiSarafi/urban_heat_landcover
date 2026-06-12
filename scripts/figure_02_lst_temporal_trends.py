#!/usr/bin/env python3
"""
Figure 2: Temporal dynamics of LST by land cover class with global land temperature (2000–2020).
Outputs: figure_02_lst_temporal_trends.png
Data required: city_year_lst_lc.csv
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Load data
df = pd.read_csv("../data/city_year_lst_lc.csv")
df = df.dropna(subset=['mean_LST', 'max_LST'])

lc_class_map = {1: 'Impervious', 2: 'Vegetation', 3: 'Cropland', 4: 'Water', 5: 'Bare'}
df['LC_class_name'] = df['LC_class'].map(lc_class_map)
df['year'] = df['year'].astype(int)

grouped = df.groupby(['year', 'LC_class_name']).agg({'mean_LST': 'mean', 'max_LST': 'mean'}).reset_index()

# ENSO years from NOAA CPC ONI (peak years)
el_nino_years = [2002, 2004, 2006, 2009, 2015, 2018]
la_nina_years = [2000, 2005, 2007, 2008, 2010, 2011, 2016, 2017, 2020]

# Berkeley Earth land temperature (Kelvin)
berkeley_years = list(range(2000, 2021))
berkeley_land_temp_k = [
    286.90, 287.07, 287.17, 287.20, 287.18, 287.30, 287.23, 287.25,
    287.20, 287.30, 287.40, 287.33, 287.40, 287.45, 287.50, 287.70,
    287.80, 287.70, 287.60, 287.65, 287.75
]

# Plotting
plt.figure(figsize=(16, 9))
sns.set(style="whitegrid")

color_map = {
    'Impervious': '#E69F00',
    'Vegetation': '#009E73',
    'Cropland': '#F0E442',
    'Water': '#56B4E9',
    'Bare': '#CC79A7'
}
line_styles = {'mean_LST': '-', 'max_LST': '--'}

for lc_class in color_map.keys():
    subset = grouped[grouped['LC_class_name'] == lc_class]
    for metric in ['mean_LST', 'max_LST']:
        display_label = f"{lc_class} (mean)" if metric == 'mean_LST' else f"{lc_class} (max)"
        plt.plot(subset['year'], subset[metric],
                 linestyle=line_styles[metric],
                 color=color_map[lc_class],
                 linewidth=2.5 if metric == 'mean_LST' else 1.8,
                 label=display_label, zorder=3)

plt.plot(berkeley_years, berkeley_land_temp_k, color='black', linewidth=3.5,
         label='Global Mean Land Temp (K)', zorder=4, alpha=0.9)

for i, year in enumerate(el_nino_years):
    plt.axvline(x=year, color='#C0392B', linestyle=':', alpha=0.6, linewidth=2.2,
                label='El Niño' if i == 0 else "", zorder=1)
for i, year in enumerate(la_nina_years):
    plt.axvline(x=year, color='#27AE60', linestyle=':', alpha=0.6, linewidth=2.2,
                label='La Niña' if i == 0 else "", zorder=1)

plt.title("Temporal Dynamics of LST by LC Class with Global Land Temperature (2000–2020)",
          fontsize=18, fontweight='bold', pad=15)
plt.xlabel("Year", fontsize=15, fontweight='bold')
plt.ylabel("Temperature (K)", fontsize=15, fontweight='bold')
plt.xticks(sorted(df['year'].unique()), fontsize=13)
plt.yticks(fontsize=13)
plt.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=11)
plt.xlim(1999.5, 2020.5)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("../outputs/figures/figure_02_lst_temporal_trends.png", dpi=300, bbox_inches='tight')
plt.show()

print("\nENSO years used:")
print(f"El Niño  : {el_nino_years}")
print(f"La Niña  : {la_nina_years}")