#!/usr/bin/env python3
"""
Figure 4: Scatter plots of LC% vs LST metrics (mean, max, top-10%) for each LC class in 2020.
Includes correlation coefficients and regression lines where p < 0.05.
Outputs: figure_04_lc_vs_lst_scatter_2020.png
Data required: city_year_lst_lc.csv

"""

import matplotlib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']

df = pd.read_csv("../data/city_year_lst_lc.csv")
df_2020 = df[df['year'] == 2020].copy()

lc_class_map = {1: 'Impervious', 2: 'Vegetation', 3: 'Cropland', 4: 'Water', 5: 'Bare'}

data_by_class = {}
for lc_code, lc_name in lc_class_map.items():
    subset = df_2020[df_2020['LC_class'] == lc_code]
    if not subset.empty:
        city_means = subset.groupby('city').agg({
            'mean_LST': 'mean',
            'max_LST': 'mean',
            'mean_top10_LST': 'mean',
            'LC_percent': 'mean'
        }).reset_index()
        data_by_class[lc_name] = city_means

# Calculate correlations
correlations = {}
for lc_name, data in data_by_class.items():
    n = len(data)
    r_mean, p_mean = stats.pearsonr(data['LC_percent'], data['mean_LST'])
    r_max, p_max = stats.pearsonr(data['LC_percent'], data['max_LST'])
    r_top10, p_top10 = stats.pearsonr(data['LC_percent'], data['mean_top10_LST'])
    correlations[lc_name] = {'mean': (r_mean, p_mean, n),
                             'max': (r_max, p_max, n),
                             'top10': (r_top10, p_top10, n)}

# Plot -- figure is generated at final print width (~170 mm / 6.7 in)
fig = plt.figure(figsize=(6.7, 4.6))
gs = gridspec.GridSpec(2, 3, figure=fig, wspace=0.4, hspace=0.45)

mean_color = '#2E86AB'
max_color = '#8B0000'
top10_color = '#ffb703'
fit_mean_color = '#1a5276'
fit_max_color = '#6c1e4a'
fit_top10_color = '#b35900'
alpha_sig = 0.05

positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)]
lc_names = ['Impervious', 'Vegetation', 'Cropland', 'Water', 'Bare']

for idx, (row, col) in enumerate(positions):
    lc_name = lc_names[idx]
    ax = fig.add_subplot(gs[row, col])
    data = data_by_class[lc_name]
    x = data['LC_percent'].values
    y_mean = data['mean_LST'].values
    y_max = data['max_LST'].values
    y_top10 = data['mean_top10_LST'].values

    ax.scatter(x, y_mean, c=mean_color, marker='o', s=14, alpha=0.7,
               edgecolors='white', linewidth=0.3, zorder=3, label='Mean LST')
    ax.scatter(x, y_max, c=max_color, marker='s', s=16, alpha=0.7,
               edgecolors='white', linewidth=0.3, zorder=3, label='Max LST')
    ax.scatter(x, y_top10, c=top10_color, marker='^', s=14, alpha=0.7,
               edgecolors='white', linewidth=0.3, zorder=3, label='Mean Top-10% LST')

    # Regression lines if significant
    r_mean, p_mean, _ = correlations[lc_name]['mean']
    if p_mean < alpha_sig:
        z = np.polyfit(x, y_mean, 1)
        p_fit = np.poly1d(z)
        ax.plot(np.sort(x), p_fit(np.sort(x)), color=fit_mean_color, linewidth=1.2, linestyle='-')

    r_max, p_max, _ = correlations[lc_name]['max']
    if p_max < alpha_sig:
        z = np.polyfit(x, y_max, 1)
        p_fit = np.poly1d(z)
        ax.plot(np.sort(x), p_fit(np.sort(x)), color=fit_max_color, linewidth=1.2, linestyle='-')

    r_top10, p_top10, _ = correlations[lc_name]['top10']
    if p_top10 < alpha_sig:
        z = np.polyfit(x, y_top10, 1)
        p_fit = np.poly1d(z)
        ax.plot(np.sort(x), p_fit(np.sort(x)), color=fit_top10_color, linewidth=1.2, linestyle='-')

    ax.set_title(lc_name, fontsize=8.5, fontweight='bold', pad=5)

    # Add stats text box
    r_mean, p_mean, n = correlations[lc_name]['mean']
    stats_text = f'r = {r_mean:.3f}\np = {p_mean:.3f}\nn = {n}'
    ax.text(0.97, 0.03, stats_text, transform=ax.transAxes, fontsize=6,
            va='bottom', ha='right', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    ax.grid(True, alpha=0.3, linestyle='--')
    ax.tick_params(axis='both', labelsize=6.5)

fig.text(0.5, 0.02, 'Percent Land Cover (%)', ha='center', fontsize=9, fontweight='bold')
fig.text(0.005, 0.5, 'LST (K)', va='center', rotation='vertical', fontsize=9, fontweight='bold')

# Legend
ax_legend = fig.add_subplot(gs[1, 2])
ax_legend.axis('off')
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor=mean_color, markersize=6, label='Mean LST'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor=max_color, markersize=6, label='Max LST'),
    Line2D([0], [0], marker='^', color='w', markerfacecolor=top10_color, markersize=7, label='Mean Top-10% LST'),
    Line2D([0], [0], color=fit_mean_color, linewidth=1.2, label='Mean LST fit (p<0.05)'),
    Line2D([0], [0], color=fit_max_color, linewidth=1.2, label='Max LST fit (p<0.05)'),
    Line2D([0], [0], color=fit_top10_color, linewidth=1.2, label='Top-10% LST fit (p<0.05)'),
]
ax_legend.legend(handles=legend_elements, loc='center', fontsize=6.5, frameon=True)

plt.tight_layout(rect=[0.02, 0.04, 1, 0.98])
plt.savefig("../outputs/figures/figure_04_lc_vs_lst_scatter_2020.png",
            dpi=600, bbox_inches='tight')
plt.show()