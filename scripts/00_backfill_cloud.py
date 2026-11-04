"""
00_backfill_cloud.py — Descarga e integración secuencial del backfill de Colombia desde GitHub Releases.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.1.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-11-03][Duvan]: Backfill incremental y ordenado para noviembre 2026.
"""

from sys import exit, path
path.insert(0, '/home/dnieves/Documentos/My-4Cast')

from os import remove
from json import loads
from shutil import rmtree
from os.path import exists
from zipfile import ZipFile
from urllib.request import Request, urlopen
from xarray import open_zarr
from src.descarga import apilar_corrida_zarr

#%% CONFIGURACIÓN DE PARÁMETROS
repo_owner = 'Duvancho321'
repo_name  = 'My-4Cast'
ruta_tmp   = '/mnt/datos/dnieves/WN3/staging/tmp_backfill.zip'
ruta_dir   = '/mnt/datos/dnieves/WN3/staging/tmp_backfill_extracted.zarr'
ruta_zarr  = '/mnt/datos/dnieves/WN3/raw/colombia_wn3_full.zarr'
ruta_stage = '/mnt/datos/dnieves/WN3/staging/tmp_append.zarr'

runs_nov   = [
    '20261101_00hr_01_preds',
    '20261101_06hr_01_preds',
    '20261101_12hr_01_preds',
    '20261101_18hr_01_preds',
    '20261102_00hr_01_preds',
    '20261102_06hr_01_preds',
    '20261102_12hr_01_preds',
    '20261102_18hr_01_preds',
    '20261103_00hr_01_preds',
    '20261103_06hr_01_preds',
    '20261103_12hr_01_preds',
]

#%% OBTENCIÓN DE TOKEN DE GITHUB DE CREDENCIALES LOCALES
def obtener_github_token():
    try:
        with open('/home/dnieves/.git-credentials') as f:
            for linea in f:
                if 'github.com' in linea:
                    return linea.split('//')[1].split('@')[0].split(':')[1]
    except Exception:
        pass
    return None

token_gh = obtener_github_token()
headers  = {'User-Agent': 'My-4Cast-Backfill'}
if token_gh:
    headers['Authorization'] = f'token {token_gh}'

#%% PROCESAMIENTO SECUENCIAL DE CORRIDAS
for run_id in runs_nov:
    tag_rel = f'colombia-{run_id}'
    url_api = f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{tag_rel}'
    print(f'\n=== Consultando corrida {run_id} ({tag_rel}) ===', flush=True)

    try:
        req_meta = Request(url_api, headers=headers)
        with urlopen(req_meta) as resp:
            data_rel = loads(resp.read().decode())
    except Exception:
        url_api = f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/colombia-wn3-latest'
        try:
            req_meta = Request(url_api, headers=headers)
            with urlopen(req_meta) as resp:
                data_rel = loads(resp.read().decode())
        except Exception as e:
            print(f'Release {tag_rel} aun no disponible: {e}', flush=True)
            continue

    assets = [a for a in data_rel.get('assets', []) if a.get('name', '').startswith('colombia_part_')]
    assets.sort(key=lambda x: x['name'])
    if not assets:
        assets = [a for a in data_rel.get('assets', []) if a.get('name') == 'colombia_latest.zip']

    if not assets:
        print(f'No hay archivos recortados en el release {tag_rel}. Omitiendo.', flush=True)
        continue

    # Verificar si la corrida ya está integrada localmente
    manifest_asset = next((a for a in data_rel.get('assets', []) if a.get('name') == 'manifest.json'), None)
    if manifest_asset and exists(ruta_zarr):
        try:
            url_man = manifest_asset['url'] if token_gh else manifest_asset['browser_download_url']
            req_man = Request(url_man, headers=headers)
            with urlopen(req_man) as resp_m:
                man_data = loads(resp_m.read().decode())
            init_cand = man_data.get('init_time')
            ds_loc    = open_zarr(ruta_zarr)
            if str(init_cand) in [str(t) for t in ds_loc.init_time.values]:
                print(f'Corrida {init_cand} ya existe en el Zarr local. Omitiendo descarga.', flush=True)
                continue
        except Exception:
            pass

    if exists(ruta_tmp):
        remove(ruta_tmp)

    headers_dl = headers.copy()
    if token_gh:
        headers_dl['Accept'] = 'application/octet-stream'

    print(f'Descargando {len(assets)} partes para {run_id}...', flush=True)
    with open(ruta_tmp, 'wb') as f_out:
        for a in assets:
            url_dl = a['url'] if token_gh else a['browser_download_url']
            req_dl = Request(url_dl, headers=headers_dl)
            with urlopen(req_dl) as resp:
                while True:
                    chunk = resp.read(16 * 1024 * 1024)
                    if not chunk:
                        break
                    f_out.write(chunk)

    print('Extrayendo zarr temporal...', flush=True)
    rmtree(ruta_dir, ignore_errors=True)
    with ZipFile(ruta_tmp, 'r') as zf:
        zf.extractall(ruta_dir)

    ds_nueva  = open_zarr(ruta_dir)
    init_time = ds_nueva.init_time.values[-1]
    print(f'Integrando corrida {init_time} al Zarr definitivo...', flush=True)

    apilar_corrida_zarr(ds_nueva, ruta_zarr, ruta_stage)
    rmtree(ruta_dir, ignore_errors=True)
    if exists(ruta_tmp):
        remove(ruta_tmp)

    print(f'Corrida {run_id} integrada exitosamente.', flush=True)

print('\nProceso de backfill finalizado.', flush=True)
