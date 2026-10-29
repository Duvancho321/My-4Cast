"""
00_backfill_wn3.py — Ingesta cronológica ascendente de los últimos 7 días de WN3.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.0.1"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-10-29][Duvan]: Backfill continuo 22-29 octubre (Opción B).
"""

from os.path import exists
from shutil import rmtree
from numpy import timedelta64
from obstore.store import GCSStore
from zarr.storage import ObjectStore
from xarray import Dataset, open_zarr

#%% CONFIGURACIÓN
bucket_name = 'weathernext3_statistics_spatial'
lat_min     = -5.0
lat_max     = 16.5
lon_min     = 275.0  # -85.0° a convención 0-360
lon_max     = 300.0  # -60.0° a convención 0-360
ruta_zarr   = '/mnt/datos/dnieves/WN3/raw/colombia_weathernext3.zarr'
ruta_tmp    = '/mnt/datos/dnieves/WN3/staging/tmp_backfill.zarr'

runs = [
    '20261022_00hr_01_preds',
    '20261023_00hr_01_preds',
    '20261024_00hr_01_preds',
    '20261025_00hr_01_preds',
    '20261026_00hr_01_preds',
    '20261027_00hr_01_preds',
    '20261028_00hr_01_preds',
    '20261029_00hr_01_preds',
    '20261029_06hr_01_preds',
]

#%% PROCESO SECUENCIAL MONITOREADO
for i, run_id in enumerate(runs):
    prefix_run = f'weathernext_3_0_0_statistics/zarr/2026_to_present/{run_id}/predictions.zarr'
    print(f'[{i+1}/{len(runs)}] Descargando {run_id}...')
    
    ds_remote = open_zarr(ObjectStore(GCSStore(bucket=bucket_name, prefix=prefix_run)))
    vars_ppt  = [v for v in ds_remote.data_vars if 'precipitation' in v]
    
    ds_col = (ds_remote[vars_ppt]
        .sel(lat_0p1=slice(lat_min, lat_max), lon_0p1=slice(lon_min, lon_max),
             lead_time=slice(timedelta64(1, 'h'), timedelta64(360, 'h')))
        .expand_dims('init_time')
        .load())
    
    rmtree(ruta_tmp, ignore_errors=True)
    ds_col.to_zarr(ruta_tmp, mode='w')
    
    if i == 0 or not exists(ruta_zarr):
        rmtree(ruta_zarr, ignore_errors=True)
        ds_col.to_zarr(ruta_zarr, mode='w')
    else:
        ds_col.to_zarr(ruta_zarr, mode='a', append_dim='init_time')
        
    rmtree(ruta_tmp, ignore_errors=True)
    print(f'[{i+1}/{len(runs)}] Completado y apilado {run_id}.')
