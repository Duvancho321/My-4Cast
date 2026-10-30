"""
descarga.py — Ingesta y validación modular de corridas de WeatherNext 3.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.2.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-10-29][Duvan]: Soporte para streaming de todas las 126 variables.
"""

from os.path import exists
from shutil import rmtree
from xarray import open_zarr
from obstore.store import GCSStore
from zarr.storage import ObjectStore
from numpy import datetime64, timedelta64

#%% CONFIGURACIÓN CANÓNICA
lat_min    = -5.0
lat_max    = 16.5
lon_min    = 275.0
lon_max    = 300.0
bucket_wn3 = 'weathernext3_statistics_spatial'

#%% FUNCIONES DE INGESTA
def verificar_corrida_local(ruta_zarr, init_time):
    """
    Verifica si una corrida específica ya existe en el Zarr local.

    Parameters
    ----------
    ruta_zarr : str
        Ruta absoluta al almacén Zarr local.
    init_time : str or numpy.datetime64
        Fecha y hora de inicialización de la corrida a verificar.

    Returns
    -------
    bool
        True si la corrida ya se encuentra en el almacén, False si no existe.
    """
    if not exists(ruta_zarr):
        return False
    ds_local = open_zarr(ruta_zarr)
    return datetime64(init_time) in ds_local['init_time'].values


def existe_en_gcs(run_id):
    """
    Verifica si una corrida existe publicada en Google Cloud Storage.

    Parameters
    ----------
    run_id : str
        Identificador de la corrida (ej. '20261029_12hr_01_preds').

    Returns
    -------
    bool
        True si la corrida existe en GCS, False en caso contrario.
    """
    prefix_run = f'weathernext_3_0_0_statistics/zarr/2026_to_present/{run_id}/predictions.zarr'
    try:
        open_zarr(ObjectStore(GCSStore(bucket=bucket_wn3, prefix=prefix_run)))
        return True
    except Exception:
        return False


def descargar_corrida_wn3(run_id, lead_horas=360, tipo_vars='all'):
    """
    Descarga y recorta una corrida de WeatherNext 3 desde Google Cloud Storage.

    Parameters
    ----------
    run_id : str
        Identificador de la corrida (ej. '20261029_12hr_01_preds').
    lead_horas : int, optional
        Horizonte máximo de pronóstico en horas (por defecto 360).
    tipo_vars : str, optional
        'all' para las 126 variables o 'precipitation' para precipitación.

    Returns
    -------
    xarray.Dataset
        Dataset recortado con dimensión 'init_time' para Colombia.
    """
    prefix_run = f'weathernext_3_0_0_statistics/zarr/2026_to_present/{run_id}/predictions.zarr'
    ds_remote  = open_zarr(ObjectStore(GCSStore(bucket=bucket_wn3, prefix=prefix_run)))
    vars_sel   = list(ds_remote.data_vars) if tipo_vars == 'all' else [v for v in ds_remote.data_vars if 'precipitation' in v]
    return (ds_remote[vars_sel]
        .sel(lat_0p1=slice(lat_min, lat_max), lon_0p1=slice(lon_min, lon_max),
             lat_0p05=slice(lat_min, lat_max), lon_0p05=slice(lon_min, lon_max),
             lead_time=slice(timedelta64(1, 'h'), timedelta64(lead_horas, 'h')))
        .expand_dims('init_time'))


def apilar_corrida_zarr(ds_nueva, ruta_zarr, ruta_tmp):
    """
    Escribe o añade de forma atómica una corrida al almacén Zarr local.

    Parameters
    ----------
    ds_nueva : xarray.Dataset
        Dataset recortado con dimensión 'init_time' a almacenar.
    ruta_zarr : str
        Ruta absoluta al almacén Zarr de destino.
    ruta_tmp : str
        Ruta temporal de staging para garantizar escritura atómica.

    Returns
    -------
    None
    """
    rmtree(ruta_tmp, ignore_errors=True)
    ds_nueva['init_time'].encoding['units'] = 'hours since 2026-10-22 00:00:00'
    ds_nueva['init_time'].encoding['dtype'] = 'int64'
    ds_nueva.to_zarr(ruta_tmp, mode='w')
    if not exists(ruta_zarr):
        ds_nueva.to_zarr(ruta_zarr, mode='w')
    else:
        ds_nueva.to_zarr(ruta_zarr, mode='a', append_dim='init_time')
    rmtree(ruta_tmp, ignore_errors=True)
