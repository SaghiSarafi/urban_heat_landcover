#!/usr/bin/env python3
"""
Figure 3: Temporal dynamics of LST by land cover class with global
LAND-ONLY mean temperature (2000-2020).

Data required:
  - ../data/city_year_lst_lc.csv   (your GEE-derived LST/LC data)
  - ../data/raw/berkeley_earth_land_tavg.csv (from 00_fetch_berkeley_land.py)
  - ../data/raw/noaa_oni.csv (from 00_fetch_noaa_oni.py)

Run 00_fetch_berkeley_land.py and 00_fetch_noaa_oni.py first.
"""

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import json

# Use a sans-serif font family (Helvetica/Arial), per journal artwork guidelines.
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']

# ---- Load city/LC LST data -------------------------------------------------
df = pd.read_csv("../data/city_year_lst_lc.csv")
df = df.dropna(subset=['mean_LST', 'max_LST'])

lc_class_map = {1: 'Impervious', 2: 'Vegetation', 3: 'Cropland', 4: 'Water', 5: 'Bare'}
df['LC_class_name'] = df['LC_class'].map(lc_class_map)
df['year'] = df['year'].astype(int)

grouped = df.groupby(['year', 'LC_class_name']).agg(
    {'mean_LST': 'mean', 'max_LST': 'mean'}
).reset_index()

# ---- Load Berkeley Earth LAND-ONLY data (not hardcoded) --------------------
berkeley = pd.read_csv("../data/raw/berkeley_earth_land_tavg.csv")
with open("../data/raw/berkeley_earth_land_tavg.meta.json") as f:
    berkeley_meta = json.load(f)

berkeley_annual = berkeley[(berkeley.month == 6) &
                            (berkeley.year >= 2000) & (berkeley.year <= 2020)]
berkeley_years = berkeley_annual['year'].tolist()
berkeley_land_temp_k = berkeley_annual['absolute_temp_K'].tolist()

assert len(berkeley_years) == 21, (
    f"Expected 21 years (2000-2020), got {len(berkeley_years)} - "
    f"check the Berkeley Earth data file for missing years."
)

# ---- ENSO years (NOAA CPC ONI, computed from real data, not hardcoded) -----
# Classification rule: ONI >= +0.5C (El Nino) or <= -0.5C (La Nina),
# sustained for >=5 consecutive overlapping 3-month seasons (NOAA CPC
# standard). Each calendar year is labeled by its DJF (winter) season only,
# so a year is marked only if it officially qualifies. See
# 00_fetch_noaa_oni.py for the full classification logic and source data.
with open("../data/raw/noaa_oni.meta.json") as f:
    oni_meta = json.load(f)
el_nino_years = oni_meta["el_nino_years_2000_2020"]
la_nina_years = oni_meta["la_nina_years_2000_2020"]

# ---- Plotting ---------------------------------------------------------------
fig = plt.figure(figsize=(6.7, 4.4))
sns.set(style="whitegrid")

color_map = {
    'Impervious': '#D62728',
    'Vegetation': '#2CA02C',
    'Cropland': '#FF7F0E',
    'Water': '#1F77B4',
    'Bare': '#9467BD'
}
line_styles = {'mean_LST': '-', 'max_LST': '--'}

for lc_class in color_map.keys():
    subset = grouped[grouped['LC_class_name'] == lc_class]
    for metric in ['mean_LST', 'max_LST']:
        display_label = f"{lc_class} (mean)" if metric == 'mean_LST' else f"{lc_class} (max)"
        plt.plot(subset['year'], subset[metric],
                 linestyle=line_styles[metric], color=color_map[lc_class],
                 linewidth=1.4 if metric == 'mean_LST' else 1.0,
                 label=display_label, zorder=3)

# Global mean land temperature: dash-dot style so it's visually distinct
# from the solid Vegetation (mean) line (Reviewer 1, comment on Fig. 2).
plt.plot(berkeley_years, berkeley_land_temp_k, color='black', linewidth=2.0,
          linestyle=(0, (5, 1, 1, 1)), label='Global Mean Land Temp (K)',
          zorder=4, alpha=0.9)

for i, year in enumerate(el_nino_years):
    plt.axvline(x=year, color='#C0392B', linestyle=':', alpha=0.6, linewidth=1.1,
                label='El Nino' if i == 0 else "", zorder=1)
for i, year in enumerate(la_nina_years):
    plt.axvline(x=year, color='#27AE60', linestyle=':', alpha=0.6, linewidth=1.1,
                label='La Nina' if i == 0 else "", zorder=1)

plt.title("Temporal Dynamics of LST by LC Class with Global Mean Land Temperature (2000-2020)",
          fontsize=9.5, fontweight='bold', pad=8)
plt.xlabel("Year", fontsize=9, fontweight='bold')
plt.ylabel("Temperature (K)", fontsize=9, fontweight='bold')
plt.xticks(sorted(df['year'].unique()), fontsize=7)
plt.yticks(fontsize=7)

plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=4,
           fontsize=6.5, frameon=True)

plt.xlim(1999.5, 2020.5)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("../outputs/figures/figure_03_lst_temporal_trends.png",
            dpi=600, bbox_inches='tight')
plt.show()

# ---- Print delta summary for the manuscript text ---------------------------
print("\n" + "=" * 60)
print("DATA SOURCES (cite these in the manuscript / methods):")
print(f"  {berkeley_meta['source_citation']}")
print(f"  Product: {berkeley_meta['product']}")
print(f"  Accessed: {berkeley_meta['accessed']}")
print(f"  {oni_meta['source_citation']}")
print(f"  Classification: {oni_meta['classification_rule']}")
print(f"  Accessed: {oni_meta['accessed']}")
print("=" * 60)

global_2000 = berkeley_annual.loc[berkeley_annual.year == 2000, 'absolute_temp_C'].values[0]
global_2020 = berkeley_annual.loc[berkeley_annual.year == 2020, 'absolute_temp_C'].values[0]
global_delta = global_2020 - global_2000
print(f"\nGlobal LAND-ONLY mean temp: {global_2000:.2f} C (2000) -> {global_2020:.2f} C (2020)")
print(f"Global land-only delta: {global_delta:.2f} K")

print("\nUrban LC-class deltas (2000 -> 2020) and ratio vs corrected global delta:")
for lc_name in color_map.keys():
    sub = grouped[grouped['LC_class_name'] == lc_name]
    v2000 = sub.loc[sub.year == 2000, 'mean_LST'].values
    v2020 = sub.loc[sub.year == 2020, 'mean_LST'].values
    if len(v2000) and len(v2020):
        d = v2020[0] - v2000[0]
        print(f"  {lc_name:12s} mean_LST delta: {d:5.2f} K  ({d/global_delta:.2f}x global)")

print(f"\nEl Nino years (computed, not hardcoded): {el_nino_years}")
print(f"La Nina years (computed, not hardcoded): {la_nina_years}")
