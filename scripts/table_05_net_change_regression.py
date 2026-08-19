#!/usr/bin/env python3
"""
Table 5a: OLS regression of city-level delta LST metrics on net percentage change
in each LC class (2000-2020), reported as two models:
  (a) ORIGINAL: the 5 LC-class predictors only, all 100 study cities
      (Baku included) -- this is the primary model cited throughout the
      manuscript (Abstract, Results, Discussion, Conclusion: R^2 = 0.186).
  (b) AUGMENTED: the same 5 predictors plus two boundary-sensitivity
      covariates added in response to Reviewer 1's request to include
      "at minimum" boundary morphology metrics as regression covariates:
        - area_ratio: city's own administrative-boundary land area divided
          by the area of its GHSL Urban Centre (population/built-up-based)
          extent -- how much of the city's real full extent the boundary
          captures.
        - perimeter_area_ratio: boundary compactness (shape irregularity),
          the reviewer's literal suggestion.
      Baku City is excluded from THIS model only -- see
      03_boundary_covariates_ghsl_compactness.js for why (a boundary
      data-quality issue found during this sensitivity analysis). The
      manuscript's Limitations section reports the effect of this
      exclusion directly on the original model too (R^2 = 0.186 -> 0.196),
      confirming it changes no headline result -- but that comparison is a
      side note, not a reason to silently drop Baku from the primary,
      published Table 5a numbers.

Outputs: table_05a_net_change_regression.csv (original model, 100 cities),
         table_05b_net_change_regression_augmented.csv (augmented model, 99 cities)
Data required: city_year_lst_lc.csv, boundary_covariates_ghsl_compactness.csv
"""

import pandas as pd
import statsmodels.api as sm

df = pd.read_csv("../data/city_year_lst_lc.csv")

df_2000 = df[df['year'] == 2000]
df_2020 = df[df['year'] == 2020]

pivot_2000 = df_2000.pivot_table(index='city', columns='LC_class', values='LC_percent').add_prefix('2000_')
pivot_2020 = df_2020.pivot_table(index='city', columns='LC_class', values='LC_percent').add_prefix('2020_')
df_merge = pivot_2000.merge(pivot_2020, left_index=True, right_index=True)

for lc_class in df_2000['LC_class'].unique():
    df_merge[f'change_LC_{lc_class}'] = df_merge[f'2020_{lc_class}'] - df_merge[f'2000_{lc_class}']

# LST changes
mean_LST_2000 = df_2000.groupby('city')['mean_LST'].mean()
mean_LST_2020 = df_2020.groupby('city')['mean_LST'].mean()
df_merge['delta_LST'] = mean_LST_2020 - mean_LST_2000

mean_max_2000 = df_2000.groupby('city')['max_LST'].mean()
mean_max_2020 = df_2020.groupby('city')['max_LST'].mean()
df_merge['delta_max'] = mean_max_2020 - mean_max_2000

mean_top10_2000 = df_2000.groupby('city')['mean_top10_LST'].mean()
mean_top10_2020 = df_2020.groupby('city')['mean_top10_LST'].mean()
df_merge['delta_top10'] = mean_top10_2020 - mean_top10_2000

predictors_original = [f'change_LC_{lc}' for lc in df_2000['LC_class'].unique()]
lc_names = {1: 'Impervious', 2: 'Vegetation', 3: 'Cropland', 4: 'Water', 5: 'Bare'}

# ---- ORIGINAL model: ALL 100 cities, Baku included --------------------------
# This is the primary model cited throughout the manuscript (R^2 = 0.186).
# Do NOT exclude Baku here -- that exclusion applies only to the augmented
# model below, which specifically requires the boundary covariates dataset.
all_results_original = []
for response_name, response_col in [('ΔLST', 'delta_LST'), ('ΔLST_Max', 'delta_max'), ('ΔLST_Max10', 'delta_top10')]:
    df_reg = df_merge[predictors_original + [response_col]].dropna()
    X = sm.add_constant(df_reg[predictors_original])
    y = df_reg[response_col]
    model = sm.OLS(y, X).fit()
    for pred in predictors_original:
        lc_num = int(pred.split('_')[-1])
        all_results_original.append({
            'Response': response_name,
            'LC_Class': lc_names[lc_num],
            'β_(K_per_%)': model.params[pred],
            'Std_Err': model.bse[pred],
            't_value': model.tvalues[pred],
            'p_value': model.pvalues[pred],
            'n': len(df_reg),
            'model_R2': round(model.rsquared, 4),
        })

results_original_df = pd.DataFrame(all_results_original)
results_original_df.to_csv('../outputs/tables/table_05a_net_change_regression.csv', index=False)
print("=== ORIGINAL MODEL (5 predictors, all 100 cities, Baku included) ===")
print(results_original_df.to_string())

# ---- AUGMENTED model: add boundary covariates, Baku excluded here only -----
df_aug_base = df[df['city'] != 'Baku City']
df_2000_aug = df_aug_base[df_aug_base['year'] == 2000]
df_2020_aug = df_aug_base[df_aug_base['year'] == 2020]
pivot_2000_aug = df_2000_aug.pivot_table(index='city', columns='LC_class', values='LC_percent').add_prefix('2000_')
pivot_2020_aug = df_2020_aug.pivot_table(index='city', columns='LC_class', values='LC_percent').add_prefix('2020_')
df_merge_aug = pivot_2000_aug.merge(pivot_2020_aug, left_index=True, right_index=True)
for lc_class in df_2000_aug['LC_class'].unique():
    df_merge_aug[f'change_LC_{lc_class}'] = df_merge_aug[f'2020_{lc_class}'] - df_merge_aug[f'2000_{lc_class}']
df_merge_aug['delta_LST'] = df_2020_aug.groupby('city')['mean_LST'].mean() - df_2000_aug.groupby('city')['mean_LST'].mean()
df_merge_aug['delta_max'] = df_2020_aug.groupby('city')['max_LST'].mean() - df_2000_aug.groupby('city')['max_LST'].mean()
df_merge_aug['delta_top10'] = df_2020_aug.groupby('city')['mean_top10_LST'].mean() - df_2000_aug.groupby('city')['mean_top10_LST'].mean()

cov = pd.read_csv("../data/boundary_covariates_ghsl_compactness.csv")
cov['ghsl_reliable'] = (cov['ghsl_urban_centre_area_km2'] > 4) & (cov['ghsl_urban_centre_area_km2'] != -1)

compactness_by_city = cov.groupby('city')['perimeter_area_ratio'].first()
area_ratio_by_city = cov[cov['ghsl_reliable']].groupby('city')['area_ratio'].mean()

df_merge_aug = df_merge_aug.merge(area_ratio_by_city.rename('area_ratio'),
                                left_index=True, right_index=True, how='left')
df_merge_aug = df_merge_aug.merge(compactness_by_city.rename('perimeter_area_ratio'),
                                    left_index=True, right_index=True, how='left')

predictors_augmented = predictors_original + ['area_ratio', 'perimeter_area_ratio']

all_results_augmented = []
for response_name, response_col in [('ΔLST', 'delta_LST'), ('ΔLST_Max', 'delta_max'), ('ΔLST_Max10', 'delta_top10')]:
    df_reg = df_merge_aug[predictors_augmented + [response_col]].dropna()
    X = sm.add_constant(df_reg[predictors_augmented])
    y = df_reg[response_col]
    model = sm.OLS(y, X).fit()
    for pred in predictors_augmented:
        if pred in ('area_ratio', 'perimeter_area_ratio'):
            label = pred
        else:
            lc_num = int(pred.split('_')[-1])
            label = lc_names[lc_num]
        all_results_augmented.append({
            'Response': response_name,
            'Predictor': label,
            'β_(K_per_%)': model.params[pred],
            'Std_Err': model.bse[pred],
            't_value': model.tvalues[pred],
            'p_value': model.pvalues[pred],
            'n': len(df_reg),
            'model_R2': round(model.rsquared, 4),
            'model_adj_R2': round(model.rsquared_adj, 4),
        })

results_augmented_df = pd.DataFrame(all_results_augmented)
results_augmented_df.to_csv('../outputs/tables/table_05b_net_change_regression_augmented.csv', index=False)
print("\n=== AUGMENTED MODEL (5 + area_ratio + compactness, Baku excluded) ===")
print(results_augmented_df.to_string())