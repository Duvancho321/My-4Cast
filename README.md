# My-4Cast

**Multimodel weather forecasts for Colombia, refreshed every cycle and served as a static web map and a point-sounding API.**

[![Web](https://img.shields.io/badge/web-weather.dnieves.stream-2874B5?style=flat)](https://weather.dnieves.stream)
[![Sounding API](https://img.shields.io/badge/API-sounding.dnieves.stream-1F6A45?style=flat)](https://sounding.dnieves.stream/api/health)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0F2A44.svg)](LICENSE)

My-4Cast crops 11 global forecast systems (AI, physical and satellite-based) to the Colombian domain, condenses ensembles to P10/P50/P90, stores them as Zarr and publishes two products:

- **[weather.dnieves.stream](https://weather.dnieves.stream)**: an interactive map with 360 hourly frames per variable, wind vectors, 45 monitoring points and 15-day meteograms.
- **[sounding.dnieves.stream](https://sounding.dnieves.stream/api/health)**: an API that returns the full time series for any point in Colombia.

> [!WARNING]
> Research and information use only. These are experimental model outputs, not official warnings. Do not use them for emergency management, navigation or life-critical decisions. For official warnings in Colombia, consult **IDEAM**.

---

## Contents

1. [Forecast sources](#1-forecast-sources)
2. [How it works](#2-how-it-works)
3. [Using the API](#3-using-the-api)
4. [Running it locally](#4-running-it-locally)
5. [Repository layout](#5-repository-layout)
6. [Data terms and acknowledgments](#6-data-terms-and-acknowledgments)
7. [Author and license](#7-author-and-license)

---

## 1. Forecast sources

| ID | System | Provider | Type | Grid | Step | Horizon |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `wn3` | WeatherNext 3 | Google DeepMind | AI ensemble (64 members) | 0.10° (~10 km) | 1 h | 360 h |
| `ecmwf_ifs` | IFS ENS (open data) | ECMWF | Physical ensemble (51 members) | 0.25° | 3 h → 6 h | 360 h |
| `ecmwf_aifs_ens` | AIFS ENS | ECMWF | AI ensemble (51 members) | 0.25° | 6 h | 360 h |
| `ecmwf_aifs_single` | AIFS Single | ECMWF | AI deterministic | 0.25° | 6 h | 360 h |
| `noaa_gfs` | GFS | NOAA / NCEP | Physical deterministic | 0.25° | 1 h → 3 h | 384 h |
| `dwd_icon` | ICON Global | DWD | Physical deterministic | 0.125° | 3 h | 180 h |
| `chirps_gefs` | CHIRPS-GEFS v3 | UC Santa Barbara CHC | Satellite + GEFS (precipitation) | 0.05° | 24 h | 384 h |
| `graphcast_gfs` | GraphCast | Google DeepMind / NOAA | AI deterministic | 0.25° | 6 h | 240 h |
| `aurora_gfs` | Aurora | Microsoft Research / NOAA | AI deterministic | 0.25° | 6 h | 240 h |
| `fourcastnet_gfs` | FourCastNet v2 | NVIDIA / NOAA | AI deterministic | 0.25° | 6 h | 240 h |
| `pangu_gfs` | Pangu-Weather | Huawei Cloud / NOAA | AI deterministic | 0.25° | 6 h | 240 h |

Variables on the map: hourly precipitation (three schemes), 2 m temperature, 10 m and 100 m wind, surface solar radiation and total, low, mid and high cloud cover.

---

## 2. How it works

```text
Provider stores (GCS, S3, open-data servers)
        │
        ▼
GitHub Actions croppers ── check that all 360 h exist (no NaN), crop
        │                   lat −5…16.5°N, lon −85…−60°W, publish a release
        ▼
Processing node ── fetch, append to the Zarr cube atomically,
        │           export JSON + PNG frames, render MP4 animations
        ├──────────────► Static web map (Cloudflare Pages)
        └──────────────► Sounding API (FastAPI behind Cloudflare Tunnel)
```

| Stage | Where | Schedule |
| :--- | :--- | :--- |
| WeatherNext 3 cropper | `.github/workflows/crop_colombia.yml` | every 3 h (`20 */3 * * *` UTC) |
| Multimodel cropper | `.github/workflows/crop_multimodel_colombia.yml` | every 6 h (`45 */6 * * *` UTC) |
| Ingest, export, publish | `scripts/run_pipeline.sh` | four times a day |
| Sounding API | `src/api_sounding.py` | always on |

Color scales for every variable are defined once in [`src/paletas.py`](src/paletas.py). The web legend uses the same colors and breaks, so legend and map always match.

---

## 3. Using the API

```bash
# Service status
curl -s "https://sounding.dnieves.stream/api/health"

# Time series at 6.01°N 73.67°W from WeatherNext 3
curl -s "https://sounding.dnieves.stream/api/sounding?lat=6.01&lon=-73.67&model=wn3"
```

- `model` takes any ID from the table above.
- The response is JSON: an `info` block (point, grid) and hourly series per variable with `p10`, `p50` and `p90`.
- The limit is 60 requests per minute per IP; above that the API answers HTTP 429 with `Retry-After`.
- Responses are cached at the edge for 4 h.

---

## 4. Running it locally

Requirements: Linux, conda or micromamba, and FFmpeg (for the animations).

```bash
git clone https://github.com/Duvancho321/My-4Cast.git
cd My-4Cast
micromamba env create -f environment.yml   # or: conda env create -f environment.yml
micromamba activate my-4cast
```

```bash
python scripts/00_fetch_cloud_wn3.py          # ingest the latest WeatherNext 3 crop
python scripts/02_export_web_data.py all      # export JSON and PNG frames for all models
uvicorn src.api_sounding:app --port 8000      # start the sounding API
```

> [!NOTE]
> Storage paths are currently set for the production machine (`src/modelos.py`, `scripts/run_pipeline.sh`). Adjust them before running elsewhere. `requirements.txt` only covers the cloud croppers; use `environment.yml` for the full pipeline.

---

## 5. Repository layout

| Path | What it holds |
| :--- | :--- |
| `src/modelos.py` | Catalog of the 11 sources: IDs, paths, variables |
| `src/paletas.py` | Color scales and breaks for every variable |
| `src/descarga.py` | Atomic append of new cycles to the Zarr cube |
| `src/animacion.py` | Map rendering (Cartopy) and MP4 encoding (FFmpeg) |
| `src/api_sounding.py` | Sounding API: nearest-cell extraction, rate limit, LRU cache |
| `scripts/00_*.py`, `scripts/cloud_crop_*.py` | Download, crop and backfill |
| `scripts/01_animate_*.py` | Precipitation, temperature and radiation animations |
| `scripts/02_export_web_data.py` | JSON and frames for the web map |
| `scripts/03_upload_drive.py` | Animation archive |
| `scripts/run_pipeline.sh`, `scripts/watch_and_run_wn3.sh` | Orchestration |
| `.github/workflows/` | Cloud croppers and backfill |

---

## 6. Data terms and acknowledgments

Forecast data remain subject to each provider's terms: Google DeepMind (WeatherNext 3, GraphCast), ECMWF (IFS, AIFS open data), NOAA/NCEP (GFS and the NOAA machine-learning model runs), DWD (ICON open data), UC Santa Barbara Climate Hazards Center (CHIRPS-GEFS), Microsoft Research (Aurora), NVIDIA (FourCastNet) and Huawei Cloud (Pangu-Weather). Check each provider's terms before reusing the outputs.

Built with [Xarray](https://docs.xarray.dev/), [Zarr](https://zarr.readthedocs.io/), [Dask](https://www.dask.org/), [Cartopy](https://scitools.org.uk/cartopy/), [Matplotlib](https://matplotlib.org/), [FastAPI](https://fastapi.tiangolo.com/), [Leaflet](https://leafletjs.com/) and [Chart.js](https://www.chartjs.org/).

---

## 7. Author and license

My-4Cast is a personal project by **Duvan Nieves Ruiz** · [dnieves.sci@gmail.com](mailto:dnieves.sci@gmail.com).

Code released under the [MIT License](LICENSE).
