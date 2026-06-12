# Google Earth Engine Scripts

This folder contains the JavaScript code used to extract Landsat‑based LST and GLAD land cover data for 100 global cities.

## Scripts

### `01_extract_city_lst_lc_per_year.js`

**Purpose:**  
For each city and each analysis year (2000, 2005, 2010, 2015, 2020), compute:
- Percentage of each LC class within the city boundary.
- Mean, maximum, and mean of the top‑10% summer LST (Kelvin) for each LC class.
- Number of valid images and sensor used.

**Outputs:**  
CSV files exported to Google Drive (one per batch). After merging all batches, rename to `city_year_lst_lc.csv`.

### `02_pixel_transition_analysis.js`

**Purpose:**  
For each city, identify every pixel that changed LC class between 2000 and 2020. For each transition type (off‑diagonal and stable), compute:
- Percentage of city area occupied by that transition.
- Mean, max, and top‑10% LST in 2000 and 2020.
- ΔLST, ΔmaxLST, Δtop10LST (2020 – 2000).

**Outputs:**  
CSV files exported to Google Drive (one per batch). After merging, rename to `pixel_transitions_thermal_2000_2020.csv`.

## City Boundaries

The GEE script loads city boundaries from a private asset:

`projects/ee-saghisarafi/assets/Global_UHI_City_Boundaries`

For transparency, a complete list of the 100 cities, along with their coordinates and other metadata, is provided in the `data/city_list.csv` file. You can use this list to create your own boundary FeatureCollection in GEE (e.g., by buffering points or using administrative boundaries from a public dataset like FAO/GAUL). The script expects a `name` property for each city.

## How to Run

1. Go to the [Google Earth Engine Code Editor](https://code.earthengine.google.com/).
2. Create a new script and paste the entire content of the desired `.js` file.
3. **Replace the city boundary asset path** (`projects/ee-saghisarafi/assets/Global_UHI_City_Boundaries`) with your own FeatureCollection asset that contains a `name` property for each city.
4. Adjust `batchSize` if needed (start with 1 for testing, then increase to 5–10 for production).
5. Click **Run**. The script will export CSV files to your Google Drive (folder: `LST_LC_Extractions` or `LC_Pixel_Transitions_2000_2020`).
6. Download all CSV files and merge them locally (use a simple Python script or command line).

## Dependencies (GEE Assets)

All input datasets are publicly available:
- **GLAD LC:** `projects/glad/GLCLU2020/v2/LCLUC_YYYY` (where YYYY = 2000, 2005, 2010, 2015, 2020)
- **Land mask:** `projects/glad/OceanMask`
- **Landsat LST module:** `users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js` (Ermida et al. 2020)

## Runtime

- Annual extraction (~5 years × 100 cities): **2–4 hours** (batches of 20 cities)
- Pixel transition analysis (2000→2020 only): **1–2 hours** (batches of 1 city recommended)

## Notes

- City boundaries are simplified (`simplify(500)`) to reduce vertex count and avoid memory errors.
- The top‑10% LST is approximated as `(p90 + p100) / 2`, matching the city‑level script.
- If a city‑year has no valid LST pixels, the script returns a `NO_DATA` row for that city.