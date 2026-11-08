"""
00_backfill_cloud.py — Descarga e integración del backfill de noviembre (10 km y 5 km) desde GitHub Releases.

__author__: "Duvan Nieves"
__copyright__: "Duvan Nieves Ruiz"
__version__: "0.2.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves.sci@gmail.com"
__status__: "Developer"
__changues__:
    - [2026-11-08][Duvan]: Backfill dual (10 km + 5 km) para todo noviembre.
    - [2026-11-03][Duvan]: Backfill incremental y ordenado para noviembre 2026.
"""

from sys import path
from pathlib import Path
path.insert(0, str(Path(__file__).resolve().parent.parent))

from json import loads
from shutil import rmtree
from zipfile import ZipFile
from xarray import open_zarr
from time import monotonic, sleep
from os import getenv, remove
from pandas import date_range
from numpy import datetime64, isnan, where
from os.path import exists, expanduser
from urllib.request import Request, urlopen
from src.descarga import apilar_corrida_zarr

#%% CONFIGURACIÓN DE PARÁMETROS
dir_datos   = getenv('MY4CAST_DATA_DIR', '/mnt/datos/dnieves/WN3')
repo_owner  = 'Duvancho321'
repo_name   = 'My-4Cast'
ruta_tmp    = f'{dir_datos}/staging/tmp_backfill.zip'
ruta_dir    = f'{dir_datos}/staging/tmp_backfill_extracted.zarr'
ruta_zarr   = f'{dir_datos}/raw/colombia_wn3_full.zarr'
max_bps     = 6 * 1024 * 1024
fechas_nov  = date_range('2026-11-01 00:00', '2026-11-08 00:00', freq='6h')

#%% OBTENCIÓN DE TOKEN DE GITHUB
def obtener_github_token():
    tok = getenv('GITHUB_TOKEN')
    if tok:
        return tok
    try:
        with open(expanduser('~/.git-credentials')) as f:
            for linea in f:
                if 'github.com' in linea:
                    return linea.split('//')[1].split('@')[0].split(':')[1]
    except Exception:
        pass
    return None

token_gh   = obtener_github_token()
headers    = {'User-Agent': 'My-4Cast-Backfill'}
if token_gh:
    headers['Authorization'] = f'token {token_gh}'
headers_dl = {**headers, 'Accept': 'application/octet-stream'} if token_gh else headers

#%% BUCLE DE INTEGRACIÓN HASTA COMPLETAR NOVIEMBRE (10 KM + 5 KM)
for intento in range(1, 40):
    ds_loc     = open_zarr(ruta_zarr)
    pendientes = []
    for dt in fechas_nov:
        run_id = f'{dt:%Y%m%d_%H}hr_01_preds'
        t_val  = datetime64(dt.to_datetime64())
        idxs   = where(ds_loc.init_time.values == t_val)[0]
        if len(idxs) == 0:
            pendientes.append((run_id, 'all'))
            continue
        idx = int(idxs[0])
        n10 = int(isnan(ds_loc['total_precipitation_1hr_mean'].isel(init_time=idx, lat_0p1=100, lon_0p1=100).values).sum())
        n5  = int(isnan(ds_loc['station_head_temperature_2m_mean'].isel(init_time=idx, lat_0p05=200, lon_0p05=200).values).sum())
        if n10 > 0:
            pendientes.append((run_id, 'all'))
        elif n5 > 0:
            pendientes.append((run_id, '5km'))

    print(f'\n[Ciclo {intento}] Corridas pendientes en noviembre: {len(pendientes)}', flush=True)
    if not pendientes:
        print('Todo noviembre (10 km y 5 km) está 100% completo en el Zarr local.', flush=True)
        break

    progreso = 0
    for run_id, modo in pendientes:
        tag_rel = f'colombia-5km-{run_id}' if modo == '5km' else f'colombia-{run_id}'
        url_api = f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{tag_rel}'
        try:
            with urlopen(Request(url_api, headers=headers), timeout=30) as resp:
                data_rel = loads(resp.read().decode())
        except Exception:
            continue

        assets = sorted(
            [a for a in data_rel.get('assets', []) if a.get('name', '').startswith('colombia_part_')],
            key=lambda x: x['name']
        )
        if not assets or not any(a.get('name') == 'manifest.json' for a in data_rel.get('assets', [])):
            continue

        print(f'Descargando {tag_rel} ({len(assets)} partes, modo={modo})...', flush=True)
        if exists(ruta_tmp):
            remove(ruta_tmp)

        t_ini    = monotonic()
        desc_b   = 0
        with open(ruta_tmp, 'wb') as f_out:
            for a in assets:
                url_dl = a['url'] if token_gh else a['browser_download_url']
                with urlopen(Request(url_dl, headers=headers_dl), timeout=120) as resp:
                    while True:
                        chunk = resp.read(2 * 1024 * 1024)
                        if not chunk:
                            break
                        f_out.write(chunk)
                        desc_b += len(chunk)
                        t_esp   = (desc_b / max_bps) - (monotonic() - t_ini)
                        if t_esp > 0:
                            sleep(t_esp)

        rmtree(ruta_dir, ignore_errors=True)
        with ZipFile(ruta_tmp, 'r') as zf:
            zf.extractall(ruta_dir)

        ds_nueva = open_zarr(ruta_dir)
        print(f'Integrando {tag_rel} ({str(ds_nueva.init_time.values[0])[:19]}) en Zarr local...', flush=True)
        apilar_corrida_zarr(ds_nueva, ruta_zarr)
        rmtree(ruta_dir, ignore_errors=True)
        if exists(ruta_tmp):
            remove(ruta_tmp)
        progreso += 1
        print(f'Integrada {tag_rel} exitosamente.', flush=True)

    if len(pendientes) - progreso > 0:
        print(f'Esperando 90 s por corridas en curso en GitHub Actions ({len(pendientes) - progreso} restantes)...', flush=True)
        sleep(90)
