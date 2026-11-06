"""
03_upload_drive.py — Sincronización automática de animaciones operativas hacia Google Drive con estructura actual e histórico para todas las fuentes.

__author__: "Duvan Nieves"
__copyright__: "Duvan Nieves Ruiz"
__version__: "0.4.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves.sci@gmail.com"
__status__: "Developer"
__changues__:
    - [2026-11-05][Duvan]: Estructura dual actual/ e historico/<fecha_tag>/ para las 11 fuentes en Drive (datos crudos efímeros, animaciones preservadas).
    - [2026-11-05][Duvan]: Creación de una carpeta independiente en Drive por cada una de las 11 fuentes.
"""

from sys import argv, path
from pathlib import Path
path.insert(0, str(Path(__file__).resolve().parent.parent))

from os import getenv
from glob import glob
from xarray import open_zarr
from numpy import timedelta64
from os.path import basename, exists
from src.modelos import modelos_colombia
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

#%% PARÁMETROS Y CONSTANTES
FOLDER_ROOT_ID = getenv('DRIVE_FOLDER_ID', '1zsEhI-CnExH7RGM0qi-y1zTGPj9pAF45')
TOKEN_FILE     = getenv('DRIVE_TOKEN_FILE', str(Path(__file__).resolve().parent.parent / 'token_drive.json'))
SCOPES         = ['https://www.googleapis.com/auth/drive']

def obtener_servicio_drive():
    creds = None
    if exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        else:
            raise RuntimeError(f'Token no válido o no encontrado en {TOKEN_FILE}. Ejecuta scripts/auth_drive.py primero.')
    return build('drive', 'v3', credentials=creds)

def obtener_o_crear_carpeta(service, nombre, parent_id):
    query = f"'{parent_id}' in parents and name = '{nombre}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    res   = service.files().list(
        q=query,
        fields='files(id, name)',
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    files = res.get('files', [])
    if files:
        return files[0]['id']
    meta = {
        'name': nombre,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    carpeta = service.files().create(body=meta, fields='id', supportsAllDrives=True).execute()
    return carpeta.get('id')

def limpiar_archivos_raiz_fuente(service, id_fuente):
    query = f"'{id_fuente}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
    res   = service.files().list(
        q=query,
        fields='files(id, name)',
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    for f in res.get('files', []):
        service.files().delete(fileId=f['id'], supportsAllDrives=True).execute()
        print(f"    [✕ Limpieza raíz] {f['name']}", flush=True)

def subir_o_actualizar_archivo(service, ruta_local, parent_id, nombre_destino):
    media = MediaFileUpload(ruta_local, mimetype='video/mp4', resumable=True)
    query = f"'{parent_id}' in parents and name = '{nombre_destino}' and trashed = false"
    res   = service.files().list(
        q=query,
        fields='files(id, name)',
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    files = res.get('files', [])

    if files:
        file_id     = files[0]['id']
        actualizado = service.files().update(
            fileId=file_id,
            media_body=media,
            fields='id, name, size',
            supportsAllDrives=True
        ).execute()
        print(f"    [✓ Actualizado] {nombre_destino} ({int(actualizado.get('size', 0)) / 1e6:.1f} MB)", flush=True)
        return actualizado.get('id')

    meta   = {'name': nombre_destino, 'parents': [parent_id]}
    creado = service.files().create(
        body=meta,
        media_body=media,
        fields='id, name, size',
        supportsAllDrives=True
    ).execute()
    print(f"    [✓ Subido] {nombre_destino} ({int(creado.get('size', 0)) / 1e6:.1f} MB)", flush=True)
    return creado.get('id')

#%% SINCRONIZACIÓN CON CARPETA EXCLUSIVA POR CADA FUENTE EN DRIVE
if __name__ == '__main__':
    objetivo = argv[1] if len(argv) > 1 else 'all'
    print('==========================================================', flush=True)
    print('Sincronización Multimodelo a Google Drive (11 Fuentes)', flush=True)
    print('==========================================================', flush=True)

    service = obtener_servicio_drive()

    for m_id, cfg in modelos_colombia.items():
        if objetivo != 'all' and m_id not in objetivo.split(','):
            continue

        # Garantizar que exista la carpeta exclusiva de cada fuente en la raíz de 01_Animaciones
        id_fuente = obtener_o_crear_carpeta(service, cfg['carpeta'], FOLDER_ROOT_ID)
        print(f"\n[{cfg['carpeta']}] {cfg['etiqueta_fuente']} -> Carpeta Drive verificada ({id_fuente})", flush=True)

        if not exists(cfg['ruta_zarr']) or not exists(cfg['dir_anim']):
            continue

        videos = [v for v in sorted(glob(f"{cfg['dir_anim']}/{m_id}_animacion_*.mp4")) if not v.endswith('_master.mp4')]
        if not videos:
            continue

        ds        = open_zarr(cfg['ruta_zarr'])
        init_utc  = ds.init_time.values[-1]
        init_hl   = init_utc - timedelta64(5, 'h')
        fecha_tag = str(init_hl)[:10].replace('-', '') + f"_{str(init_hl)[11:13]}HL"
        print(f"  Corrida activa: {fecha_tag} ({len(videos)} videos)", flush=True)

        # Depurar archivos sueltos en raíz de la carpeta de la fuente
        limpiar_archivos_raiz_fuente(service, id_fuente)

        # Estructura dual: actual/ (última corrida) e historico/<fecha_tag>/ (registro temporal inmutable)
        id_actual = obtener_o_crear_carpeta(service, 'actual', id_fuente)
        id_hist   = obtener_o_crear_carpeta(service, 'historico', id_fuente)
        id_corr   = obtener_o_crear_carpeta(service, fecha_tag, id_hist)

        for v in videos:
            nom_limpio = basename(v).replace('_whatsapp', '')
            subir_o_actualizar_archivo(service, v, id_actual, nom_limpio)
            subir_o_actualizar_archivo(service, v, id_corr, f'{fecha_tag}_{nom_limpio}')

    print('\n✓ Sincronización multimodelo a Google Drive finalizada.', flush=True)
