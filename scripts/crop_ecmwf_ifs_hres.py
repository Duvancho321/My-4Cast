#!/usr/bin/env python3
"""
crop_ecmwf_ifs_hres.py — Descarga y recorte del modelo ECMWF IFS HRES (0.1°) vía Arraylake para Colombia.

__author__: "Duvan Nieves"
__copyright__: "Duvan Nieves Ruiz"
__version__: "0.1.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves.sci@gmail.com"
__status__: "Developer"
__changues__:
    - [2026-11-06][Duvan]: Versión inicial con soporte Zarr v3 e Icechunk v2 vía Arraylake.
"""

from json import dump, load
from shutil import rmtree
from os.path import exists
from os import getenv, makedirs
from arraylake import Client
from datetime import datetime, timezone
from xarray import DataArray, Dataset, open_dataset
from numpy import clip, diff, float32, hypot, timedelta64

#%% CONFIGURACIÓN DE RUTAS Y DOMINIO
dir_base   = getenv('MY4CAST_DATA_DIR', '/mnt/datos/dnieves/WN3')
dir_models = f'{dir_base}/staging/models'
ruta_zarr  = f'{dir_models}/ecmwf_ifs_hres.zarr'
ruta_man   = f'{dir_models}/models_manifest.json'
makedirs(dir_models, exist_ok=True)

lat_min = -5.0
lat_max = 16.5
lon_min = -85.0
lon_max = -60.0

#%% CONEXIÓN A ARRAYLAKE Y APERTURA DEL REPOSITORIO
print('Conectando a Arraylake (organización my-4cast)...', flush=True)
client  = Client()
repo    = client.get_repo('my-4cast/ecmwf-ifs-15-day-forecast-open-subscription')
session = repo.readonly_session(branch='main')
ds      = open_dataset(session.store, engine='zarr', chunks={})

init_dt64 = ds.time.values[-1]
init_str  = str(init_dt64)[:19]
print(f'Última corrida disponible: {init_str} UTC', flush=True)

#%% EXTRACCIÓN DEL DOMINIO DE COLOMBIA
req_vars = ['2t', 'tp', '10u', '10v', '100u', '100v', 'ssrd', 'lcc', 'mcc', 'hcc']
print(f'Descargando recorte espacial de Colombia (0.1°) para {len(req_vars)} variables...', flush=True)
sub = ds[req_vars].isel(time=-1).sel(
    latitude=slice(lat_max, lat_min),
    longitude=slice(lon_min, lon_max)
).compute()

# Invertir eje latitudinal a orden ascendente (-5 a 16.5)
sub      = sub.isel(latitude=slice(None, None, -1))
lats_asc = sub.latitude.values.astype(float32)
lons_360 = (sub.longitude.values + 360.0).astype(float32)

#%% CÁLCULO DE PASOS Y DESACUMULACIÓN TEMPORAL (LEADS >= 1)
# Omitir lead 0 (análisis) para el pronóstico
leads_td = sub.step.values[1:]
step_h   = (sub.step.values.astype('timedelta64[s]').astype(float)) / 3600.0
diff_h   = diff(step_h)

# Variables instantáneas (leads 1 en adelante)
t2m_k = sub['2t'].values[1:].astype(float32)
u10   = sub['10u'].values[1:].astype(float32)
v10   = sub['10v'].values[1:].astype(float32)
w10   = hypot(u10, v10).astype(float32)
u100  = sub['100u'].values[1:].astype(float32)
v100  = sub['100v'].values[1:].astype(float32)
w100  = hypot(u100, v100).astype(float32)

# Desacumulación de precipitación total (m/h)
tp_raw    = sub['tp'].values
tp_diff   = clip(diff(tp_raw, axis=0), 0.0, None)
ppt_rate  = (tp_diff / diff_h[:, None, None]).astype(float32)

# Desacumulación de radiación solar superficial incidente (J/m^2/h)
ssrd_raw  = sub['ssrd'].values
ssrd_diff = clip(diff(ssrd_raw, axis=0), 0.0, None)
ssrd_rate = (ssrd_diff / diff_h[:, None, None]).astype(float32)

# Cobertura nubosa total vía máxima-aleatoria
lcc = clip(sub['lcc'].values[1:], 0.0, 1.0)
mcc = clip(sub['mcc'].values[1:], 0.0, 1.0)
hcc = clip(sub['hcc'].values[1:], 0.0, 1.0)
tcc = (1.0 - (1.0 - lcc) * (1.0 - mcc) * (1.0 - hcc)).astype(float32)

#%% ESTRUCTURACIÓN DEL DATASET CANÓNICO
coords = {
    'init_time': [init_dt64],
    'lead_time': leads_td,
    'lat_0p1':   lats_asc,
    'lon_0p1':   lons_360
}
dims_4d = ('init_time', 'lead_time', 'lat_0p1', 'lon_0p1')

campos = {
    'total_precipitation_1hr_p10':               ppt_rate[None, ...],
    'total_precipitation_1hr_p50':               ppt_rate[None, ...],
    'total_precipitation_1hr_p90':               ppt_rate[None, ...],
    'temperature_2m_p10':                        t2m_k[None, ...],
    'temperature_2m_p50':                        t2m_k[None, ...],
    'temperature_2m_p90':                        t2m_k[None, ...],
    'u_component_of_wind_10m_p50':               u10[None, ...],
    'v_component_of_wind_10m_p50':               v10[None, ...],
    'wind_speed_10m_p10':                        w10[None, ...],
    'wind_speed_10m_p50':                        w10[None, ...],
    'wind_speed_10m_p90':                        w10[None, ...],
    'u_component_of_wind_100m_p50':              u100[None, ...],
    'v_component_of_wind_100m_p50':              v100[None, ...],
    'wind_speed_100m_p50':                       w100[None, ...],
    'surface_solar_radiation_downwards_1hr_p50': ssrd_rate[None, ...],
    'total_cloud_cover_p50':                     tcc[None, ...]
}

attrs = {
    'nombre': 'ECMWF IFS HRES 15-Day (Open)',
    'organizacion': 'ECMWF / Brightband',
    'tipo': 'Físico Determinista',
    'resolucion': '0.1° (~10 km)',
    'paso_h': 1,
    'horizonte_h': 360,
    'almacenamiento': 'efimero_visualizacion',
    'ensamble': 'False'
}

data_vars = {k: DataArray(v, coords=coords, dims=dims_4d) for k, v in campos.items()}
ds_out    = Dataset(data_vars, coords=coords, attrs=attrs)
ds_out['init_time'].encoding['units'] = 'hours since 2026-01-01 00:00:00'
ds_out['init_time'].encoding['dtype'] = 'int64'

print(f'Guardando dataset Zarr en: {ruta_zarr}...', flush=True)
rmtree(ruta_zarr, ignore_errors=True)
ds_out.to_zarr(ruta_zarr, mode='w')
print('Recorte guardado exitosamente.', flush=True)

#%% ACTUALIZACIÓN DEL MANIFEST LOCAL
manifest = {'updated_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'models': {}}
if exists(ruta_man):
    try:
        with open(ruta_man, 'r', encoding='utf-8') as f:
            manifest = load(f)
    except Exception:
        pass

manifest['models']['ecmwf_ifs_hres'] = {
    'model_id': 'ecmwf_ifs_hres',
    'init_time': init_str,
    'steps': len(leads_td),
    'zip': 'colombia_ecmwf_ifs_hres.zip',
    'nombre': 'ECMWF IFS HRES 15-Day (Open)',
    'organizacion': 'ECMWF / Brightband',
    'tipo': 'Físico Determinista',
    'resolucion': '0.1° (~10 km)',
    'paso_h': 1,
    'horizonte_h': 360,
    'ensamble': False
}
manifest['updated_utc'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

with open(ruta_man, 'w', encoding='utf-8') as f:
    dump(manifest, f, indent=2, ensure_ascii=False)
print('Manifest local actualizado.', flush=True)
