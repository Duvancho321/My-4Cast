"""
00_fetch_cloud_wn3.py — Descarga ligera del recorte de Colombia desde GitHub Release.

__author__: "Duvan Nieves"
__copyright__: "Duvan Nieves Ruiz"
__version__: "0.2.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves.sci@gmail.com"
__status__: "Developer"
__changues__:
    - [2026-11-08][Duvan]: Auto-dispatch de GitHub Actions si GCS tiene corrida mas reciente.
    - [2026-11-03][Duvan]: Ingesta ultraligera desde GitHub Release sin saturar red UNAL.
"""

from sys import exit, path
from pathlib import Path
path.insert(0, str(Path(__file__).resolve().parent.parent))

from numpy import isnan
from shutil import rmtree
from zipfile import ZipFile
from xarray import open_zarr
from json import dumps, loads
from os import getenv, remove
from time import monotonic, sleep
from obstore.store import GCSStore
from zarr.storage import ObjectStore
from os.path import exists, expanduser
from urllib.request import Request, urlopen
from src.descarga import apilar_corrida_zarr
from datetime import datetime, timedelta, timezone

#%% CONFIGURACIÓN DE PARÁMETROS
dir_datos  = getenv('MY4CAST_DATA_DIR', '/mnt/datos/dnieves/WN3')
max_mb_seg = 6.0
tam_bloque = 1024 * 1024
repo_owner = 'Duvancho321'
repo_name  = 'My-4Cast'
tag_rel    = 'colombia-wn3-latest'
ruta_tmp   = f'{dir_datos}/staging/tmp_cloud.zip'
ruta_dir   = f'{dir_datos}/staging/tmp_cloud_extracted.zarr'
ruta_zarr  = f'{dir_datos}/raw/colombia_wn3_full.zarr'
ruta_stage = f'{dir_datos}/staging/tmp_append.zarr'

#%% OBTENCIÓN DE TOKEN DE GITHUB DE ENTORNO O CREDENCIALES LOCALES
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

token_gh = obtener_github_token()
headers  = {'User-Agent': 'My-4Cast-Local'}
if token_gh:
    headers['Authorization'] = f'token {token_gh}'

#%% CONSULTA DE ASSET EN GITHUB API
url_api = f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{tag_rel}'
print(f'Consultando ultimo recorte en: {url_api}', flush=True)

try:
    req_meta = Request(url_api, headers=headers)
    with urlopen(req_meta) as resp:
        data_rel = loads(resp.read().decode())
except Exception as e:
    print(f'Alerta: No se pudo consultar el release en GitHub: {e}', flush=True)
    exit(10)

assets = [a for a in data_rel.get('assets', []) if a.get('name', '').startswith('colombia_part_')]
assets.sort(key=lambda x: x['name'])
if not assets:
    assets = [a for a in data_rel.get('assets', []) if a.get('name') == 'colombia_latest.zip']

if not assets:
    print('No se encontraron partes de recorte en el release.', flush=True)
    exit(10)

tam_total = sum(a.get('size', 0) for a in assets)
if tam_total < 4000000000:
    print(f'Release actual ({tam_total / 1e9:.2f} GB) incompleto (<360h). Esperando recorte completo...', flush=True)
    exit(10)

headers_dl = headers.copy()
if token_gh:
    headers_dl['Accept'] = 'application/octet-stream'

init_cand      = None
run_id_rel     = None
manifest_asset = next((a for a in data_rel.get('assets', []) if a.get('name') == 'manifest.json'), None)
if manifest_asset and exists(ruta_zarr):
    try:
        url_man = manifest_asset['url'] if token_gh else manifest_asset['browser_download_url']
        req_man = Request(url_man, headers=headers_dl)
        with urlopen(req_man) as resp_m:
            man_data = loads(resp_m.read().decode())
        init_cand  = str(man_data.get('init_time'))[:19]
        run_id_rel = man_data.get('run_id')
        ds_loc     = open_zarr(ruta_zarr)
        for idx_l in range(len(ds_loc.init_time) - 1, -1, -1):
            if str(ds_loc.init_time.values[idx_l])[:19] == init_cand:
                muestra = ds_loc['temperature_2m_p50'].isel(init_time=idx_l, lat_0p1=100, lon_0p1=100).values
                if not isnan(muestra).any() and len(muestra) == 360:
                    print(f'Corrida {init_cand} completa (360h) ya se encuentra en el almacén local.', flush=True)
                    if token_gh:
                        ahora = datetime.now(timezone.utc)
                        for dh in [0, 6, 12]:
                            tev  = ahora - timedelta(hours=dh)
                            hc   = '18' if tev.hour >= 18 else ('12' if tev.hour >= 12 else ('06' if tev.hour >= 6 else '00'))
                            rgcs = f"{tev.strftime('%Y%m%d')}_{hc}hr_01_preds"
                            if rgcs == run_id_rel:
                                break
                            try:
                                pfx = f'weathernext_3_0_0_statistics/zarr/2026_to_present/{rgcs}/predictions.zarr'
                                dsg = open_zarr(ObjectStore(GCSStore(bucket='weathernext3_statistics_spatial', prefix=pfx)))
                                vf  = dsg['temperature_2m_p50'].sel(lat_0p1=4.6, lon_0p1=286.0, method='nearest').isel(lead_time=-1).values
                                if not isnan(vf).any():
                                    u_runs = f'https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/crop_colombia.yml/runs?per_page=3'
                                    with urlopen(Request(u_runs, headers=headers)) as rr:
                                        w_runs = loads(rr.read().decode()).get('workflow_runs', [])
                                    if not any(w.get('status') in ('in_progress', 'queued') for w in w_runs):
                                        u_disp = f'https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/crop_colombia.yml/dispatches'
                                        req_d  = Request(u_disp, data=dumps({'ref': 'main', 'inputs': {'run_id': rgcs}}).encode(), headers={**headers, 'Content-Type': 'application/json'}, method='POST')
                                        urlopen(req_d)
                                        print(f'Auto-dispatch enviado a GitHub Actions para nueva corrida en GCS: {rgcs}', flush=True)
                                    break
                            except Exception:
                                continue
                    exit(10)
    except SystemExit:
        raise
    except Exception:
        pass

ya_extraida = False
if exists(ruta_dir) and init_cand:
    try:
        ds_prev = open_zarr(ruta_dir)
        if str(ds_prev.init_time.values[-1])[:19] == init_cand and len(ds_prev.data_vars) >= 90:
            print(f'Usando extracción previa en staging para {init_cand}...', flush=True)
            ya_extraida = True
    except Exception:
        pass

if not ya_extraida:
    if exists(ruta_tmp):
        remove(ruta_tmp)

    #%% DESCARGA Y ENSAMBLADO DE PARTES
    with open(ruta_tmp, 'wb') as f_out:
        for a in assets:
            print(f"Descargando parte {a['name']} ({a['size'] / 1e6:.1f} MB, máx {max_mb_seg} MB/s)...", flush=True)
            url_dl   = a['url'] if token_gh else a['browser_download_url']
            tam_esp  = a['size']
            recibido = 0
            while recibido < tam_esp:
                hdrs_r = {**headers_dl, 'Range': f'bytes={recibido}-'} if recibido > 0 else headers_dl
                with urlopen(Request(url_dl, headers=hdrs_r), timeout=120) as resp:
                    while True:
                        t_ini = monotonic()
                        chunk = resp.read(tam_bloque)
                        if not chunk:
                            break
                        f_out.write(chunk)
                        recibido += len(chunk)
                        t_esp = (len(chunk) / (max_mb_seg * 1024 * 1024)) - (monotonic() - t_ini)
                        if t_esp > 0:
                            sleep(t_esp)

    print('Descarga y ensamblado completados. Extrayendo...', flush=True)
    rmtree(ruta_dir, ignore_errors=True)
    with ZipFile(ruta_tmp, 'r') as zf:
        zf.extractall(ruta_dir)

#%% APILADO EN ALMACÉN LOCAL
ds_nueva  = open_zarr(ruta_dir)
init_time = ds_nueva.init_time.values[-1]
print(f'Integrando corrida {init_time} al Zarr local...', flush=True)

apilar_corrida_zarr(ds_nueva, ruta_zarr)
rmtree(ruta_dir, ignore_errors=True)
rmtree(ruta_stage, ignore_errors=True)
if exists(ruta_tmp):
    remove(ruta_tmp)

print('Integracion exitosa completada.', flush=True)
