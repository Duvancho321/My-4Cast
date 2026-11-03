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
from datetime import datetime, timedelta, timezone
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
def obtener_dataset_disponible():
    if len(argv) > 1 and argv[1] != 'auto':
        r_id = argv[1]
        pfx  = f'weathernext_3_0_0_statistics/zarr/2026_to_present/{r_id}/predictions.zarr'
        return r_id, open_zarr(ObjectStore(GCSStore(bucket=bucket_wn3, prefix=pfx)))
    
    ahora = datetime.now(timezone.utc)
    for delta_h in [0, 6, 12, 18, 24]:
        t_eval = ahora - timedelta(hours=delta_h)
        h_int  = t_eval.hour
        h_corr = '18' if h_int >= 18 else ('12' if h_int >= 12 else ('06' if h_int >= 6 else '00'))
        f_str  = t_eval.strftime('%Y%m%d')
        r_id   = f'{f_str}_{h_corr}hr_01_preds'
        pfx    = f'weathernext_3_0_0_statistics/zarr/2026_to_present/{r_id}/predictions.zarr'
        try:
            ds = open_zarr(ObjectStore(GCSStore(bucket=bucket_wn3, prefix=pfx)))
            return r_id, ds
        except Exception:
            continue
    raise RuntimeError('No se encontro ninguna corrida reciente disponible en GCS.')

if __name__ == '__main__':
    run_id, ds_remoto = obtener_dataset_disponible()
    ruta_sal          = f'colombia_{run_id}.zarr'
    ruta_zip          = f'colombia_{run_id}'
    
    print(f'Procesando corrida: {run_id}', flush=True)
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
