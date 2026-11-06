# My-4Cast: Multimodel Operational Weather Forecasting Pipeline for Colombia

[![Platform](https://img.shields.io/badge/Web_Platform-weather.dnieves.stream-0284c7?style=flat&logo=cloudflare)](https://weather.dnieves.stream)
[![API](https://img.shields.io/badge/Sounding_API-sounding.dnieves.stream-10b981?style=flat)](https://sounding.dnieves.stream/api/health)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**My-4Cast** is an open scientific pipeline that automates the acquisition, spatial cropping, statistical condensation, Zarr storage, and dissemination of high-resolution numerical and Artificial Intelligence weather forecasts over continental, insular, and maritime Colombia.

---

## 1. Multimodel Inventory and Data Sources

The platform continuously processes **11 state-of-the-art meteorological models** covering physical Numerical Weather Prediction (NWP), Deep Learning foundation models, and satellite-calibrated precipitation systems.

### Comprehensive Sources Table

| Identifier | Model / System | Author / Institution | Paradigm | Spatial Grid | Temporal Step | Horizon | Primary Data Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `wn3` | **WeatherNext 3** | Google DeepMind / ECMWF | AI Ensemble (64 members) | $0.10^\circ$ (~10 km) | 1 hour | 360 h (15 days) | Google Cloud Storage (`gs://weathernext3_statistics_spatial/`) |
| `ecmwf_ifs` | **IFS ENS 15-day Open** | ECMWF | Physical NWP (51 members) | $0.25^\circ$ (~28 km) | 3 h (1–6d) / 6 h (7–15d) | 360 h (15 days) | ECMWF Open Data / Earthmover S3 (`dynamical-ecmwf-ifs-ens`) |
| `ecmwf_aifs_ens` | **AIFS ENS 15-day** | ECMWF | AI Ensemble (51 members) | $0.25^\circ$ (~28 km) | 6 hours | 360 h (15 days) | ECMWF Open Data / Earthmover S3 (`dynamical-ecmwf-aifs-ens`) |
| `ecmwf_aifs_single` | **AIFS Single** | ECMWF | AI Deterministic | $0.25^\circ$ (~28 km) | 6 hours | 360 h (15 days) | ECMWF Open Data / Earthmover S3 (`dynamical-ecmwf-aifs-single`) |
| `noaa_gfs` | **NOAA GFS** | NCEP / NOAA | Physical NWP Deterministic | $0.25^\circ$ (~28 km) | 1 h (to 120h) / 3 h (to 384h) | 384 h (16 days) | NOAA Open Data / Earthmover S3 (`dynamical-noaa-gfs`) |
| `dwd_icon` | **DWD ICON Global** | Deutscher Wetterdienst (DWD) | Physical NWP Deterministic | $0.125^\circ$ (~13 km) | 3 hours | 180 h (7.5 days) | DWD OpenData Server (`opendata.dwd.de/weather/nwp/icon/`) |
| `chirps_gefs` | **CHIRPS-GEFS v3** | UC Santa Barbara / CHC | Hybrid Satellite + GEFS | $0.05^\circ$ (~5.5 km) | 24 hours (daily) | 384 h (16 days) | CHC UCSB Server (`data.chc.ucsb.edu/products/CHIRPS-GEFS_precip/`) |
| `graphcast_gfs` | **GraphCast GFS** | Google DeepMind / NOAA | AI Deterministic (GNN) | $0.25^\circ$ (~28 km) | 6 hours | 240 h (10 days) | NOAA Open Data / Earthmover S3 |
| `aurora_gfs` | **Aurora GFS** | Microsoft Research / NOAA | AI Foundation Model | $0.25^\circ$ (~28 km) | 6 hours | 240 h (10 days) | NOAA Open Data / Earthmover S3 |
| `fourcastnet_gfs` | **FourCastNet v2 GFS** | NVIDIA / NOAA | AI Deterministic (AFNO) | $0.25^\circ$ (~28 km) | 6 hours | 240 h (10 days) | NOAA Open Data / Earthmover S3 |
| `pangu_gfs` | **Pangu-Weather GFS** | Huawei Cloud / NOAA | AI Deterministic (3D Earth) | $0.25^\circ$ (~28 km) | 6 hours | 240 h (10 days) | NOAA Open Data / Earthmover S3 |

---

## 2. System Architecture

The pipeline operates as a **four-tier hybrid architecture**, decoupling heavy planetary cloud datasets from client delivery:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Planetary Cloud Datasets (GCS / S3 / Icechunk Stores)    │
│    Google DeepMind · ECMWF · NOAA · DWD · UCSB CHC          │
└──────────────────────────────┬──────────────────────────────┘
                               │ High-Speed Network
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Cloud Cropper Workers (GitHub Actions CI/CD)              │
│    - Verifies 360-hour forecast completeness (anti-NaN)     │
│    - Extracts Colombia spatial domain [-5 to 16.5°N, -85 to │
│      -60°W] across 15 physical parameters                   │
│    - Publishes compressed multi-part releases               │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS CDN Distribution
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Automated Processing Node (Linux Server Pipeline)        │
│    - Ingestion: Fetch, reassemble, atomic Zarr append       │
│    - Multi-model Web Export: JSON telemetry & 3,960 frames  │
│    - Video Engine: H.264 MP4 rendering & Cloud Archive      │
│    - Sounding API: FastAPI + LRU Cache on Port 8000         │
└───────────────┬─────────────────────────────┬───────────────┘
                │ Cloudflare Tunnel           │ Git CI Deploy
                ▼                             ▼
┌───────────────────────────────┐ ┌───────────────────────────┐
│ 4a. Point Sounding API        │ │ 4b. Synoptic Web UI       │
│     sounding.dnieves.stream   │ │     weather.dnieves.stream│
│  - Arbitrary pixel sampling   │ │  - Interactive SPA        │
│  - Rate limiting (60 req/min) │ │  - Leaflet + Chart.js     │
│  - Extraterrestrial ToA flux  │ │  - Real-time wind quivers │
└───────────────────────────────┘ └───────────────────────────┘
```

---

## 3. Usage and API Endpoints

### 3.1 Web Platform
Access the production dashboard at **[https://weather.dnieves.stream](https://weather.dnieves.stream)**:
- **Clean Map Mode**: Toggle panels on/off for unobstructed cartographic analysis.
- **Multimodel Selector**: Switch between WeatherNext 3, ECMWF IFS, AIFS, NOAA GFS, DWD ICON, and experimental AI models.
- **Diagnostic Console**: Open the responsive drawer for 15-day multi-axis meteograms (precipitation, temperature, wind, cloud cover, and solar irradiance).
- **Point Sounding**: Click any point across Colombia to request real-time time series computed on demand from the numerical Zarr store.

### 3.2 Public Sounding API
The arbitrary point extraction service is accessible via HTTPS:

```bash
# Health check and service status
curl -s "https://sounding.dnieves.stream/api/health"

# Query custom coordinates (e.g. 6.01°N, 73.67°W on WeatherNext 3)
curl -s "https://sounding.dnieves.stream/api/sounding?lat=6.01&lon=-73.67&model=wn3"
```

**API Characteristics**:
- **Rate Limit**: 60 requests/minute per client IP (HTTP 429 response on breach).
- **Caching**: Global edge CDN caching with `Cache-Control: public, max-age=14400, stale-while-revalidate=3600`.
- **Response Format**: Compact JSON containing hourly series (360h) for percentiles p10, p50, and p90.

---

## 4. Local Installation and Execution

### Requirements
- Linux OS (Ubuntu 22.04 LTS or superior recommended)
- Python 3.11+
- FFmpeg (for video rendering)

```bash
# Clone the repository
git clone https://github.com/Duvancho321/My-4Cast.git
cd My-4Cast

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running Components
```bash
# Ingest latest Colombia crop from cloud release
python scripts/00_fetch_cloud_wn3.py

# Export web JSON and spatial PNG frames for all models
python scripts/02_export_web_data.py all

# Launch the Point Sounding Microservice locally
uvicorn src.api_sounding:app --host 0.0.0.0 --port 8000
```

---

## 5. Scientific and Operational Disclaimer

> [!WARNING]
> **Scientific & Research Use Only**:  
> The forecasts and data visualizations provided by **My-4Cast** are generated by experimental numerical models and artificial intelligence research systems (including Google DeepMind WeatherNext 3, ECMWF IFS/AIFS, and NOAA GFS).  
> 
> They are intended solely for academic research, operational evaluation, and scientific inquiry. They **do not constitute official weather warnings or alerts** and must not be used as the primary basis for emergency management, disaster response, navigation, or critical decision-making. For official warnings and meteorological bulletins in Colombia, consult the competent national authorities (such as **IDEAM**).

---

## 6. Attributions and Open-Source Acknowledgments

We gratefully acknowledge the researchers, organizations, and open-source communities whose work makes this project possible:

- **Google DeepMind**: For WeatherNext 3 and GraphCast models and data access via Google Cloud Public Datasets.
- **European Centre for Medium-Range Weather Forecasts (ECMWF)**: For the Integrated Forecasting System (IFS) and Artificial Intelligence Forecasting System (AIFS) open data.
- **National Oceanic and Atmospheric Administration (NOAA / NCEP)**: For the Global Forecast System (GFS) and open model initiatives.
- **Deutscher Wetterdienst (DWD)**: For the ICON global model open data server.
- **UC Santa Barbara Climate Hazards Center (CHC)**: For the CHIRPS-GEFS rainfall dataset.
- **Microsoft Research**: For the Aurora atmospheric foundation model.
- **NVIDIA Corporation**: For the FourCastNet v2 architecture.
- **Huawei Cloud**: For the Pangu-Weather model.
- **Software Libraries**: Built on [Leaflet](https://leafletjs.com/), [Chart.js](https://www.chartjs.org/), [Tailwind CSS](https://tailwindcss.com/), [FastAPI](https://fastapi.tiangolo.com/), [Xarray](https://docs.xarray.dev/), [Zarr](https://zarr.readthedocs.io/), [Cartopy](https://scitools.org.uk/cartopy/), and [Matplotlib](https://matplotlib.org/).

---

## 7. License

This repository is distributed under the **MIT License**. Original model outputs and meteorological datasets remain subject to their respective provider terms and open-data licenses.
