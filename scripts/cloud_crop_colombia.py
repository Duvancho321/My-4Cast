"""
cloud_crop_colombia.py — Extracción y recorte de WeatherNext 3 para Colombia en GitHub Actions.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.1.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-11-03][Duvan]: Worker de recorte para 15 variables fisicas seleccionadas.
"""

from sys import argv
from os.path import exists
from shutil import copyfile, make_archive, rmtree
from datetime import datetime, timezone
from obstore.store import GCSStore
from zarr.storage import ObjectStore
from numpy import timedelta64
from xarray import open_zarr

#%% CONFIGURACIÓN DE PARÁMETROS
lat_min    = -5.0
lat_max    = 16.5
lon_min    = 275.0
lon_max    = 300.0
bucket_wn3 = 'weathernext3_statistics_spatial'

bases_sel  = [
    'total_precipitation_1hr',
    'imerg_tp_1hr',
    'experimental_tp_1hr',
    'u_component_of_wind_10m',
    'v_component_of_wind_10m',
    'wind_speed_10m',
    'u_component_of_wind_100m',
    'v_component_of_wind_100m',
    'wind_speed_100m',
    'temperature_2m',
    'surface_solar_radiation_downwards_1hr',
    'total_cloud_cover',
    'low_cloud_cover',
    'medium_cloud_cover',
    'high_cloud_cover',
]

#%% DETERMINACIÓN DE CORRIDA A PROCESAR
def obtener_run_id():
    if len(argv) > 1 and argv[1] != 'auto':
        return argv[1]
    ahora  = datetime.now(timezone.utc)
    f_str  = ahora.strftime('%Y%m%d')
    h_int  = ahora.hour
    h_corr = '18' if h_int >= 20 else ('12' if h_int >= 14 else ('06' if h_int >= 8 else '00'))
    return f'{f_str}_{h_corr}hr_01_preds'

#%% EJECUCIÓN DEL RECORTE EN LA NUBE
run_id     = obtener_run_id()
prefix_run = f'weathernext_3_0_0_statistics/zarr/2026_to_present/{run_id}/predictions.zarr'
ruta_sal   = f'colombia_{run_id}.zarr'
ruta_zip   = f'colombia_{run_id}'

print(f'Procesando corrida: {run_id}', flush=True)
ds_remoto = open_zarr(ObjectStore(GCSStore(bucket=bucket_wn3, prefix=prefix_run)))

vars_validas = [v for v in ds_remoto.data_vars if any(v.startswith(b) for b in bases_sel)]
print(f'Variables seleccionadas para descarga ({len(vars_validas)}):', flush=True)

sub = (ds_remoto[vars_validas]
    .sel(lat_0p1=slice(lat_min, lat_max), lon_0p1=slice(lon_min, lon_max),
         lead_time=slice(timedelta64(1, 'h'), timedelta64(360, 'h')))
    .expand_dims('init_time'))

sub['init_time'].encoding['units'] = 'hours since 2026-10-22 00:00:00'
sub['init_time'].encoding['dtype'] = 'int64'

rmtree(ruta_sal, ignore_errors=True)
sub.to_zarr(ruta_sal, mode='w')
make_archive(ruta_zip, 'zip', ruta_sal)
copyfile(f'{ruta_zip}.zip', 'colombia_latest.zip')
rmtree(ruta_sal, ignore_errors=True)

print(f'Recorte exitoso empaquetado en: {ruta_zip}.zip y colombia_latest.zip', flush=True)
