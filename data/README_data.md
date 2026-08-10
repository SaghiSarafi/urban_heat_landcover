# Data Description

This folder contains the two main datasets used in the analysis, both derived from Landsat LST and GLAD land cover via Google Earth Engine.

## Files

### `city_year_lst_lc.csv`

**2,244 rows** – one row per city × analysis year × LC class.

| Column | Description |
|--------|-------------|
| `city` | City name |
| `year` | Analysis year (2000, 2005, 2010, 2015, 2020) |
| `LC_class` | LC class code (1=Impervious, 2=Vegetation, 3=Cropland, 4=Water, 5=Bare) |
| `LC_percent` | Percentage of city area covered by this LC class (%) |
| `mean_LST` | Mean summer LST for this LC class in this city‑year (K) |
| `max_LST` | Maximum summer LST (K) |
| `mean_top10_LST` | Mean of 90th–100th percentile LST values (K) |
| `n_images` | Number of Landsat scenes composited |
| `sensor` | Landsat sensor used (L5, L7, L8) |

### `pixel_transitions_thermal_2000_2020.csv`

**Varies rows** – one row per city × LC transition type (off‑diagonal + stable).

| Column | Description |
|--------|-------------|
| `city` | City name |
| `transition` | LC conversion pathway (e.g., `veg→imp`) |
| `transition_area_pct` | Fraction of city area undergoing this transition (%) |
| `delta_LST` | Mean LST change 2000→2020 for those pixels (K) |
| `delta_max_LST` | Max LST change (K) |
| `delta_top10_LST` | Top‑10% LST change (K) |
| `mean_LST_2000` / `mean_LST_2020` | Baseline and final mean LST (K) |
| `n_pixels` | Number of pixels in this transition class |
| `n_images_2000` / `n_images_2020` | Number of Landsat scenes for each year |
| `sensor_2000` / `sensor_2020` | Landsat sensor used |

### `city_list.csv`

**100 rows** – one row per study city.

| Column | Description |
|--------|-------------|
| `city` | City name |
| `country` | Country of the city |
| `latitude` | Latitude of the city center (decimal degrees) |
| `longitude` | Longitude of the city center (decimal degrees) |
| `hemisphere` | Northern or Southern |
| `gee_asset_id` | GEE asset path of the city boundary (for reference) |

This file is provided for reference and transparency; the Python scripts do not directly read it. The actual boundaries used in the analysis are stored in the GEE asset listed above.

## Data Sources

- **LST:** Landsat 5, 7, 8, 9 (USGS), processed in Google Earth Engine using the emissivity correction of Ermida et al. (2020).
- **Land Cover:** GLAD global land cover and land use change dataset (Potapov et al. 2022, *Frontiers in Remote Sensing*).  
  [https://doi.org/10.3389/frsen.2022.856903](https://doi.org/10.3389/frsen.2022.856903)
- **City boundaries:** Administrative polygons from OpenStreetMap via the OSMnx Python package (Boeing 2017, *Computers, Environment and Urban Systems*).

## Global Comparison Data (`raw/` subfolder)

Used in Figure 2 as global reference series overlaid on the city-level LST trends.

### `raw/berkeley_earth_land_tavg.csv`
Global mean land-only surface temperature, 2000–2020. Source: Rohde, R. A. and Hausfather, Z. (2020). *Earth Syst. Sci. Data*, 12, 3469–3479. https://doi.org/10.5194/essd-12-3469-2020. Regenerate with `scripts/00_fetch_berkeley_land.py`.

### `raw/noaa_oni.csv`
NOAA Climate Prediction Center Oceanic Niño Index (ONI), seasonal values, with computed El Niño/La Niña episode flags. Classification: ONI ≥ +0.5°C (El Niño) or ≤ −0.5°C (La Niña), sustained for ≥5 consecutive overlapping 3-month seasons (NOAA CPC standard). Each calendar year in Figure 2 is labeled by its DJF (winter) season only, so a year is marked only if it officially qualifies under this rule. Regenerate with `scripts/00_fetch_noaa_oni.py`. See `raw/noaa_oni.meta.json` for the exact year lists used and source citation.

## Notes

- Missing values (e.g., no valid LST pixels for a given city‑year‑LC combination) are omitted from the CSV.
- LC class codes are consistent with the reclassification scheme described in the main paper (Table 1).
- For the transition file, only transitions occurring in at least one city are included; rare transitions may appear for only a few cities.