"""
cloud_crop_colombia.py — Extracción y recorte de WeatherNext 3 para Colombia en GitHub Actions.

__author__: "Duvan Nieves"
__copyright__: "Duvan Nieves Ruiz"
__version__: "0.2.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves.sci@gmail.com"
__status__: "Developer"
__changues__:
    - [2026-11-08][Duvan]: Incorporacion de station heads de 5 km (t2m y d2m).
    - [2026-11-03][Duvan]: Worker de recorte para 15 variables fisicas seleccionadas.
"""

from os import getenv, link
from sys import argv, exit
from os.path import exists
from json import dump, loads
from xarray import open_zarr
from obstore.store import GCSStore
from shutil import make_archive, rmtree
from zarr.storage import ObjectStore
from numpy import isnan, timedelta64
from urllib.request import Request, urlopen
from datetime import datetime, timedelta, timezone

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
    'station_head_temperature_2m',
    'station_head_dewpoint_temperature_2m',
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
            ds      = open_zarr(ObjectStore(GCSStore(bucket=bucket_wn3, prefix=pfx)))
            val_fin = ds['temperature_2m_p50'].sel(lat_0p1=4.6, lon_0p1=286.0, method='nearest').isel(lead_time=-1).values
            if isnan(val_fin).any():
                print(f'Corrida {r_id} aun incompleta en GCS (360h NaN), evaluando ciclo previo...', flush=True)
                continue
            return r_id, ds
        except Exception:
            continue
    raise RuntimeError('No se encontro ninguna corrida reciente disponible en GCS.')

if __name__ == '__main__':
    run_id, ds_remoto = obtener_dataset_disponible()

    # Comprobación de idempotencia: Si ya está publicada en colombia-wn3-latest, salir
    if len(argv) <= 1 or argv[1] == 'auto':
        gh_tok  = getenv('PRIVATE_REPO_TOKEN') or getenv('GITHUB_TOKEN')
        hdrs_gh = {'Authorization': f'token {gh_tok}'} if gh_tok else {'User-Agent': 'My-4Cast'}
        url_chk = 'https://api.github.com/repos/Duvancho321/My-4Cast-Private/releases/tags/colombia-wn3-latest'
        try:
            req_chk = Request(url_chk, headers=hdrs_gh)
            with urlopen(req_chk) as resp_c:
                rel_c = loads(resp_c.read().decode())
            tam_rel = sum(a.get('size', 0) for a in rel_c.get('assets', []) if a.get('name', '').startswith('colombia_part_'))
            if (run_id in rel_c.get('name', '') or run_id in rel_c.get('body', '')) and tam_rel > 4000000000:
                print(f'Corrida {run_id} completa ({tam_rel / 1e9:.2f} GB) ya se encuentra publicada en colombia-wn3-latest. Se omite re-procesamiento.', flush=True)
                exit(0)
        except Exception:
            pass

    modo      = argv[2] if len(argv) > 2 else 'all'
    bases_uso = ['station_head_temperature_2m', 'station_head_dewpoint_temperature_2m'] if modo == '5km' else bases_sel
    ruta_sal  = f'colombia_{run_id}.zarr'
    ruta_zip  = f'colombia_{run_id}'
    
    print(f'Procesando corrida: {run_id} (modo={modo})', flush=True)
    vars_validas = [v for v in ds_remoto.data_vars if any(v.startswith(b) for b in bases_uso)]
    print(f'Campos seleccionados para descarga ({len(vars_validas)}):', flush=True)
    
    sel_kw = {'lat_0p05': slice(lat_min, lat_max), 'lon_0p05': slice(lon_min, lon_max), 'lead_time': slice(timedelta64(1, 'h'), timedelta64(360, 'h'))}
    if modo != '5km':
        sel_kw['lat_0p1'] = slice(lat_min, lat_max)
        sel_kw['lon_0p1'] = slice(lon_min, lon_max)
    sub = ds_remoto[vars_validas].sel(**sel_kw).expand_dims('init_time')
    
    sub['init_time'].encoding['units'] = 'hours since 2026-10-22 00:00:00'
    sub['init_time'].encoding['dtype'] = 'int64'
    
    rmtree(ruta_sal, ignore_errors=True)
    sub.to_zarr(ruta_sal, mode='w')
    make_archive(ruta_zip, 'zip', ruta_sal)
    rmtree(ruta_sal, ignore_errors=True)
    try:
        link(f'{ruta_zip}.zip', 'colombia_latest.zip')
    except Exception:
        pass
    
    init_val = str(sub.init_time.values[0])
    with open('manifest.json', 'w') as fm:
        dump({'run_id': run_id, 'init_time': init_val, 'mode': modo}, fm)
    
    print(f'Recorte exitoso empaquetado en: {ruta_zip}.zip y colombia_latest.zip', flush=True)
