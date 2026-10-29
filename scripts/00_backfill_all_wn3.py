"""
00_backfill_all_wn3.py — Backfill de todas las variables (126 campos) de WeatherNext 3.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.1.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-10-29][Duvan]: Ingesta completa de 126 variables estadisticas en Zarr.
"""

from os.path import exists
from shutil import rmtree
from numpy import timedelta64
from obstore.store import GCSStore
from zarr.storage import ObjectStore
from xarray import Dataset, open_zarr

#%% CONFIGURACIÓN DE PARÁMETROS
bucket_wn3 = 'weathernext3_statistics_spatial'
lat_min    = -5.0
lat_max    = 16.5
lon_min    = 275.0
lon_max    = 300.0
ruta_zarr  = '/mnt/datos/dnieves/WN3/raw/colombia_wn3_full.zarr'
ruta_tmp   = '/mnt/datos/dnieves/WN3/staging/tmp_all_vars.zarr'

fechas     = [f'202610{d:02d}' for d in range(22, 29)]
horas      = ['00', '06', '12', '18']
runs       = [f'{f}_{h}hr_01_preds' for f in fechas for h in horas] + [
    '20261029_00hr_01_preds',
    '20261029_06hr_01_preds',
    '20261029_12hr_01_preds',
]

#%% PROCESAMIENTO SECUENCIAL DE TODAS LAS VARIABLES
print(f'Iniciando backfill completo ({len(runs)} corridas, 126 variables)...', flush=True)

for i, run_id in enumerate(runs):
    prefix_run = f'weathernext_3_0_0_statistics/zarr/2026_to_present/{run_id}/predictions.zarr'
    print(f'[{i+1}/{len(runs)}] Procesando {run_id}...', flush=True)
    
    ds_remote = open_zarr(ObjectStore(GCSStore(bucket=bucket_wn3, prefix=prefix_run)))
    
    sub = (ds_remote
        .sel(lat_0p1=slice(lat_min, lat_max), lon_0p1=slice(lon_min, lon_max),
             lat_0p05=slice(lat_min, lat_max), lon_0p05=slice(lon_min, lon_max),
             lead_time=slice(timedelta64(1, 'h'), timedelta64(360, 'h')))
        .expand_dims('init_time'))
    
    sub['init_time'].encoding['units'] = 'hours since 2026-10-22 00:00:00'
    sub['init_time'].encoding['dtype'] = 'int64'
    
    rmtree(ruta_tmp, ignore_errors=True)
    sub.to_zarr(ruta_tmp, mode='w')
    
    if i == 0 and not exists(ruta_zarr):
        sub.to_zarr(ruta_zarr, mode='w')
    else:
        sub.to_zarr(ruta_zarr, mode='a', append_dim='init_time')
        
    rmtree(ruta_tmp, ignore_errors=True)
    print(f'[{i+1}/{len(runs)}] Completado {run_id}.', flush=True)

print('Backfill completo de 126 variables finalizado con exito.', flush=True)
