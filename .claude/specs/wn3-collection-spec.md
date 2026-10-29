# Especificación Técnica: Conexión y Recolección WeatherNext 3 (WN3)

## Origen
- **Plataforma**: Google DeepMind / Google Research WeatherNext 3.
- **Acceso Autorizado**: `dnieves@unal.edu.co`.
- **Buckets GCS**:
  - `gs://weathernext3_spatial/weathernext_3_0_0/zarr/`
  - `gs://weathernext3_statistics_spatial/weathernext_3_0_0_statistics/zarr/`
- **Mecanismo**: Google Cloud Storage con Requester Pays + Zarr.

## Stack de Ingesta
- `xarray`
- `zarr`
- `gcsfs` / `obstore`

## Pipeline de Extracción
1. Conexión autenticada vía Application Default Credentials (ADC) asociadas a `dnieves@unal.edu.co`.
2. Apertura remota de store Zarr con `xarray.open_zarr(...)`.
3. Slicing espaciotemporal (bounding box sobre Colombia / región de interés) para evitar descargas innecesarias del globo terráqueo completo.
4. Escritura atómica a `/mnt/datos/dnieves/WN3/raw/` (o NetCDF local).
