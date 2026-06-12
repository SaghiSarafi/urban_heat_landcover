# Landcover Change and Urban Heat in a Warming Climate: A Global Satellite Perspective

[![DOI](https://zenodo.org/badge/DOI/10.xxxx/zenodo.xxxxxxx.svg)](https://doi.org/10.xxxx/zenodo.xxxxxxx)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)

**Authors:** Saghi Sarafi¹²³, Christopher D. Lippitt¹³, Gernot Paulus²

¹ Department of Geography and Environmental Studies, University of New Mexico, USA  
² Department of Geoinformation and Environmental Technologies, Carinthia University of Applied Sciences, Austria  
³ UNM Center for the Advancement of Spatial Informatics Research and Education (ASPIRE)

---

## Overview

This repository contains all data, code, and supplementary materials for the study analyzing how **land cover (LC) change mediates Urban Heat Island (UHI) dynamics** across **100 major global cities** from **2000 to 2020**, using Google Earth Engine (GEE) with Landsat-derived Land Surface Temperature (LST) and the GLAD land‑cover dataset.

The study introduces a **hierarchical three‑level analytical framework**:

| Level | Name | What it answers |
|-------|------|-----------------|
| 1 | Net Compositional Change | Do cities that gain impervious cover warm more? |
| 2 | Transition‑Specific Pathways | Which specific LC conversions cause warming or cooling? |
| 3 | Relative Temperature Index (RTI) | Are impervious surfaces always warmer than city averages? |

---

## Repository Structure

```
urban_heat_landcover/
│
├── README.md ← This file
├── LICENSE ← MIT License
├── requirements.txt ← Python dependencies
├── CITATION.cff ← Citation metadata
│
├── data/
│ ├── README_data.md ← Data description and provenance
│ ├── city_year_lst_lc.csv ← City × year × LC class LST summary (2,244 rows)
│ ├── pixel_transitions_thermal_2000_2020.csv ← Pixel‑level LC transition thermal responses
│ └── city_list.csv ← 100 study cities with coordinates and metadata
│
├── GEE/
│ ├── README_GEE.md ← GEE script documentation
│ ├── 01_extract_city_lst_lc_per_year.js ← Annual LST + LC extraction (all years)
│ └── 02_pixel_transition_analysis.js ← Pixel‑level transition analysis (2000→2020)
│
├── scripts/
│ ├── README_scripts.md ← Script descriptions and run order
│ ├── figure_02_lst_temporal_trends.py ← Figure 2 (temporal LST trends)
│ ├── figure_03_landcover_composition_trends.py ← Figure 3 (LC trends)
│ ├── figure_04_lc_vs_lst_scatter_2020.py ← Figure 4 (LC vs LST 2020)
│ ├── figure_05_delta_lc_vs_delta_lst.py ← Figure 5 (ΔLC vs ΔLST, mean)
│ ├── table_03_correlations_2020.py ← Table 3 (2020 correlations)
│ ├── table_04_correlations_delta.py ← Table 4 (Δcorrelations)
│ ├── table_05_net_change_regression.py ← Table 5 (net change regression)
│ ├── table_06_transition_analysis.py ← Tables 6 (transition analysis)
│ └── table_07_rti_statistics.py ← Table 7 (RTI)
│
├── outputs/
│ ├── figures/ ← Generated figures (PNG, 300 dpi)
│ └── tables/ ← Generated CSV result tables
│
└── docs/
```

---

## Data Description

### `data/city_year_lst_lc.csv` — City‑Level LST Summary
**2,244 rows** | One row per city × year × LC class

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
| `sensor` | Landsat sensor used |

### `data/pixel_transitions_thermal_2000_2020.csv` — Pixel‑Level Transition Thermal Responses
One row per city × transition type (off‑diagonal + stable). Contains:

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

---

## Google Earth Engine Scripts

Both scripts are located in the `GEE/` folder and are fully documented.

### `01_extract_city_lst_lc_per_year.js`
- **Purpose:** For each analysis year (2000,2005,2010,2015,2020), compute LC percentages and LST metrics (mean, max, top‑10%) for each city and LC class.
- **Inputs:** City boundaries (user asset), GLAD LC, Landsat LST module (Ermida).
- **Outputs:** CSV files exported to Google Drive; merge to obtain `city_year_lst_lc.csv`.

### `02_pixel_transition_analysis.js`
- **Purpose:** For each city, identify every pixel that changed LC between 2000 and 2020. For each transition type, compute area percentage and LST changes (mean, max, top‑10%).
- **Inputs:** Same as above.
- **Outputs:** CSV files exported to Google Drive; merge to obtain `pixel_transitions_thermal_2000_2020.csv`.

To run, paste each script into the [Google Earth Engine Code Editor](https://code.earthengine.google.com/) and execute. All input datasets are publicly available.

---

## Python Scripts

### Run Order

```
table_03_correlations_2020.py → Table 3
table_04_correlations_delta.py → Table 4
table_05_net_change_regression.py → Table 5
table_06_transition_analysis.py → Tables 6
table_07_rti_statistics.py → Table 7
figure_02_lst_temporal_trends.py → Figure 2
figure_03_landcover_composition_trends.py → Figure 3
figure_04_lc_vs_lst_scatter_2020.py → Figure 4
figure_05_delta_lc_vs_delta_lst.py → Figure 5
```
---

### Script Details

**`figure_02_lst_temporal_trends.py`**  
Plots mean and maximum LST by land cover class across 2000–2020, overlaid with global mean land temperature (Berkeley Earth) and ENSO event markers (NOAA CPC ONI).

**Inputs:** `data/city_year_lst_lc.csv`  
**Outputs:** `outputs/figures/figure_02_lst_temporal_trends.png`  
**Key parameters:** ENSO years based on NOAA CPC Oceanic Niño Index (ONI ≥ 0.5 / ≤ −0.5 for ≥5 consecutive months)

---

**`figure_03_landcover_composition_trends.py`**  
Plots land cover percentage composition per year across all 100 cities — bold lines for cross-city mean, thin lines for individual city trajectories.

**Inputs:** `data/city_year_lst_lc.csv`  
**Outputs:** `outputs/figures/figure_03_landcover_composition_trends.png`  
**Key parameters:** Individual city trajectories shown with α=0.12; cities with only one year of data are excluded from trajectory plots

---

**`figure_04_lc_vs_lst_scatter_2020.py`**  
Creates 5-panel scatter plot (one per LC class) showing the relationship between LC percent cover and mean/max/top-10% LST across cities in 2020. Pearson r, p, and n annotated per panel. Regression lines shown only for statistically significant correlations (p < 0.05).

**Inputs:** `data/city_year_lst_lc.csv`  
**Outputs:** `outputs/figures/figure_04_lc_vs_lst_scatter_2020.png`

---

**`figure_05_delta_lc_vs_delta_lst.py`**  
Creates 5-panel scatter plot (one per LC class) showing the relationship between ΔLC% (2000–2020) and ΔLST (mean). Pearson r and p annotated.

**Inputs:** `data/city_year_lst_lc.csv`  
**Outputs:** `outputs/figures/figure_05_delta_lc_vs_delta_lst.png`

---

**`table_05_net_change_regression.py`**  
OLS multiple regression of city-level LST change (ΔLST, ΔLSTMax, ΔLSTMax10) on net percentage change in each LC class between 2000 and 2020. Implements **Level 1** of the hierarchical framework.

**Inputs:** `data/city_year_lst_lc.csv`  
**Outputs:** `outputs/tables/table_05_net_change_regression.csv`  
**Model:** `statsmodels` OLS with intercept; 5 LC predictors entered simultaneously  
**Key result:** R² ≈ 0.186; impervious (β = +0.1696 K/%, p = 0.016) and cropland loss (β = −0.2173 K/%, p = 0.031) are significant predictors

---

**`table_06_transition_analysis.py`**  
Full **Level 2** transition analysis pipeline:
- Computes direct pixel‑level thermal responses (ΔLST, ΔLSTMax, ΔLSTMax10) for each LC transition type across all cities (Table 6)

**Inputs:** `data/pixel_transitions_thermal_2000_2020.csv`  
**Outputs:**  
- `outputs/tables/table_06_direct_mean.csv`
- `outputs/tables/table_06_direct_max.csv`
- `outputs/tables/table_06_direct_top10.csv`
- `outputs/tables/table_06_direct_thermal_all_metrics.csv`

**Key result:** Water loss drives the strongest warming (wat→bare = +4.93 K); all →imp conversions produce +2.9–4.2 K warming; extreme heat metrics are ≈1.6× larger for water‑loss transitions.

---

**`table_07_rti_statistics.py`**  
Computes Relative Temperature Index (RTI) for each LC class across all city-years. RTI = class mean LST / city‑year mean LST. Values >1 indicate warmer than city average.

**Inputs:** `data/city_year_lst_lc.csv`  
**Outputs:** `outputs/tables/table_07_rti_statistics.csv`  
**Key result:** Impervious RTI = 1.0106 ± 0.0069; Water RTI = 0.9880 ± 0.0088; Vegetation RTI = 1.0000 ± 0.0065

---

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/urban-heat-landcover.git
cd urban-heat-landcover

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### `requirements.txt`
```
pandas>=1.5
numpy>=1.23
matplotlib>=3.6
seaborn>=0.12
scipy>=1.9
statsmodels>=0.14
```

---

## Citation

If you use this code or data, please cite:

> Sarafi, S., Lippitt, C. D., & Paulus, G. (2026). Landcover Change and Urban Heat in a Warming Climate: A Global Satellite Perspective. *[Journal Name]*. https://doi.org/XXXX

BibTeX:
```bibtex
@article{sarafi2026,
  author  = {Sarafi, Saghi and Lippitt, Christopher D. and Paulus, Gernot},
  title   = {Landcover Change and Urban Heat in a Warming Climate: A Global Satellite Perspective},
  journal = {[Journal Name]},
  year    = {2026},
  doi     = {XXXX}
}
```

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

This research was supported by the **Austrian Marshall Plan Foundation**. The authors gratefully acknowledge USGS for Landsat data, Google Earth Engine for cloud computing infrastructure, and the GLAD team (Potapov et al.) for the global land cover dataset.

---

## Contact

**Saghi Sarafi** — saghi3@unm.edu  
Department of Geography and Environmental Studies, University of New Mexico
