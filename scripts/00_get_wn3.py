"""
00_get_wn3.py — Ingesta operativa parametrizada de WeatherNext 3 para Colombia.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.1.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-10-29][Duvan]: Ingesta con parámetros CLI y validación anti-duplicados.
"""

from sys import exit, path
from argparse import ArgumentParser
from datetime import datetime, timezone

path.insert(0, '/home/dnieves/Documentos/My-4Cast')
from src.descarga import apilar_corrida_zarr, descargar_corrida_wn3, verificar_corrida_local

#%% CONFIGURACIÓN DE PARÁMETROS
parser = ArgumentParser(description='Ingesta de corridas WeatherNext 3 para Colombia')
parser.add_argument('--fecha', type=str, default=datetime.now(timezone.utc).strftime('%Y%m%d'),
                    help='Fecha de la corrida (YYYYMMDD o YYYY-MM-DD)')
parser.add_argument('--hora', type=str, default='06', choices=['00', '06', '12', '18'],
                    help='Hora sinóptica UTC de inicialización (00, 06, 12, 18)')
parser.add_argument('--forzar', action='store_true',
                    help='Fuerza la descarga e ignora la verificación local')
args = parser.parse_args()

fecha_limpia = args.fecha.replace('-', '')
fecha_iso    = f'{fecha_limpia[:4]}-{fecha_limpia[4:6]}-{fecha_limpia[6:8]}'
hora_str     = args.hora.zfill(2)
run_id       = f'{fecha_limpia}_{hora_str}hr_01_preds'
init_time    = f'{fecha_iso}T{hora_str}:00:00'
ruta_zarr    = '/mnt/datos/dnieves/WN3/raw/colombia_weathernext3.zarr'
ruta_tmp     = f'/mnt/datos/dnieves/WN3/staging/tmp_{run_id}.zarr'

#%% VERIFICACIÓN E INGESTA
if not args.forzar and verificar_corrida_local(ruta_zarr, init_time):
    print(f'Corrida {init_time} ya existe en el Zarr local. Omitiendo descarga.')
    exit(0)

print(f'Descargando corrida {run_id} ({init_time})...')
ds_corrida = descargar_corrida_wn3(run_id, lead_horas=360)
apilar_corrida_zarr(ds_corrida, ruta_zarr, ruta_tmp)
print(f'Corrida {run_id} integrada exitosamente en {ruta_zarr}.')
