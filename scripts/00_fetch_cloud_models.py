"""
00_fetch_cloud_models.py — Descarga efímera y con control de ancho de banda de modelos alternativos desde GitHub Release.

__author__: "Duvan Nieves"
__copyright__: "Duvan Nieves Ruiz"
__version__: "0.2.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves.sci@gmail.com"
__status__: "Developer"
__changues__:
    - [2026-11-05][Duvan]: Limitador explícito de ancho de banda para proteger la red UNAL y almacenamiento efímero.
"""

from sys import argv, exit
from shutil import rmtree
from requests import get
from zipfile import ZipFile
from json import dump, loads
from xarray import open_zarr
from time import monotonic, sleep
from os import getenv, makedirs, remove
from os.path import exists, expanduser

#%% CONFIGURACIÓN DE PARÁMETROS
dir_datos  = getenv('MY4CAST_DATA_DIR', '/mnt/datos/dnieves/WN3')
max_mb_seg = 4.0
tam_bloque = 1024 * 1024
repo_owner = 'Duvancho321'
repo_name  = 'My-4Cast'
tag_rel    = 'colombia-models-latest'
dir_models = f'{dir_datos}/staging/models'
filtro     = argv[1] if len(argv) > 1 else 'all'
makedirs(dir_models, exist_ok=True)

#%% OBTENCIÓN DE CREDENCIALES DE GITHUB
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

#%% CONSULTA DE RELEASE MULTIMODELO EN GITHUB (CON RESPALDO DE ARTIFACTS)
url_api   = f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{tag_rel}'
print(f'Consultando recortes multimodelo efímeros en: {url_api}', flush=True)
data_rel  = None
modo_art  = False

r_meta = get(url_api, headers=headers, timeout=20)
if r_meta.status_code == 200:
    data_rel = r_meta.json()
else:
    print(f'Aviso: Release {tag_rel} no publicado aún (HTTP {r_meta.status_code}); consultando artifacts de la última corrida de GitHub Actions...', flush=True)
    modo_art = True

if modo_art:
    url_runs = f'https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/crop_multimodel_colombia.yml/runs?per_page=3'
    runs = get(url_runs, headers=headers, timeout=20).json().get('workflow_runs', [])
    arts_all = []
    for run in runs:
        arts = get(run['artifacts_url'], headers=headers, timeout=20).json().get('artifacts', [])
        if arts:
            arts_all = arts
            print(f'  Usando {len(arts_all)} artifacts de la corrida #{run["id"]} ({run["created_at"]})', flush=True)
            break
    if not arts_all:
        print('No se encontraron artifacts disponibles.', flush=True)
        exit(10)

    actualizados = 0
    manifest_acum = {'updated_utc': '', 'models': {}}
    for art in arts_all:
        if not art['name'].startswith('crop-'):
            continue
        m_id = art['name'].replace('crop-', '')
        if filtro != 'all' and m_id not in filtro.split(','):
            continue
        ruta_art_zip = f'{dir_models}/art_{m_id}.zip'
        ruta_ext_dir = f'{dir_models}/ext_{m_id}'
        ruta_zarr    = f'{dir_models}/{m_id}.zarr'
        print(f'  - [{m_id}] Descargando artifact {art["name"]} ({art["size_in_bytes"]/1e6:.2f} MB, máx {max_mb_seg} MB/s)...', flush=True)
        with get(art['archive_download_url'], headers=headers, stream=True, timeout=90) as resp_a:
            resp_a.raise_for_status()
            with open(ruta_art_zip, 'wb') as f_out:
                for chunk in resp_a.iter_content(chunk_size=tam_bloque):
                    t_ini = monotonic()
                    if not chunk:
                        continue
                    f_out.write(chunk)
                    t_esp = (len(chunk) / (max_mb_seg * 1024 * 1024)) - (monotonic() - t_ini)
                    if t_esp > 0:
                        sleep(t_esp)
        rmtree(ruta_ext_dir, ignore_errors=True)
        with ZipFile(ruta_art_zip, 'r') as zf:
            zf.extractall(ruta_ext_dir)
        remove(ruta_art_zip)

        man_file = f'{ruta_ext_dir}/manifest_{m_id}.json'
        if exists(man_file):
            m_data = loads(open(man_file, encoding='utf-8').read())
            manifest_acum['updated_utc'] = m_data.get('updated_utc', manifest_acum['updated_utc'])
            manifest_acum['models'].update(m_data.get('models', {}))

        inner_zip = f'{ruta_ext_dir}/colombia_{m_id}.zip'
        if exists(inner_zip):
            rmtree(ruta_zarr, ignore_errors=True)
            with ZipFile(inner_zip, 'r') as zf_in:
                zf_in.extractall(ruta_zarr)
            actualizados += 1
            print(f'  [✓ {m_id}] Actualizado en {ruta_zarr} (efímero, corrida única).', flush=True)
        rmtree(ruta_ext_dir, ignore_errors=True)
        sleep(1.0)

    with open(f'{dir_models}/models_manifest.json', 'w', encoding='utf-8') as fm:
        dump(manifest_acum, fm, indent=2, ensure_ascii=False)
    print(f'Se actualizaron {actualizados} modelos efímeros exitosamente sin saturar la red.', flush=True)
    exit(0 if actualizados > 0 else 10)

headers_dl = headers.copy()
if token_gh:
    headers_dl['Accept'] = 'application/octet-stream'

assets_map = {a['name']: a for a in data_rel.get('assets', [])}
if 'models_manifest.json' not in assets_map:
    print('No se encontró models_manifest.json en el release.', flush=True)
    exit(10)

url_man = assets_map['models_manifest.json']['url'] if token_gh else assets_map['models_manifest.json']['browser_download_url']
manifest = get(url_man, headers=headers_dl, timeout=20).json()

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
    with get(url_dl, headers=headers_dl, stream=True, timeout=60) as resp_z:
        resp_z.raise_for_status()
        with open(ruta_zip, 'wb') as f_out:
            for chunk in resp_z.iter_content(chunk_size=tam_bloque):
                t_ini = monotonic()
                if not chunk:
                    continue
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
