"""
03_upload_drive.py — Sincronización automática de animaciones operativas hacia Google Drive.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.1.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
"""

from glob import glob
from os.path import basename, exists, getsize
from json import load
from xarray import open_zarr
from numpy import timedelta64
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

#%% PARÁMETROS Y CONSTANTES
FOLDER_ROOT_ID = '1zsEhI-CnExH7RGM0qi-y1zTGPj9pAF45'
DIR_ANIM       = '/mnt/datos/dnieves/WN3/animations'
RUTA_ZARR      = '/mnt/datos/dnieves/WN3/raw/colombia_wn3_full.zarr'
TOKEN_FILE     = '/home/dnieves/Documentos/My-4Cast/token_drive.json'
CLIENT_SECRET  = '/home/dnieves/Documentos/My-4Cast/client_secret.json'
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
    res = service.files().list(
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
    res = service.files().list(
        q=query,
        fields='files(id, name)',
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    files = res.get('files', [])

    if files:
        file_id = files[0]['id']
        actualizado = service.files().update(
            fileId=file_id,
            media_body=media,
            fields='id, name, size',
            supportsAllDrives=True
        ).execute()
        print(f"  [✓ Actualizado] {nombre_destino} ({int(actualizado.get('size', 0)) / 1e6:.1f} MB)", flush=True)
        return actualizado.get('id')
    else:
        meta = {
            'name': nombre_destino,
            'parents': [parent_id]
        }
        creado = service.files().create(
            body=meta,
            media_body=media,
            fields='id, name, size',
            supportsAllDrives=True
        ).execute()
        print(f"  [✓ Subido] {nombre_destino} ({int(creado.get('size', 0)) / 1e6:.1f} MB)", flush=True)
        return creado.get('id')

if __name__ == '__main__':
    print('==========================================================', flush=True)
    print('Sincronización de animaciones WhatsApp hacia Google Drive', flush=True)
    print('==========================================================', flush=True)

    ds = open_zarr(RUTA_ZARR)
    init_utc = ds.init_time.values[-1]
    init_hl  = init_utc - timedelta64(5, 'h')
    fecha_tag = str(init_hl)[:10].replace('-', '') + f"_{str(init_hl)[11:13]}HL"
    print(f'Corrida canónica activa: {fecha_tag}', flush=True)

    service = obtener_servicio_drive()

    print('Verificando estructura de carpetas en Drive...', flush=True)
    id_actual = obtener_o_crear_carpeta(service, 'actual', FOLDER_ROOT_ID)
    id_hist_root = obtener_o_crear_carpeta(service, 'historico', FOLDER_ROOT_ID)
    id_hist_corrida = obtener_o_crear_carpeta(service, fecha_tag, id_hist_root)

    archivos_whatsapp = sorted(glob(f'{DIR_ANIM}/*whatsapp*.mp4'))
    if not archivos_whatsapp:
        print('Aviso: No se encontraron archivos *whatsapp*.mp4 en', DIR_ANIM, flush=True)
        exit(0)

    def limpiar_nombre(nombre_archivo):
        # Quita el sufijo _whatsapp para que el archivo quede limpio en Drive
        return nombre_archivo.replace('_whatsapp', '')

    print(f'Archivos encontrados para sincronizar ({len(archivos_whatsapp)}):', flush=True)
    for f in archivos_whatsapp:
        tam_mb = getsize(f) / 1e6
        print(f" - {basename(f)} ➔ {limpiar_nombre(basename(f))} ({tam_mb:.1f} MB)", flush=True)

    print('\n1. Sincronizando carpeta "actual"...', flush=True)
    for ruta in archivos_whatsapp:
        nom_destino = limpiar_nombre(basename(ruta))
        subir_o_actualizar_archivo(service, ruta, id_actual, nom_destino)

    print(f'\n2. Guardando copia en histórico ("historico/{fecha_tag}")...', flush=True)
    for ruta in archivos_whatsapp:
        nom_destino = f"{fecha_tag}_{limpiar_nombre(basename(ruta))}"
        subir_o_actualizar_archivo(service, ruta, id_hist_corrida, nom_destino)

    print('\n✓ Sincronización a Google Drive finalizada exitosamente.', flush=True)
