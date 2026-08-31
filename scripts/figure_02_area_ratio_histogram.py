#!/usr/bin/env python3
"""
Figure 2: Histogram of the area-ratio boundary covariate (city administrative
boundary land area divided by its GHS-SMOD Urban Centre extent) across the
study sample. Included in the Data section to directly show readers how much
administrative boundaries vary in how well they represent each city's real
urban extent -- the underlying concern raised by Reviewer 1's boundary-
sensitivity comment, and the basis for the covariate used in Table 5.

A value near 1.0 means the administrative boundary closely matches the
GHS-SMOD-defined urban extent. Values below 1.0 mean the boundary is smaller
than the true urban extent (the boundary undersamples the real city); values
above 1.0 mean the boundary is larger (the boundary oversamples, including
substantial non-urban land).

Outputs: figure_02_area_ratio_histogram.png
Data required: boundary_covariates_ghsl_compactness.csv
"""

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']

cov = pd.read_csv("../data/boundary_covariates_ghsl_compactness.csv")

# Same reliability rule and per-city aggregation used in the Table 5
# regression: average area_ratio across each city's reliable years only.
cov['ghsl_reliable'] = (cov['ghsl_urban_centre_area_km2'] > 4) & (cov['ghsl_urban_centre_area_km2'] != -1)
area_ratio_by_city = cov[cov['ghsl_reliable']].groupby('city')['area_ratio'].mean()

# Matches the 170mm print-width convention used in Figures 2, 3, 6, 7.
fig, ax = plt.subplots(figsize=(6.7, 4.2))

# LOG-SCALE x-axis: area_ratio is a genuinely long-tailed distribution (22 of
# 95 cities exceed ratio=3, up to Ulaanbaatar at ~31 -- a real, verified
# administrative area, not an outlier to exclude). A linear-scale histogram
# crams nearly all cities into one or two bins and makes the long tail
# unreadable. Log scale is also more honest for ratio data generally: a
# boundary at half the true size (ratio=0.5) and one at double the true size
# (ratio=2.0) are equally "wrong" in a multiplicative sense, and a log axis
# places them symmetrically around 1.0, whereas a linear axis would visually
# exaggerate the oversized-boundary cases relative to the undersized ones.
log_ratios = np.log10(area_ratio_by_city)
bins = np.linspace(log_ratios.min(), log_ratios.max(), 21)

ax.hist(log_ratios, bins=bins, color='#1F77B4', edgecolor='white', alpha=0.85)
ax.axvline(0, color='black', linestyle='--', linewidth=1.2, alpha=0.7,
           label='Boundary exactly matches\nGHS-SMOD Urban Centre extent')

# Tick labels shown as actual ratio values, not log10 values, so the axis
# stays interpretable at a glance.
tick_locs = [-1, -0.5, 0, 0.5, 1, 1.5]
tick_locs = [t for t in tick_locs if log_ratios.min() - 0.2 <= t <= log_ratios.max() + 0.2]
ax.set_xticks(tick_locs)
ax.set_xticklabels([f'{10**t:.2g}' for t in tick_locs])

ax.set_xlabel('Area ratio (boundary / GHS-SMOD Urban Centre area), log scale',
              fontsize=9, fontweight='bold')
ax.set_ylabel('Number of cities (frequency)', fontsize=9, fontweight='bold')
ax.tick_params(axis='both', labelsize=8)
ax.legend(fontsize=7.5, loc='upper right')
ax.grid(True, alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig("../outputs/figures/figure_02_area_ratio_histogram.png",
            dpi=600, bbox_inches='tight')
plt.show()

print(f"n cities with usable area_ratio: {len(area_ratio_by_city)}")
print(f"Mean: {area_ratio_by_city.mean():.4f}")
print(f"Median: {area_ratio_by_city.median():.4f}")
print(f"Min: {area_ratio_by_city.min():.4f}")
print(f"Max: {area_ratio_by_city.max():.4f}")
print(f"Cities with ratio < 0.5 (boundary much smaller than real urban extent): "
      f"{(area_ratio_by_city < 0.5).sum()}")
print(f"Cities with ratio > 2.0 (boundary much larger than real urban extent): "
      f"{(area_ratio_by_city > 2.0).sum()}")
