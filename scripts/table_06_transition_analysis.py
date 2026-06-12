#!/usr/bin/env python3
"""
Table 6: Pixel-level direct thermal responses.
- Table 6: Direct thermal responses (mean ΔLST, ΔmaxLST, Δtop10LST) per transition type.

Data required: pixel_transitions_thermal_2000_2020.csv
Outputs: tables/table_06_direct_*.csv, tables/table_06_direct_thermal_all_metrics.csv
"""

import pandas as pd
from pathlib import Path

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
DATA_PATH = Path("../data/pixel_transitions_thermal_2000_2020.csv")
OUT_TABLES = Path("../outputs/tables")
OUT_TABLES.mkdir(exist_ok=True, parents=True)

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
METRICS = [
    ("delta_LST",       "Mean LST",     "mean"),
    ("delta_max_LST",   "Max LST",      "max"),
    ("delta_top10_LST", "Top-10% LST",  "top10"),
]

# -------------------------------------------------------------------
# Load and clean data
# -------------------------------------------------------------------
df = pd.read_csv(DATA_PATH)
df = df[df["transition"] != "NO_DATA"].copy()

numeric_cols = [
    "transition_area_pct", "n_pixels",
    "delta_LST", "mean_LST_2000", "mean_LST_2020",
    "delta_max_LST", "max_LST_2000", "max_LST_2020",
    "delta_top10_LST", "top10_LST_2000", "top10_LST_2020",
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=["delta_LST"]).copy()

def is_off_diagonal(transition):
    parts = transition.split("→")
    return len(parts) == 2 and parts[0] != parts[1]

df_off = df[df["transition"].apply(is_off_diagonal)].copy()

# -------------------------------------------------------------------
# Table 6: Direct thermal responses (mean ΔLST, Δmax, Δtop10 per transition)
# -------------------------------------------------------------------
direct_tables = {}
for delta_col, metric_label, metric_tag in METRICS:
    if delta_col not in df.columns:
        continue
    agg = (df_off.dropna(subset=[delta_col])
           .groupby("transition")
           .agg(n_cities=("city", "count"),
                mean_dLST=(delta_col, "mean"),
                median_dLST=(delta_col, "median"),
                std_dLST=(delta_col, "std"),
                mean_area=("transition_area_pct", "mean"),
                std_area=("transition_area_pct", "std"))
           .round(4)
           .sort_values("mean_dLST", ascending=False))
    agg.to_csv(OUT_TABLES / f"table_06_direct_{metric_tag}.csv")
    direct_tables[metric_tag] = agg

# Merge all three metrics into one table (as in paper's Table 6)
dtr_frames = []
for metric_tag, tbl in direct_tables.items():
    renamed = tbl[["n_cities", "mean_dLST", "std_dLST", "mean_area"]].copy()
    renamed.columns = [f"{metric_tag}_{c}" for c in renamed.columns]
    dtr_frames.append(renamed)
merged_dtr = pd.concat(dtr_frames, axis=1)
merged_dtr["n_cities"] = direct_tables["mean"]["n_cities"]
merged_dtr["mean_area_pct"] = direct_tables["mean"]["mean_area"]
if "mean" in direct_tables and "max" in direct_tables:
    merged_dtr["ratio_max_vs_mean"] = (direct_tables["max"]["mean_dLST"] / direct_tables["mean"]["mean_dLST"]).round(2)
if "mean" in direct_tables and "top10" in direct_tables:
    merged_dtr["ratio_top10_vs_mean"] = (direct_tables["top10"]["mean_dLST"] / direct_tables["mean"]["mean_dLST"]).round(2)
merged_dtr.sort_values("mean_mean_dLST", ascending=False, inplace=True)
merged_dtr.to_csv(OUT_TABLES / "table_06_direct_thermal_all_metrics.csv")

print("Table 6 saved to outputs/tables/")