#!/usr/bin/env python3
"""
Table 5: Single merged OLS regression of city-level delta LST metrics on
net percentage change in each LC class (2000-2020), PLUS two
boundary-sensitivity covariates, all entered into ONE model together:
  - area_ratio: city's own administrative-boundary land area divided by
    the area of its GHSL Urban Centre (population/built-up-based) extent
    -- how much of the city's real full extent the boundary captures.
  - perimeter_area_ratio: boundary shape irregularity (perimeter divided
    by the square root of area, so it is scale-independent -- see script
    comments in 03_boundary_covariates_ghsl_compactness.js for why raw
    perimeter/area is not used).
    

Outputs: table_05_net_change_regression.csv
Data required: city_year_lst_lc.csv, boundary_covariates_ghsl_compactness.csv

Note: Baku City is excluded (a boundary data-quality issue found during
this sensitivity analysis -- see 03_boundary_covariates_ghsl_compactness.js).
A handful of additional cities are excluded because they lack a usable
area_ratio value (GHSL Urban Centre detection failed for these -- see
same script for which cities and why); this is now a SINGLE model, so
all 7 predictors must have valid data for the same set of cities.
"""

import pandas as pd
import statsmodels.api as sm

df = pd.read_csv("../data/city_year_lst_lc.csv")
df = df[df['city'] != 'Baku City']

df_2000 = df[df['year'] == 2000]
df_2020 = df[df['year'] == 2020]

pivot_2000 = df_2000.pivot_table(index='city', columns='LC_class', values='LC_percent').add_prefix('2000_')
pivot_2020 = df_2020.pivot_table(index='city', columns='LC_class', values='LC_percent').add_prefix('2020_')
df_merge = pivot_2000.merge(pivot_2020, left_index=True, right_index=True)

for lc_class in df_2000['LC_class'].unique():
    df_merge[f'change_LC_{lc_class}'] = df_merge[f'2020_{lc_class}'] - df_merge[f'2000_{lc_class}']

df_merge['delta_LST'] = df_2020.groupby('city')['mean_LST'].mean() - df_2000.groupby('city')['mean_LST'].mean()
df_merge['delta_max'] = df_2020.groupby('city')['max_LST'].mean() - df_2000.groupby('city')['max_LST'].mean()
df_merge['delta_top10'] = df_2020.groupby('city')['mean_top10_LST'].mean() - df_2000.groupby('city')['mean_top10_LST'].mean()

# ---- Boundary covariates ----------------------------------------------------
cov = pd.read_csv("../data/boundary_covariates_ghsl_compactness.csv")
cov['ghsl_reliable'] = (cov['ghsl_urban_centre_area_km2'] > 4) & (cov['ghsl_urban_centre_area_km2'] != -1)

compactness_by_city = cov.groupby('city')['perimeter_area_ratio'].first()
area_ratio_by_city = cov[cov['ghsl_reliable']].groupby('city')['area_ratio'].mean()

df_merge = df_merge.merge(area_ratio_by_city.rename('area_ratio'), left_index=True, right_index=True, how='left')
df_merge = df_merge.merge(compactness_by_city.rename('perimeter_area_ratio'), left_index=True, right_index=True, how='left')

predictors = [f'change_LC_{lc}' for lc in df_2000['LC_class'].unique()] + ['area_ratio', 'perimeter_area_ratio']
lc_names = {1: 'Impervious', 2: 'Vegetation', 3: 'Cropland', 4: 'Water', 5: 'Bare'}

all_results = []
for response_name, response_col in [('\u0394LST', 'delta_LST'), ('\u0394LST_Max', 'delta_max'), ('\u0394LST_Max10', 'delta_top10')]:
    df_reg = df_merge[predictors + [response_col]].dropna()
    X = sm.add_constant(df_reg[predictors])
    y = df_reg[response_col]
    model = sm.OLS(y, X).fit()
    for pred in predictors:
        label = pred if pred in ('area_ratio', 'perimeter_area_ratio') else lc_names[int(pred.split('_')[-1])]
        all_results.append({
            'Response': response_name,
            'Predictor': label,
            '\u03b2_(K_per_%)': model.params[pred],
            'Std_Err': model.bse[pred],
            't_value': model.tvalues[pred],
            'p_value': model.pvalues[pred],
            'n': len(df_reg),
            'model_R2': round(model.rsquared, 4),
            'model_adj_R2': round(model.rsquared_adj, 4),
        })

results_df = pd.DataFrame(all_results)
results_df.to_csv('../outputs/tables/table_05_net_change_regression.csv', index=False)
print("=== SINGLE MERGED MODEL (5 LC predictors + area_ratio + perimeter_area_ratio) ===")
print(results_df.to_string())
