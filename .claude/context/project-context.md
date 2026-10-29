# Contexto del Proyecto: My-4Cast

## Propósito
`My-4Cast` es una plataforma y pipeline para la recolección, postprocesamiento, calibración estadística/ML y generación de pronósticos meteorológicos de alta resolución.

## Entornos y Rutas
- **Código y Operaciones (Producción & Desarrollo simultáneos)**:
  `/home/dnieves/Documentos/My-4Cast`
- **Almacén Base de Datos Masivos**:
  `/mnt/datos/dnieves/WN3`
  - Subcarpeta prevista para datos crudos: `/mnt/datos/dnieves/WN3/raw/` (solo lectura tras descarga).
  - Subcarpeta para procesados/intermedios: `/mnt/datos/dnieves/WN3/processed/` o `zarr/`.
  - Subcarpeta para checkpoints/modelos: `/mnt/datos/dnieves/WN3/models/`.

## Stack Tecnológico
- **Manipulación de Datos Atmosféricos en Grilla**: `xarray`, `dask`, `netCDF4`, `zarr`, `metpy`.
- **Análisis Numérico y ML**: `numpy`, `scipy`, `pandas`, `scikit-learn`, `torch` (si aplica).
- **Visualización Científica**: `matplotlib`, `cartopy` (siguiendo directrices de `plots-style.md`).
- **Control y Automatización**: `cron`, scripts bash minimalistas, Python con tipado estricto.

## Datos Clave: WN3
- Corresponde a pronósticos numéricos de alta resolución (típicamente WRF Nested Domain 3 o equivalentes de área limitada).
- Variables típicas: Viento (U, V, W), Temperatura a 2m, Humedad Relativa / Específica, Presión a nivel de superficie / geopotencial, Precipitación acumulada, Radiación solar.
- Formatos esperados: NetCDF / GRIB2 / Zarr.
