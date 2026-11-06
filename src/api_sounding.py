"""
api_sounding.py — Microservicio FastAPI de sondeo puntual sobre mallas Zarr de pronóstico meteorológico.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.1.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-11-05][Duvan]: Servicio asíncrono con LRU cache y headers CDN.
"""

from json import dumps
from xarray import open_zarr
from asyncio import Semaphore
from pandas import to_datetime
from functools import lru_cache
from os.path import exists, getmtime
from src.modelos import modelos_colombia
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Query, Response
from numpy import arctan2, cos, cumsum, deg2rad, isnan, maximum, nan_to_num, pi, rad2deg, round, sin, timedelta64, zeros

#%% CONFIGURACIÓN DE PARÁMETROS Y CONTROL DE CONCURRENCIA
app            = FastAPI(title='My-4Cast Sounding API', version='0.1.0')
semaforo_disco = Semaphore(8)
cache_modelos  = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['*'])

#%% GESTIÓN DE MODELOS EN MEMORIA
def obtener_modelo(model_id):
    if model_id not in modelos_colombia:
        return None
    cfg  = modelos_colombia[model_id]
    ruta = cfg['ruta_zarr']
    if not exists(ruta):
        return None
    mtime = getmtime(ruta)
    if model_id in cache_modelos and cache_modelos[model_id]['mtime'] == mtime:
        return cache_modelos[model_id]

    ds     = open_zarr(ruta)
    latest = None
    for idx in range(len(ds.init_time) - 1, -1, -1):
        cand   = ds.isel(init_time=idx)
        sample = cand['temperature_2m_p50'].isel(lat_0p1=len(cand.lat_0p1) // 2, lon_0p1=len(cand.lon_0p1) // 2).values
        if not isnan(sample).all():
            if model_id != 'wn3' or (not isnan(sample).any() and len(sample) == 360):
                latest = cand
                break
    if latest is None:
        return None

    init_utc_raw = latest.init_time.values
    lead_horas   = [int(td / timedelta64(1, 'h')) for td in latest.lead_time.values]
    dts          = to_datetime([init_utc_raw + timedelta64(h, 'h') for h in lead_horas])
    theta_d      = 2 * pi * (dts.day_of_year.values - 1) / 365.0
    rc_dis       = 1.00011 + 0.034221 * cos(theta_d) + 0.00128 * sin(theta_d) + 0.000719 * cos(2 * theta_d) + 0.000077 * sin(2 * theta_d)
    rc_dec       = 0.006918 - 0.39912 * cos(theta_d) + 0.070257 * sin(theta_d) - 0.006758 * cos(2 * theta_d) + 0.000907 * sin(2 * theta_d) - 0.002697 * cos(3 * theta_d) + 0.00148 * sin(3 * theta_d)
    utc_hour     = dts.hour.values + dts.minute.values / 60.0

    cache_modelos[model_id] = {
        'cand': latest,
        'mtime': mtime,
        'cfg': cfg,
        'lead_horas': lead_horas,
        'n_frames': len(lead_horas),
        'rc_dis': rc_dis,
        'rc_dec': rc_dec,
        'utc_hour': utc_hour,
        'paso_f': float(cfg['paso_h']) if cfg['paso_h'] < 24 else 1.0
    }
    return cache_modelos[model_id]

#%% EXTRACCIÓN Y SERIALIZACIÓN OPTIMIZADA CON CACHÉ LRU
@lru_cache(maxsize=16384)
def extraer_sondeo_json(model_id, lat_r, lon_r):
    entry = obtener_modelo(model_id)
    if entry is None:
        return None

    cand     = entry['cand']
    cfg      = entry['cfg']
    n_frames = entry['n_frames']
    lon_t    = 360.0 + lon_r if lon_r < 0 else lon_r
    pt       = cand.sel(lat_0p1=lat_r, lon_0p1=lon_t, method='nearest')

    actual_lat = float(pt.lat_0p1.values)
    actual_lon = float(pt.lon_0p1.values)
    if actual_lon > 180:
        actual_lon -= 360.0

    ceros_pt = zeros(n_frames, dtype=float)
    t2m_p50  = round(nan_to_num(pt['temperature_2m_p50'].values.astype(float) - 273.15, nan=20.0), 1).tolist()
    t2m_p10  = round(nan_to_num(pt['temperature_2m_p10'].values.astype(float) - 273.15, nan=15.0), 1).tolist()
    t2m_p90  = round(nan_to_num(pt['temperature_2m_p90'].values.astype(float) - 273.15, nan=25.0), 1).tolist()

    ppt_p50  = round(nan_to_num(pt['total_precipitation_1hr_p50'].values.astype(float) * 1000.0, nan=0.0), 2).tolist()
    ppt_p10  = round(nan_to_num(pt['total_precipitation_1hr_p10'].values.astype(float) * 1000.0, nan=0.0), 2).tolist()
    ppt_p90  = round(nan_to_num(pt['total_precipitation_1hr_p90'].values.astype(float) * 1000.0, nan=0.0), 2).tolist()

    wspd_p50 = round(nan_to_num(pt['wind_speed_10m_p50'].values.astype(float), nan=2.0), 1).tolist()
    wspd_p10 = round(nan_to_num(pt['wind_speed_10m_p10'].values.astype(float), nan=1.0), 1).tolist()
    wspd_p90 = round(nan_to_num(pt['wind_speed_10m_p90'].values.astype(float), nan=4.0), 1).tolist()

    u    = nan_to_num(pt['u_component_of_wind_10m_p50'].values.astype(float), nan=0.0)
    v    = nan_to_num(pt['v_component_of_wind_10m_p50'].values.astype(float), nan=0.0)
    wdir = round((180 + rad2deg(arctan2(u, v))) % 360, 0).astype(int).tolist()

    rad_p50   = round(nan_to_num(pt['surface_solar_radiation_downwards_1hr_p50'].values.astype(float) / 3600.0, nan=0.0), 0).astype(int).tolist()
    cld_p50   = round(nan_to_num(pt['total_cloud_cover_p50'].values.astype(float) * 100.0, nan=50.0), 0).astype(int).tolist()
    cldl_p50  = round(nan_to_num(pt['low_cloud_cover_p50'].values.astype(float) * 100.0, nan=0.0), 0).astype(int).tolist() if 'low_cloud_cover_p50' in pt else ceros_pt.astype(int).tolist()
    cldm_p50  = round(nan_to_num(pt['medium_cloud_cover_p50'].values.astype(float) * 100.0, nan=0.0), 0).astype(int).tolist() if 'medium_cloud_cover_p50' in pt else ceros_pt.astype(int).tolist()
    cldh_p50  = round(nan_to_num(pt['high_cloud_cover_p50'].values.astype(float) * 100.0, nan=0.0), 0).astype(int).tolist() if 'high_cloud_cover_p50' in pt else ceros_pt.astype(int).tolist()
    imerg_p50 = round(nan_to_num(pt['imerg_tp_1hr_p50'].values.astype(float) * 1000.0, nan=0.0), 2).tolist() if 'imerg_tp_1hr_p50' in pt else ppt_p50
    exptp_p50 = round(nan_to_num(pt['experimental_tp_1hr_p50'].values.astype(float) * 1000.0, nan=0.0), 2).tolist() if 'experimental_tp_1hr_p50' in pt else ppt_p50

    w100_p50 = round(nan_to_num(pt['wind_speed_100m_p50'].values.astype(float), nan=2.0), 1).tolist() if 'wind_speed_100m_p50' in pt else wspd_p50
    u100     = nan_to_num(pt['u_component_of_wind_100m_p50'].values.astype(float), nan=0.0) if 'u_component_of_wind_100m_p50' in pt else u
    v100     = nan_to_num(pt['v_component_of_wind_100m_p50'].values.astype(float), nan=0.0) if 'v_component_of_wind_100m_p50' in pt else v
    wdir100  = round((180 + rad2deg(arctan2(u100, v100))) % 360, 0).astype(int).tolist()

    omega   = deg2rad(15.0 * ((entry['utc_hour'] + lon_r / 15.0) % 24 - 12.0))
    lat_rad = deg2rad(lat_r)
    cos_z   = sin(lat_rad) * sin(entry['rc_dec']) + cos(lat_rad) * cos(entry['rc_dec']) * cos(omega)
    rad_toa = round(maximum(0.0, 1361.0 * entry['rc_dis'] * cos_z), 0).astype(int).tolist()

    paso_f = entry['paso_f']
    doc    = {
        'info': {
            'nombre': f'Punto {actual_lat:.2f}°, {abs(actual_lon):.2f}°W',
            'depto': 'Sondeo puntual',
            'lat': round(actual_lat, 4),
            'lon': round(actual_lon, 4),
            'altitud': 0,
            'tag': 'Malla ' + cfg['resolucion']
        },
        'temperatura': {'p10': t2m_p10, 'p50': t2m_p50, 'p90': t2m_p90},
        'precipitacion': {
            'p10': ppt_p10,
            'p50': ppt_p50,
            'p90': ppt_p90,
            'acumulada_p10': round(cumsum(ppt_p10) * paso_f, 2).tolist(),
            'acumulada': round(cumsum(ppt_p50) * paso_f, 2).tolist(),
            'acumulada_p90': round(cumsum(ppt_p90) * paso_f, 2).tolist()
        },
        'precipitacion_imerg': {'p50': imerg_p50},
        'precipitacion_exp': {'p50': exptp_p50},
        'viento': {'p10': wspd_p10, 'p50': wspd_p50, 'p90': wspd_p90, 'dir': wdir},
        'viento_100m': {'p50': w100_p50, 'dir': wdir100},
        'radiacion_solar': {'p50': rad_p50, 'teorica': rad_toa},
        'nubosidad': {'p50': cld_p50},
        'nubosidad_baja': {'p50': cldl_p50},
        'nubosidad_media': {'p50': cldm_p50},
        'nubosidad_alta': {'p50': cldh_p50}
    }
    return dumps(doc, ensure_ascii=False, separators=(',', ':'))

#%% RUTAS DEL SERVICIO HTTP
@app.get('/api/sounding')
async def sounding(
    lat: float = Query(..., ge=-5.0, le=16.5, description='Latitud (-5 a 16.5)'),
    lon: float = Query(..., ge=-85.0, le=-60.0, description='Longitud (-85 a -60)'),
    model: str = Query('wn3', description='Identificador del modelo')):
    if model not in modelos_colombia:
        raise HTTPException(status_code=400, detail=f'Modelo {model} no reconocido')

    lat_r = round(lat, 2)
    lon_r = round(lon, 2)

    async with semaforo_disco:
        payload = extraer_sondeo_json(model, lat_r, lon_r)

    if payload is None:
        raise HTTPException(status_code=500, detail='Fallo en extracción de sondeo o modelo no disponible')

    return Response(
        content=payload,
        media_type='application/json',
        headers={
            'Cache-Control': 'public, max-age=14400, stale-while-revalidate=3600',
            'Access-Control-Allow-Origin': '*'
        })

@app.get('/api/health')
async def health():
    info_cache = extraer_sondeo_json.cache_info()
    return {
        'status': 'ok',
        'modelos_cargados': list(cache_modelos.keys()),
        'lru_hits': info_cache.hits,
        'lru_misses': info_cache.misses,
        'lru_puntos_en_memoria': info_cache.currsize,
        'lru_capacidad_max': info_cache.maxsize
    }

@app.post('/api/reload')
async def reload():
    extraer_sondeo_json.cache_clear()
    cache_modelos.clear()
    return {'status': 'cache limpiada exitosamente'}
