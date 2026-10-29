"""
00_backfill_wn3.py — Backfill continuo cada 6h de WeatherNext 3 para Colombia.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.2.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-10-29][Duvan]: Backfill regular cada 6h (30 corridas homogéneas).
"""

from sys import path
from shutil import rmtree
from os.path import exists

path.insert(0, '/home/dnieves/Documentos/My-4Cast')
from src.descarga import apilar_corrida_zarr, descargar_corrida_wn3

#%% CONFIGURACIÓN DE RUTAS Y CORRIDAS
ruta_zarr = '/mnt/datos/dnieves/WN3/raw/colombia_weathernext3.zarr'
ruta_tmp  = '/mnt/datos/dnieves/WN3/staging/tmp_backfill.zarr'

fechas    = [f'202610{d:02d}' for d in range(22, 29)]
horas     = ['00', '06', '12', '18']
runs      = [f'{f}_{h}hr_01_preds' for f in fechas for h in horas] + [
    '20261029_00hr_01_preds',
    '20261029_06hr_01_preds',
]

#%% PROCESAMIENTO SECUENCIAL HOMOGÉNEO
for i, run_id in enumerate(runs):
    print(f'[{i+1}/{len(runs)}] Descargando {run_id}...', flush=True)
    ds = descargar_corrida_wn3(run_id, lead_horas=360)
    if i == 0:
        rmtree(ruta_zarr, ignore_errors=True)
    apilar_corrida_zarr(ds, ruta_zarr, ruta_tmp)
    print(f'[{i+1}/{len(runs)}] Completado y apilado {run_id}.', flush=True)

print('Backfill de 30 corridas homogéneas cada 6h completado con éxito.', flush=True)
