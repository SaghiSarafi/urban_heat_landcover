#!/usr/bin/env python3
"""
Table 7: Relative Temperature Index (RTI) statistics by LC class across all city-years.
Outputs: table_07_rti_statistics.csv
Data required: city_year_lst_lc.csv
"""

import pandas as pd

df = pd.read_csv("../data/city_year_lst_lc.csv")

# Compute RTI: class mean LST divided by city-year mean LST
df_pivot = df.pivot_table(index=['city', 'year', 'LC_class'], values='mean_LST', aggfunc='mean')
city_year_means = df_pivot.groupby(['city', 'year']).mean().reset_index().rename(columns={'mean_LST': 'city_mean_LST'})
df_rti = df_pivot.reset_index().merge(city_year_means, on=['city', 'year'])
df_rti['RTI'] = df_rti['mean_LST'] / df_rti['city_mean_LST']

class_map = {1: 'Impervious', 2: 'Vegetation', 3: 'Cropland', 4: 'Water', 5: 'Bare'}
df_rti['LC_name'] = df_rti['LC_class'].map(class_map)

table7 = df_rti.groupby('LC_name')['RTI'].agg(
    mean='mean',
    std='std',
    min_10th=lambda x: x.quantile(0.10),
    max_90th=lambda x: x.quantile(0.90),
    mode=lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.median()
).round(4)
table7.columns = ['mean', 'std', 'min*', 'max*', 'mode']
table7 = table7.reindex(['Impervious', 'Vegetation', 'Cropland', 'Water', 'Bare'])

table7.to_csv("../outputs/tables/table_07_rti_statistics.csv")
print(table7)