"""
00_fetch_cloud_models.py — Descarga efímera y con control de ancho de banda de modelos alternativos desde GitHub Release.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.2.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-11-05][Duvan]: Limitador explícito de ancho de banda para proteger la red UNAL y almacenamiento efímero.
"""

from sys import argv, exit
from shutil import rmtree
from os.path import exists
from zipfile import ZipFile
from json import dump, loads
from xarray import open_zarr
from time import monotonic, sleep
from os import makedirs, remove
from urllib.request import Request, urlopen

#%% CONFIGURACIÓN DE PARÁMETROS Y LÍMITE DE RED UNAL
max_mb_seg = 4.0
tam_bloque = 1024 * 1024
repo_owner = 'Duvancho321'
repo_name  = 'My-4Cast'
tag_rel    = 'colombia-models-latest'
dir_models = '/mnt/datos/dnieves/WN3/staging/models'
filtro     = argv[1] if len(argv) > 1 else 'all'
makedirs(dir_models, exist_ok=True)

#%% OBTENCIÓN DE CREDENCIALES LOCALES DE GITHUB
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

#%% CONSULTA DE RELEASE MULTIMODELO EN GITHUB
url_api = f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{tag_rel}'
print(f'Consultando recortes multimodelo efímeros en: {url_api}', flush=True)

try:
    req_meta = Request(url_api, headers=headers)
    with urlopen(req_meta, timeout=20) as resp:
        data_rel = loads(resp.read().decode())
except Exception as e:
    print(f'Aviso: Release {tag_rel} aún no disponible en GitHub: {e}', flush=True)
    exit(10)

headers_dl = headers.copy()
if token_gh:
    headers_dl['Accept'] = 'application/octet-stream'

assets_map = {a['name']: a for a in data_rel.get('assets', [])}
if 'models_manifest.json' not in assets_map:
    print('No se encontró models_manifest.json en el release.', flush=True)
    exit(10)

url_man = assets_map['models_manifest.json']['url'] if token_gh else assets_map['models_manifest.json']['browser_download_url']
with urlopen(Request(url_man, headers=headers_dl), timeout=20) as resp_m:
    manifest = loads(resp_m.read().decode())

with open(f'{dir_models}/models_manifest.json', 'w', encoding='utf-8') as fm:
    dump(manifest, fm, indent=2, ensure_ascii=False)

#%% DESCARGA SECUENCIAL REGULADA (PROTECCIÓN DE RED UNAL + ALMACENAMIENTO EFÍMERO)
actualizados = 0
for m_id, info_m in manifest.get('models', {}).items():
    if filtro != 'all' and m_id not in filtro.split(','):
        continue
    zip_name  = info_m.get('zip', f'colombia_{m_id}.zip')
    init_cand = str(info_m.get('init_time', ''))[:19]
    ruta_zarr = f'{dir_models}/{m_id}.zarr'
    ruta_zip  = f'{dir_models}/tmp_{m_id}.zip'

    if zip_name not in assets_map:
        continue

    if exists(ruta_zarr):
        try:
            ds_loc   = open_zarr(ruta_zarr)
            init_loc = str(ds_loc.init_time.values[-1])[:19]
            if init_loc == init_cand:
                print(f'  - [{m_id}] Corrida {init_cand} ya activa en staging efímero. Omitiendo.', flush=True)
                continue
        except Exception:
            pass

    asset  = assets_map[zip_name]
    url_dl = asset['url'] if token_gh else asset['browser_download_url']
    print(f'  - [{m_id}] Descargando {zip_name} ({asset["size"] / 1e6:.2f} MB, máx {max_mb_seg} MB/s)...', flush=True)
    with open(ruta_zip, 'wb') as f_out:
        with urlopen(Request(url_dl, headers=headers_dl), timeout=60) as resp_z:
            while True:
                t_ini = monotonic()
                chunk = resp_z.read(tam_bloque)
                if not chunk:
                    break
                f_out.write(chunk)
                t_esp = (len(chunk) / (max_mb_seg * 1024 * 1024)) - (monotonic() - t_ini)
                if t_esp > 0:
                    sleep(t_esp)

    rmtree(ruta_zarr, ignore_errors=True)
    with ZipFile(ruta_zip, 'r') as zf:
        zf.extractall(ruta_zarr)
    remove(ruta_zip)
    actualizados += 1
    print(f'  [✓ {m_id}] Actualizado en {ruta_zarr} (efímero, corrida única).', flush=True)
    sleep(1.0)

if actualizados == 0:
    print('Todos los modelos efímeros están al día.', flush=True)
    exit(10)

print(f'Se actualizaron {actualizados} modelos efímeros exitosamente sin saturar la red.', flush=True)
