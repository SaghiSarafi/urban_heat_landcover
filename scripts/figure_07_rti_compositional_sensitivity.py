#!/usr/bin/env python3
"""
Figure 7: Sensitivity of Relative Temperature Index (RTI) to land-cover
composition. Tests whether RTI for a class is systematically related to
how much of that class is present in a city (a class dominating its own
normalizing city-year mean could in principle compress RTI toward 1.0).

Panel (a): RTI for impervious surfaces vs. percent impervious cover.
Panel (b): RTI for water vs. percent water cover.

Outputs: figure_07_rti_compositional_sensitivity.png
Data required: city_year_lst_lc.csv

PRINT SIZING NOTE: figsize is chosen to match the ~170 mm final print
width required by the journal directly (see figure_02 script for the
full rationale).
"""

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy import stats

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']

df = pd.read_csv("../data/city_year_lst_lc.csv")

# Compute RTI exactly as in table_07_rti_statistics.py
df_pivot = df.pivot_table(index=['city', 'year', 'LC_class'], values='mean_LST', aggfunc='mean')
city_year_means = df_pivot.groupby(['city', 'year']).mean().reset_index().rename(
    columns={'mean_LST': 'city_mean_LST'})
df_rti = df_pivot.reset_index().merge(city_year_means, on=['city', 'year'])
df_rti['RTI'] = df_rti['mean_LST'] / df_rti['city_mean_LST']

colors = {'Impervious': '#E69F00', 'Water': '#56B4E9'}

fig, axes = plt.subplots(1, 2, figsize=(6.7, 3.2))

def sensitivity_panel(ax, lc_code, lc_name, color, xlabel, ylabel):
    pct = df[df['LC_class'] == lc_code][['city', 'year', 'LC_percent']].rename(
        columns={'LC_percent': 'pct'})
    rti_class = df_rti[df_rti['LC_class'] == lc_code][['city', 'year', 'RTI']]
    sens = rti_class.merge(pct, on=['city', 'year']).dropna()

    r, p = stats.pearsonr(sens['pct'], sens['RTI'])
    z = np.polyfit(sens['pct'], sens['RTI'], 1)
    xs = np.linspace(sens['pct'].min(), sens['pct'].max(), 100)

    ax.scatter(sens['pct'], sens['RTI'], s=8, alpha=0.35, color=color, edgecolors='none')
    ax.plot(xs, np.poly1d(z)(xs), color='#8B0000', linewidth=1.5)
    ax.axhline(1.0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)
    ax.set_xlabel(xlabel, fontsize=8, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=8, fontweight='bold')
    p_str = "p < 0.0001" if p < 0.0001 else f"p = {p:.4f}"
    ax.set_title(f'r = {r:.3f}, {p_str}, n = {len(sens)}', fontsize=7.5)
    ax.tick_params(labelsize=7)
    ax.grid(True, alpha=0.3, linestyle='--')
    return r, p, len(sens)

r_imp, p_imp, n_imp = sensitivity_panel(
    axes[0], 1, 'Impervious', colors['Impervious'],
    '% Impervious cover', 'RTI (Impervious)')
r_wat, p_wat, n_wat = sensitivity_panel(
    axes[1], 4, 'Water', colors['Water'],
    '% Water cover', 'RTI (Water)')

plt.tight_layout()
plt.savefig("../outputs/figures/figure_07_rti_compositional_sensitivity.png",
            dpi=600, bbox_inches='tight')
plt.show()

print("Figure 7 saved to ../outputs/figures/figure_07_rti_compositional_sensitivity.png")
print(f"\nImpervious RTI vs %impervious: r={r_imp:.4f}, p={p_imp:.2e}, n={n_imp}")
print(f"Water RTI vs %water: r={r_wat:.4f}, p={p_wat:.2e}, n={n_wat}")
print("\nBoth relationships run counter to a simple compositional-dilution expectation:")
print("more of a class within a city is associated with a STRONGER deviation from")
print("the city mean, not a weaker one.")
