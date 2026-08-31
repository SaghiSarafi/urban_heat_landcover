# Google Earth Engine Scripts

This folder contains the JavaScript code used to extract Landsat‑based LST, GLAD land cover, and GHS-SMOD urban extent data for 100 global cities.

## Scripts

### `01_extract_city_lst_lc_per_year.js`

**Purpose:**
For each city and each analysis year (2000, 2005, 2010, 2015, 2020), compute:
- Percentage of each LC class within the city boundary.
- Mean, maximum, and mean of the top‑10% summer LST (Kelvin) for each LC class.
- Number of valid images and sensor used.

Local summer season is used for each city: June 1 – August 31 for Northern Hemisphere cities, November 1 – March 31 for Southern Hemisphere cities (the wider window compensates for higher regional cloud cover during the Southern summer).

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

### `03_boundary_covariates_ghsl_compactness.js`

**Purpose:**
Computes two boundary-sensitivity covariates for each city, used in Table 5 (alongside the five land-cover predictors, in a single regression) to test whether administrative boundary characteristics confound the Level 1 net-change results:
- **Area ratio:** each city's administrative-boundary land area divided by the area of the corresponding GHS-SMOD Urban Centre extent (a population/built-up-density-based definition of urban extent, independent of administrative boundaries) — how much of the city's real full extent the boundary captures.
- **Perimeter-area ratio:** boundary shape irregularity (perimeter ÷ √area), addressing the reviewer's specific request for a compactness metric.

The script includes extensive handling for edge cases discovered during development: ocean-inclusive boundaries (e.g., Tokyo's OSM boundary spans mainland Japan to the remote Izu/Ogasawara islands), a manual coordinate-override table for 10 cities where automated Urban Centre detection failed, and an automatic reliability flag for spurious single-pixel results. Full reasoning for each is documented in the script's inline comments. Baku City is excluded entirely — see the script header for the data-quality issue that prompted this.

**Outputs:**
CSV exported to Google Drive. Rename to `boundary_covariates_ghsl_compactness.csv`.

**Data source:** GHS-SMOD (Degree of Urbanisation settlement grid), Schiavina, Melchiorri and Pesaresi (2023), European Commission Joint Research Centre. https://doi.org/10.2905/A0DF7A6F-49DE-46EA-9BDE-563437A6E2BA

## City Boundaries

The GEE scripts load city boundaries from a private asset:

`projects/ee-saghisarafi/assets/Global_UHI_City_Boundaries`

For transparency, a complete list of the 100 cities, along with their coordinates and other metadata, is provided in the `data/city_list.csv` file. You can use this list to create your own boundary FeatureCollection in GEE (e.g., by buffering points or using administrative boundaries from a public dataset like FAO/GAUL). Scripts 01 and 02 expect a `name` property for each city.

## How to Run

1. Go to the [Google Earth Engine Code Editor](https://code.earthengine.google.com/).
2. Create a new script and paste the entire content of the desired `.js` file.
3. **Replace the city boundary asset path** (`projects/ee-saghisarafi/assets/Global_UHI_City_Boundaries`) with your own FeatureCollection asset that contains a `name` property for each city.
4. For scripts 01 and 02, adjust `batchSize` if needed (start with 1 for testing, then increase to 5–10 for production).
5. Click **Run**. Scripts 01 and 02 export CSV files directly; script 03 prints a reliability summary to the Console first, then requires manually starting the export task from the Tasks tab.
6. Download all CSV files and merge them locally (use a simple Python script or command line) where applicable (scripts 01 and 02 export in batches; script 03 exports as a single table).

## Dependencies (GEE Assets)

All input datasets are publicly available:
- **GLAD LC:** `projects/glad/GLCLU2020/v2/LCLUC_YYYY` (where YYYY = 2000, 2005, 2010, 2015, 2020)
- **Land mask:** `projects/glad/OceanMask`
- **Landsat LST module:** `users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js` (Ermida et al. 2020)
- **GHS-SMOD:** `JRC/GHSL/P2023A/GHS_SMOD_V2-0` (Schiavina et al. 2023), used only by script 03

## Runtime

- Annual extraction (~5 years × 100 cities): **2–4 hours** (batches of 20 cities)
- Pixel transition analysis (2000→2020 only): **1–2 hours** (batches of 1 city recommended)
- Boundary covariates (100 cities, single export): **well under 1 hour**

## Notes

- City boundaries are simplified (`simplify(500)`) to reduce vertex count and avoid memory errors in scripts 01 and 02.
- The top‑10% LST is approximated as `(p90 + p100) / 2`, matching the city‑level script.
- If a city‑year has no valid LST pixels, scripts 01 and 02 return a `NO_DATA` row for that city.
- Script 03 uses a 100m-scale land mask for its own area calculations, and correctly treats GHS-SMOD as native 1km resolution (not 100m) for its Urban Centre extent calculations — see inline comments for why this distinction matters.
