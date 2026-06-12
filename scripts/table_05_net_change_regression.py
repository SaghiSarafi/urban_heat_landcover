#!/usr/bin/env python3
"""
Table 5: OLS regression of city-level ΔLST metrics on net percentage change in each LC class (2000–2020).
Outputs: table_05_net_change_regression.csv
Data required: city_year_lst_lc.csv
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

predictors = [f'change_LC_{lc}' for lc in df_2000['LC_class'].unique()]
lc_names = {1: 'Impervious', 2: 'Vegetation', 3: 'Cropland', 4: 'Water', 5: 'Bare'}

all_results = []
for response_name, response_col in [('ΔLST', 'delta_LST'), ('ΔLST_Max', 'delta_max'), ('ΔLST_Max10', 'delta_top10')]:
    df_reg = df_merge[predictors + [response_col]].dropna()
    X = sm.add_constant(df_reg[predictors])
    y = df_reg[response_col]
    model = sm.OLS(y, X).fit()
    for pred in predictors:
        lc_num = int(pred.split('_')[-1])
        all_results.append({
            'Response': response_name,
            'LC_Class': lc_names[lc_num],
            'β_(K_per_%)': model.params[pred],
            'Std_Err': model.bse[pred],
            't_value': model.tvalues[pred],
            'p_value': model.pvalues[pred]
        })

results_df = pd.DataFrame(all_results)
results_df.to_csv('../outputs/tables/table_05_net_change_regression.csv', index=False)
print(results_df)