"""
03_upload_drive.py — Sincronización automática de animaciones operativas hacia Google Drive con separación estricta entre WN3 (histórico) y otras fuentes (efímeras).

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.2.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-11-05][Duvan]: Estructura separada WN3/ (actual + historico) vs OTRAS_FUENTES/<MODELO>/ (solo actual efímero).
"""

from sys import argv, path
path.insert(0, '/home/dnieves/Documentos/My-4Cast')

from glob import glob
from xarray import open_zarr
from numpy import timedelta64
from src.modelos import modelos_colombia
from googleapiclient.discovery import build
from os.path import basename, exists, getsize
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

#%% PARÁMETROS Y CONSTANTES
FOLDER_ROOT_ID = '1zsEhI-CnExH7RGM0qi-y1zTGPj9pAF45'
TOKEN_FILE     = '/home/dnieves/Documentos/My-4Cast/token_drive.json'
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

#%% SINCRONIZACIÓN POR FUENTE (WN3 HISTÓRICO VS. OTRAS FUENTES EFÍMERAS)
if __name__ == '__main__':
    objetivo = argv[1] if len(argv) > 1 else 'all'
    print('==========================================================', flush=True)
    print('Sincronización Multimodelo de Animaciones a Google Drive', flush=True)
    print('==========================================================', flush=True)

    service       = obtener_servicio_drive()
    id_wn3_root   = obtener_o_crear_carpeta(service, 'WN3', FOLDER_ROOT_ID)
    id_otras_root = obtener_o_crear_carpeta(service, 'OTRAS_FUENTES', FOLDER_ROOT_ID)

    for m_id, cfg in modelos_colombia.items():
        if objetivo != 'all' and m_id not in objetivo.split(','):
            continue
        if not exists(cfg['ruta_zarr']) or not exists(cfg['dir_anim']):
            continue

        videos = [v for v in sorted(glob(f"{cfg['dir_anim']}/{m_id}_animacion_*.mp4")) if not v.endswith('_master.mp4')]
        if not videos:
            continue

        ds        = open_zarr(cfg['ruta_zarr'])
        init_utc  = ds.init_time.values[-1]
        init_hl   = init_utc - timedelta64(5, 'h')
        fecha_tag = str(init_hl)[:10].replace('-', '') + f"_{str(init_hl)[11:13]}HL"

        print(f"\n[{m_id.upper()}] Corrida: {fecha_tag} ({len(videos)} videos en {cfg['dir_anim']})", flush=True)

        if cfg['almacenamiento'] == 'canonico_historico':
            id_actual = obtener_o_crear_carpeta(service, 'actual', id_wn3_root)
            id_hist   = obtener_o_crear_carpeta(service, 'historico', id_wn3_root)
            id_corr   = obtener_o_crear_carpeta(service, fecha_tag, id_hist)
            for v in videos:
                nom_limpio = basename(v).replace('_whatsapp', '')
                subir_o_actualizar_archivo(service, v, id_actual, nom_limpio)
                subir_o_actualizar_archivo(service, v, id_corr, f'{fecha_tag}_{nom_limpio}')
        else:
            subcarpeta_mod = cfg['carpeta'].split('/')[-1]
            id_mod_folder  = obtener_o_crear_carpeta(service, subcarpeta_mod, id_otras_root)
            for v in videos:
                nom_limpio = basename(v).replace('_whatsapp', '')
                subir_o_actualizar_archivo(service, v, id_mod_folder, nom_limpio)

    print('\n✓ Sincronización multimodelo a Google Drive finalizada.', flush=True)
