#!/usr/bin/env python3
"""
Fetches NOAA CPC's official Oceanic Nino Index (ONI) table and saves it
as a local, versioned CSV -- the same pattern used in
00_fetch_berkeley_land.py for the global temperature series.

Source: NOAA Climate Prediction Center (CPC)
        Oceanic Nino Index (ONI), 3-month running mean SST anomaly in the
        Nino 3.4 region (5N-5S, 120W-170W), relative to a rolling 30-year
        base period.
File:   oni.ascii.txt

Run this before figure_03_lst_temporal_trends.py.

CLASSIFICATION RULE (NOAA CPC standard):
  - A season is "warm" if ONI >= +0.5 C, "cool" if ONI <= -0.5 C.
  - An El Nino / La Nina EPISODE is only official if the threshold is met
    for at least 5 consecutive overlapping 3-month seasons.
  - This script applies that exact rule to the full historical record,
    then labels each CALENDAR YEAR by its DJF (Dec-Jan-Feb, winter) season:
    a year is marked El Nino / La Nina only if that year's DJF season falls
    within a run of 5+ consecutive qualifying seasons. DJF is used because
    it is the conventional peak/defining season for a given ENSO year in
    the climate literature, and it gives exactly one classification per
    calendar year (no double-counting when a year's earlier and later
    seasons belong to different episodes).
"""
import urllib.request
import pandas as pd
from datetime import datetime
import json

URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
OUT_RAW = "../data/raw/noaa_oni_raw.txt"
OUT_CSV = "../data/raw/noaa_oni.csv"
OUT_META = "../data/raw/noaa_oni.meta.json"


def fetch():
    with urllib.request.urlopen(URL) as resp:
        text = resp.read().decode("utf-8", errors="ignore")
    with open(OUT_RAW, "w") as f:
        f.write(text)
    return text


def parse(text):
    rows = []
    for line in text.strip().splitlines()[1:]:  # skip header row
        parts = line.split()
        if len(parts) != 3:
            continue
        season, year, anom = parts
        rows.append({"season": season, "year": int(year), "oni": float(anom)})
    return pd.DataFrame(rows)


def classify(df):
    """Apply the NOAA 5-consecutive-overlapping-season persistence rule."""
    n = len(df)
    warm_flag = [False] * n
    cool_flag = [False] * n
    oni = df["oni"].values
    for i in range(n - 4):
        window = oni[i:i + 5]
        if all(v >= 0.5 for v in window):
            for j in range(i, i + 5):
                warm_flag[j] = True
        if all(v <= -0.5 for v in window):
            for j in range(i, i + 5):
                cool_flag[j] = True
    df = df.copy()
    df["warm_episode"] = warm_flag
    df["cool_episode"] = cool_flag
    return df


def get_enso_years(df, start_year=2000, end_year=2020):
    """Return (el_nino_years, la_nina_years) using each year's DJF season."""
    djf = df[(df.season == "DJF") & (df.year >= start_year) & (df.year <= end_year)]
    el_nino_years = sorted(djf.loc[djf.warm_episode, "year"].tolist())
    la_nina_years = sorted(djf.loc[djf.cool_episode, "year"].tolist())
    return el_nino_years, la_nina_years


if __name__ == "__main__":
    text = fetch()
    df = parse(text)

    assert len(df) > 500, (
        f"Expected 500+ seasonal rows in the ONI record, got {len(df)} - "
        f"check that the NOAA CPC file format hasn't changed."
    )

    df = classify(df)
    df.to_csv(OUT_CSV, index=False)

    el_nino_years, la_nina_years = get_enso_years(df)

    meta = {
        "source_url": URL,
        "source_citation": "NOAA Climate Prediction Center. Oceanic Ni\u00f1o Index (ONI). "
                            "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
        "classification_rule": "ONI >= +0.5C (El Nino) or <= -0.5C (La Nina), "
                                "sustained for >=5 consecutive overlapping 3-month seasons",
        "year_assignment": "Calendar year classified by its DJF (winter) season only",
        "accessed": datetime.utcnow().isoformat() + "Z",
        "el_nino_years_2000_2020": el_nino_years,
        "la_nina_years_2000_2020": la_nina_years,
    }
    with open(OUT_META, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"El Nino years (2000-2020, DJF-based, officially qualifying): {el_nino_years}")
    print(f"La Nina years (2000-2020, DJF-based, officially qualifying): {la_nina_years}")
    print(f"\nSaved: {OUT_CSV}")
    print(f"Saved: {OUT_META}")
