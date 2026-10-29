"""
00_get_wn3.py — Descarga de pronósticos WeatherNext 3 para Colombia en Zarr.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.0.2"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-10-29][Duvan]: Soporte para horizonte 360h y selección de variables.
"""

from sys import argv
from os.path import exists
from shutil import rmtree
from numpy import timedelta64
from obstore.store import GCSStore
from zarr.storage import ObjectStore
from xarray import Dataset, open_zarr

#%% CONFIGURACIÓN
run_id      = argv[1] if len(argv) > 1 else '20260826_00hr_01_preds'
n_horas     = int(argv[2]) if len(argv) > 2 else 360
tipo_vars   = argv[3] if len(argv) > 3 else 'precipitation'
bucket_name = 'weathernext3_statistics_spatial'
prefix_run  = f'weathernext_3_0_0_statistics/zarr/2026_to_present/{run_id}/predictions.zarr'
lat_min     = -5.0
lat_max     = 16.5
lon_min     = 275.0  # -85.0° a convención 0-360
lon_max     = 294.0  # -66.0° a convención 0-360
ruta_zarr   = '/mnt/datos/dnieves/WN3/raw/colombia_weathernext3.zarr'
ruta_tmp    = f'/mnt/datos/dnieves/WN3/staging/{run_id}.zarr'

#%% EXTRACCIÓN Y RECORTE
ds_remote = open_zarr(ObjectStore(GCSStore(bucket=bucket_name, prefix=prefix_run)))
vars_desc = list(ds_remote.data_vars) if tipo_vars == 'all' else [v for v in ds_remote.data_vars if 'precipitation' in v]

recorte = ds_remote[vars_desc].sel(
    lat_0p1=slice(lat_min, lat_max),
    lon_0p1=slice(lon_min, lon_max),
    lead_time=slice(timedelta64(1, 'h'), timedelta64(n_horas, 'h'))
)

if any('0p05' in str(v.dims) for v in recorte.data_vars.values()):
    recorte = recorte.sel(lat_0p05=slice(lat_min, lat_max), lon_0p05=slice(lon_min, lon_max))

ds_col = recorte.expand_dims('init_time').load()

#%% PERSISTENCIA ATÓMICA
rmtree(ruta_tmp, ignore_errors=True)
ds_col.to_zarr(ruta_tmp, mode='w')

if exists(ruta_zarr):
    rmtree(ruta_zarr, ignore_errors=True)
ds_col.to_zarr(ruta_zarr, mode='w')
rmtree(ruta_tmp, ignore_errors=True)
