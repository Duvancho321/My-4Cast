"""
00_fetch_cloud_wn3.py — Descarga ligera del recorte de Colombia desde GitHub Release.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.1.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-11-03][Duvan]: Ingesta ultraligera desde GitHub Release sin saturar red UNAL.
"""

from sys import exit, path
path.insert(0, '/home/dnieves/Documentos/My-4Cast')

from shutil import rmtree
from os.path import exists
from zipfile import ZipFile
from json import loads
from urllib.request import Request, urlopen
from xarray import open_zarr
from src.descarga import apilar_corrida_zarr

#%% CONFIGURACIÓN DE PARÁMETROS
repo_owner = 'Duvancho321'
repo_name  = 'My-4Cast'
tag_rel    = 'colombia-wn3-latest'
ruta_tmp   = '/mnt/datos/dnieves/WN3/staging/tmp_cloud.zip'
ruta_dir   = '/mnt/datos/dnieves/WN3/staging/tmp_cloud_extracted.zarr'
ruta_zarr  = '/mnt/datos/dnieves/WN3/raw/colombia_wn3_full.zarr'
ruta_stage = '/mnt/datos/dnieves/WN3/staging/tmp_append.zarr'

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

asset_zip = None
for a in data_rel.get('assets', []):
    if a.get('name') == 'colombia_latest.zip':
        asset_zip = a
        break

if not asset_zip:
    print('No se encontro el archivo colombia_latest.zip en el release.', flush=True)
    exit(10)

url_descarga = asset_zip['url'] if token_gh else asset_zip['browser_download_url']
if token_gh:
    headers['Accept'] = 'application/octet-stream'

#%% DESCARGA DEL RECORTE (140 MB)
print(f"Descargando recorte {asset_zip['name']} ({asset_zip['size'] / 1e6:.1f} MB)...", flush=True)
req_data = Request(url_descarga, headers=headers)
with urlopen(req_data) as resp, open(ruta_tmp, 'wb') as f_out:
    f_out.write(resp.read())

print('Descarga completada en 1 segundo. Extrayendo...', flush=True)
rmtree(ruta_dir, ignore_errors=True)
with ZipFile(ruta_tmp, 'r') as zf:
    zf.extractall(ruta_dir)

#%% APILADO EN ALMACÉN LOCAL
ds_nueva  = open_zarr(ruta_dir)
init_time = ds_nueva.init_time.values[-1]
print(f'Integrando corrida {init_time} al Zarr local...', flush=True)

apilar_corrida_zarr(ds_nueva, ruta_zarr, ruta_stage)
rmtree(ruta_dir, ignore_errors=True)
if exists(ruta_tmp):
    rmtree(ruta_tmp, ignore_errors=True) if exists(ruta_tmp) and not exists(ruta_tmp) else None

print('Integracion exitosa completada.', flush=True)
