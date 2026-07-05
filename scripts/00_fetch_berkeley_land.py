#!/usr/bin/env python3
"""
Step 1 of the pipeline: download Berkeley Earth's official LAND-ONLY
average temperature series and save it as a local, versioned CSV.

Source: Rohde, R. and Hausfather, Z. (Berkeley Earth).
        "Estimated Global Land-Surface TAVG based on the Complete
        Berkeley Dataset."
        https://berkeleyearth.org/data/
File:   Complete_TAVG_complete.txt
Citation (paper): Rohde, R. A. and Hausfather, Z.: The Berkeley Earth
        Land/Ocean Temperature Record, Earth Syst. Sci. Data, 12,
        3469-3479, https://doi.org/10.5194/essd-12-3469-2020, 2020.

IMPORTANT: this is the LAND-ONLY product. Do not confuse with
"Land_and_Ocean_complete.txt", which is the combined land+ocean series
and has a ~14 C baseline instead of the ~8.6 C land-only baseline.
This is the exact mixup that caused the original figure to be mislabeled.
"""
import urllib.request
import pandas as pd
from datetime import datetime
from io import StringIO
import json

URL = "https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com/Global/Complete_TAVG_complete.txt"
OUT_RAW = "../data/raw/berkeley_earth_land_tavg_raw.txt"
OUT_CSV = "../data/raw/berkeley_earth_land_tavg.csv"
OUT_META = "../data/raw/berkeley_earth_land_tavg.meta.json"


def fetch():
    with urllib.request.urlopen(URL) as resp:
        text = resp.read().decode("utf-8", errors="ignore")
    with open(OUT_RAW, "w") as f:
        f.write(text)
    return text


def parse(text):
    header_lines = [l for l in text.splitlines() if l.startswith('%')]
    baseline_line = [l for l in header_lines if "absolute temperature (C)" in l][0]
    baseline_c = float(baseline_line.split(":")[1].split("+/-")[0].strip())

    data_lines = [l for l in text.splitlines() if l.strip() and not l.startswith('%')]
    df = pd.read_csv(
        StringIO("\n".join(data_lines)),
        delim_whitespace=True, header=None,
        names=["year", "month", "monthly_anomaly", "monthly_unc",
               "annual_anomaly", "annual_unc",
               "five_yr_anomaly", "five_yr_unc",
               "ten_yr_anomaly", "ten_yr_unc",
               "twenty_yr_anomaly", "twenty_yr_unc"]
    )
    df["absolute_temp_C"] = baseline_c + df["annual_anomaly"]
    df["absolute_temp_K"] = df["absolute_temp_C"] + 273.15
    return df, baseline_c


if __name__ == "__main__":
    text = fetch()
    df, baseline_c = parse(text)

    # Sanity check: land-only absolute temp must be well below land+ocean (~14C).
    # This single assertion would have caught the original mislabeling bug.
    assert 5 < baseline_c < 12, (
        f"Baseline {baseline_c} C is outside the plausible land-only range "
        f"(5-12 C) - you may have downloaded the wrong product (e.g. "
        f"Land+Ocean instead of Land-only)."
    )

    df.to_csv(OUT_CSV, index=False)

    meta = {
        "source_url": URL,
        "source_citation": "Rohde, R. A. and Hausfather, Z. (2020). "
                            "The Berkeley Earth Land/Ocean Temperature Record. "
                            "Earth Syst. Sci. Data, 12, 3469-3479. "
                            "https://doi.org/10.5194/essd-12-3469-2020",
        "product": "Land-only TAVG (Complete_TAVG_complete.txt)",
        "baseline_period": "1951-1980",
        "baseline_absolute_C": baseline_c,
        "accessed": datetime.utcnow().isoformat() + "Z",
        "units": "Celsius / Kelvin, annual values centered on June of each year"
    }
    with open(OUT_META, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Baseline (1951-1980) land-only absolute temp: {baseline_c} C  [sanity check passed]")
    for yr in [2000, 2020]:
        row = df[(df.year == yr) & (df.month == 6)]
        if not row.empty:
            print(f"{yr}: {row['absolute_temp_C'].values[0]:.3f} C "
                  f"({row['absolute_temp_K'].values[0]:.3f} K)")
    print(f"\nSaved: {OUT_CSV}")
    print(f"Saved: {OUT_META}")
