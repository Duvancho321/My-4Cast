"""
cloud_crop_multimodel.py — Recorte efímero en la nube de 11 modelos abiertos (GFS, IFS ENS/HRES, AIFS ENS/Single, CHIRPS-GEFS, ICON, GraphCast, Aurora, FourCastNet v2, Pangu) para Colombia.

__author__: "Duvan Nieves"
__copyright__: "Duvan Nieves Ruiz"
__version__: "0.3.2"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves.sci@gmail.com"
__status__: "Developer"
__changues__:
    - [2026-11-13][Duvan]: Integración de Vaisala Xweather Forecast (360h, malla Colombia) vía API.
    - [2026-11-10][Duvan]: Fallback sin token a gs://ecmwf-open-data (0.1°) para HRES.
    - [2026-11-06][Duvan]: Integración de ECMWF IFS HRES (0.1°) vía Arraylake / Icechunk v2.
    - [2026-11-05][Duvan]: Inclusión de Aurora, FourCastNet v2, GraphCast y Pangu-Weather con concurrencia en ICON y CHIRPS-GEFS.
"""

from os import getenv
from sys import argv
from re import findall
from time import sleep
from struct import unpack
from json import dump, loads
from h5py import File
from requests import Session
from bz2 import decompress
from fsspec import filesystem
from scipy.spatial import cKDTree
from rasterio import open as rio_open
from shutil import make_archive, rmtree
from gribberish import parse_grib_array
from rasterio.windows import from_bounds
from urllib.request import Request, urlopen
from icechunk import Repository, s3_storage
from xarray import DataArray, Dataset, open_zarr
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from numpy import arange, argmax, array, clip, column_stack, cos, deg2rad, diff, flipud, float32, frombuffer, full, hypot, isnan, linspace, meshgrid, nan, nan_to_num, nanpercentile, sin, take_along_axis, timedelta64, where, zeros

#%% CONFIGURACIÓN DE DOMINIO Y CATÁLOGO MULTIMODELO
lat_min = -5.0
lat_max = 16.5
lon_min = -85.0
lon_max = -60.0
filtro  = argv[1] if len(argv) > 1 else 'all'

catalogo_modelos = {
    'noaa_gfs': {
        'nombre': 'NOAA GFS Forecast',
        'organizacion': 'NOAA / NCEP',
        'tipo': 'Físico Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 1,
        'horizonte_h': 384,
        'bucket': 'dynamical-noaa-gfs',
        'prefix': 'noaa-gfs-forecast/v0.2.7.icechunk',
        'zarr_url': 'https://data.dynamical.org/noaa/gfs/forecast/latest.zarr',
        'ensamble': False
    },
    'ecmwf_ifs_hres': {
        'nombre': 'ECMWF IFS HRES 15-Day (Open)',
        'organizacion': 'ECMWF / Brightband',
        'tipo': 'Físico Determinista',
        'resolucion': '0.1° (~10 km)',
        'paso_h': 1,
        'horizonte_h': 360,
        'repo_arraylake': 'my-4cast/ecmwf-ifs-15-day-forecast-open-subscription',
        'ensamble': False
    },
    'ecmwf_ifs': {
        'nombre': 'ECMWF IFS ENS 15-Day (Open)',
        'organizacion': 'ECMWF',
        'tipo': 'Físico Ensamble (51 miembros)',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 3,
        'horizonte_h': 360,
        'bucket': 'dynamical-ecmwf-ifs-ens',
        'prefix': 'ecmwf-ifs-ens-forecast-15-day-0-25-degree/v0.1.0.icechunk',
        'zarr_url': 'https://data.dynamical.org/ecmwf/ifs-ens/forecast-15-day-0-25-degree/latest.zarr',
        'ensamble': True
    },
    'ecmwf_aifs_ens': {
        'nombre': 'ECMWF AIFS ENS 15-Day',
        'organizacion': 'ECMWF',
        'tipo': 'IA Ensamble (51 miembros)',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 360,
        'bucket': 'dynamical-ecmwf-aifs-ens',
        'prefix': 'ecmwf-aifs-ens-forecast/v0.1.0.icechunk',
        'ensamble': True
    },
    'ecmwf_aifs_single': {
        'nombre': 'ECMWF AIFS Single 15-Day',
        'organizacion': 'ECMWF',
        'tipo': 'IA Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 360,
        'bucket': 'dynamical-ecmwf-aifs-single',
        'prefix': 'ecmwf-aifs-single-forecast/v0.1.0.icechunk',
        'zarr_url': 'https://data.dynamical.org/ecmwf/aifs-single/forecast/latest.zarr',
        'ensamble': False
    },
    'chirps_gefs': {
        'nombre': 'UCSB CHIRPS-GEFS v3 16-Day',
        'organizacion': 'UCSB Climate Hazards Center',
        'tipo': 'Híbrido Satélite + GEFS',
        'resolucion': '0.05° (~5 km)',
        'paso_h': 24,
        'horizonte_h': 384,
        'ensamble': False
    },
    'dwd_icon': {
        'nombre': 'DWD ICON Global',
        'organizacion': 'Deutscher Wetterdienst (DWD)',
        'tipo': 'Físico Determinista',
        'resolucion': '0.125° (~13 km)',
        'paso_h': 3,
        'horizonte_h': 180,
        'ensamble': False
    },
    'graphcast_gfs': {
        'nombre': 'GraphCast GFS (NOAA MLWP)',
        'organizacion': 'Google DeepMind / NOAA OAR',
        'tipo': 'IA Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 240,
        'mlwp_code': 'GRAP_v100_GFS',
        'ensamble': False
    },
    'aurora_gfs': {
        'nombre': 'Microsoft Aurora GFS (NOAA MLWP)',
        'organizacion': 'Microsoft Research / NOAA OAR',
        'tipo': 'IA Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 240,
        'mlwp_code': 'AURO_v100_GFS',
        'ensamble': False
    },
    'fourcastnet_gfs': {
        'nombre': 'NVIDIA FourCastNet v2 GFS (NOAA MLWP)',
        'organizacion': 'NVIDIA / NOAA OAR',
        'tipo': 'IA Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 240,
        'mlwp_code': 'FOUR_v200_GFS',
        'ensamble': False
    },
    'pangu_gfs': {
        'nombre': 'Huawei Pangu-Weather GFS (NOAA MLWP)',
        'organizacion': 'Huawei Cloud / NOAA OAR',
        'tipo': 'IA Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 240,
        'mlwp_code': 'PANG_v100_GFS',
        'ensamble': False
    },
    'xweather': {
        'nombre': 'Vaisala Xweather Forecast (Calibrado)',
        'organizacion': 'Vaisala Xweather',
        'tipo': 'Híbrido NWP / Calibrado',
        'resolucion': '1.5° malla / 0.25° interp.',
        'paso_h': 1,
        'horizonte_h': 360,
        'xweather_api': True,
        'ensamble': False
    },
    'ideam_wrf': {
        'nombre': 'IDEAM WRF Colombia 10 km',
        'organizacion': 'IDEAM Colombia',
        'tipo': 'Físico Regional',
        'resolucion': '0.1° (~10 km)',
        'paso_h': 1,
        'horizonte_h': 192,
        'ideam_wrf': True,
        'ensamble': False
    }
}

#%% EMPAQUETADO ESTANDARIZADO AL ESQUEMA CANÓNICO DE COLOMBIA
def guardar_zarr_estandar(model_id, init_dt64, leads_td64, lats_asc, lons_360, campos, attrs_extra):
    coords = {
        'init_time': array([init_dt64], dtype='datetime64[ns]'),
        'lead_time': array(leads_td64, dtype='timedelta64[ns]'),
        'lat_0p1':   array(lats_asc, dtype=float32),
        'lon_0p1':   array(lons_360, dtype=float32)
    }
    dims_4d    = ('init_time', 'lead_time', 'lat_0p1', 'lon_0p1')
    data_vars  = {k: DataArray(v[None, ...].astype(float32), coords=coords, dims=dims_4d) for k, v in campos.items()}
    attrs_limp = {k: str(v) if isinstance(v, bool) else v for k, v in attrs_extra.items()}
    ds_out     = Dataset(data_vars, coords=coords, attrs=attrs_limp)
    ds_out['init_time'].encoding['units'] = 'hours since 2026-01-01 00:00:00'
    ds_out['init_time'].encoding['dtype'] = 'int64'

    ruta_zarr = f'colombia_{model_id}.zarr'
    ruta_zip  = f'colombia_{model_id}'
    rmtree(ruta_zarr, ignore_errors=True)
    ds_out.to_zarr(ruta_zarr, mode='w')
    make_archive(ruta_zip, 'zip', ruta_zarr)
    rmtree(ruta_zarr, ignore_errors=True)
    return f'{ruta_zip}.zip'

#%% RECORTE DE MODELOS DYNAMICAL.ORG / EARTHMOVER (GFS, IFS ENS, AIFS ENS, AIFS SINGLE)
def procesar_dynamical(model_id, cfg):
    try:
        print(f'\n[{model_id}] Abriendo Icechunk S3: s3://{cfg["bucket"]}/{cfg["prefix"]}...', flush=True)
        storage = s3_storage(bucket=cfg['bucket'], prefix=cfg['prefix'], region='us-west-2', anonymous=True)
        repo    = Repository.open(storage)
        session = repo.readonly_session('main')
        ds      = open_zarr(session.store, chunks=None)
    except Exception:
        if 'zarr_url' not in cfg:
            raise
        print(f'[{model_id}] Fallback a Zarr v3 HTTPS: {cfg["zarr_url"]}...', flush=True)
        ds = open_zarr(cfg['zarr_url'], chunks=None)

    init_idx = -1
    for idx in [-1, -2, -3, -4]:
        muestra = ds['temperature_2m'].isel(init_time=idx, lead_time=-1)
        if 'ensemble_member' in muestra.dims:
            muestra = muestra.isel(ensemble_member=0)
        val_chk = muestra.sel(latitude=4.6, longitude=-74.0, method='nearest').values
        if not isnan(val_chk).all():
            init_idx = idx
            break

    init_val = ds.init_time.values[init_idx]
    print(f'[{model_id}] Corrida activa seleccionada: {str(init_val)[:19]} UTC', flush=True)

    vars_req = [
        'precipitation_surface',
        'temperature_2m',
        'wind_u_10m',
        'wind_v_10m',
        'wind_u_100m',
        'wind_v_100m',
        'downward_short_wave_radiation_flux_surface',
        'total_cloud_cover_atmosphere'
    ]
    sub = ds[vars_req].isel(init_time=init_idx, lead_time=slice(1, None)).sel(
        latitude=slice(lat_max, lat_min),
        longitude=slice(lon_min, lon_max)
    ).load()

    sub      = sub.isel(latitude=slice(None, None, -1))
    lats_asc = sub.latitude.values.astype(float32)
    lons_360 = (sub.longitude.values + 360.0).astype(float32)
    leads_td = sub.lead_time.values

    ppt_mm_h = nan_to_num(sub['precipitation_surface'].values, nan=0.0) * 3600.0
    ppt_m    = ppt_mm_h / 1000.0
    t2m_k    = nan_to_num(sub['temperature_2m'].values, nan=20.0) + 273.15
    u10      = nan_to_num(sub['wind_u_10m'].values, nan=0.0)
    v10      = nan_to_num(sub['wind_v_10m'].values, nan=0.0)
    w10      = hypot(u10, v10)
    u100     = nan_to_num(sub['wind_u_100m'].values, nan=0.0)
    v100     = nan_to_num(sub['wind_v_100m'].values, nan=0.0)
    w100     = hypot(u100, v100)
    rad_j    = nan_to_num(sub['downward_short_wave_radiation_flux_surface'].values, nan=0.0) * 3600.0
    cld_frac = nan_to_num(sub['total_cloud_cover_atmosphere'].values, nan=50.0) / 100.0

    if cfg['ensamble']:
        ppt_p10, ppt_p50, ppt_p90 = nanpercentile(ppt_m, [10, 50, 90], axis=1)
        t2m_p10, t2m_p50, t2m_p90 = nanpercentile(t2m_k, [10, 50, 90], axis=1)
        w10_p10, w10_p50, w10_p90 = nanpercentile(w10, [10, 50, 90], axis=1)
        u10_p50  = nanpercentile(u10, 50, axis=1)
        v10_p50  = nanpercentile(v10, 50, axis=1)
        u100_p50 = nanpercentile(u100, 50, axis=1)
        v100_p50 = nanpercentile(v100, 50, axis=1)
        w100_p50 = nanpercentile(w100, 50, axis=1)
        rad_p50  = nanpercentile(rad_j, 50, axis=1)
        cld_p50  = nanpercentile(cld_frac, 50, axis=1)
    else:
        ppt_p10 = ppt_p50 = ppt_p90 = ppt_m
        t2m_p10 = t2m_p50 = t2m_p90 = t2m_k
        w10_p10 = w10_p50 = w10_p90 = w10
        u10_p50, v10_p50   = u10, v10
        u100_p50, v100_p50 = u100, v100
        w100_p50           = w100
        rad_p50            = rad_j
        cld_p50            = cld_frac

    campos = {
        'total_precipitation_1hr_p10':              ppt_p10,
        'total_precipitation_1hr_p50':              ppt_p50,
        'total_precipitation_1hr_p90':              ppt_p90,
        'temperature_2m_p10':                       t2m_p10,
        'temperature_2m_p50':                       t2m_p50,
        'temperature_2m_p90':                       t2m_p90,
        'u_component_of_wind_10m_p50':              u10_p50,
        'v_component_of_wind_10m_p50':              v10_p50,
        'wind_speed_10m_p10':                       w10_p10,
        'wind_speed_10m_p50':                       w10_p50,
        'wind_speed_10m_p90':                       w10_p90,
        'u_component_of_wind_100m_p50':             u100_p50,
        'v_component_of_wind_100m_p50':             v100_p50,
        'wind_speed_100m_p50':                      w100_p50,
        'surface_solar_radiation_downwards_1hr_p50': rad_p50,
        'total_cloud_cover_p50':                    cld_p50
    }
    zip_out = guardar_zarr_estandar(model_id, init_val, leads_td, lats_asc, lons_360, campos, cfg)
    return {'model_id': model_id, 'init_time': str(init_val)[:19], 'steps': len(leads_td), 'zip': zip_out, **cfg}

#%% RECORTE DE ECMWF IFS HRES 0.1° (ARRAYLAKE CON FALLBACK AUTOMÁTICO A GCS OPEN DATA)
def procesar_ecmwf_ifs_hres(model_id, cfg):
    req_vars = ['2t', 'tp', '10u', '10v', '100u', '100v', 'ssrd', 'lcc', 'mcc', 'hcc']
    try:
        from arraylake import Client
        from xarray import open_dataset

        print(f'\n[{model_id}] Conectando a Arraylake: {cfg["repo_arraylake"]}...', flush=True)
        client  = Client()
        repo    = client.get_repo(cfg['repo_arraylake'])
        session = repo.readonly_session(branch='main')
        ds      = open_dataset(session.store, engine='zarr', chunks={})

        t_idx = -1
        for idx in [-1, -2, -3, -4]:
            v_chk = ds['2t'].isel(time=idx, step=-1).sel(latitude=4.6, longitude=-74.0, method='nearest').values
            if not isnan(v_chk).all():
                t_idx = idx
                break

        init_dt64 = ds.time.values[t_idx]
        init_str  = str(init_dt64)[:19]
        print(f'[{model_id}] Corrida activa seleccionada (Arraylake): {init_str} UTC', flush=True)

        sub = ds[req_vars].isel(time=t_idx).sel(
            latitude=slice(lat_max, lat_min),
            longitude=slice(lon_min, lon_max)
        ).compute()

        sub      = sub.isel(latitude=slice(None, None, -1))
        lats_asc = sub.latitude.values.astype(float32)
        lons_360 = (sub.longitude.values + 360.0).astype(float32)
        leads_td = sub.step.values[1:].astype('timedelta64[ns]')
        step_h   = (sub.step.values.astype('timedelta64[s]').astype(float)) / 3600.0
        raw_map  = {v: sub[v].values.astype(float32) for v in req_vars}
    except Exception as e_al:
        print(f'[{model_id}] Arraylake no disponible ({e_al}). Usando gs://ecmwf-open-data (0.1°)...', flush=True)
        from obstore import get as obs_get, get_range as obs_range
        from obstore.store import GCSStore

        store    = GCSStore(bucket='ecmwf-open-data', skip_signature=True)
        ahora    = datetime.now(timezone.utc)
        steps_h  = list(range(0, 145, 3)) + list(range(150, 361, 6))
        pref_run = None
        init_iso = None
        for delta_h in [6, 12, 18, 24, 30]:
            t_ev   = ahora - timedelta(hours=delta_h)
            c_str  = '12' if t_ev.hour >= 12 else '00'
            p_cand = f'{t_ev:%Y%m%d}/{c_str}z/ifs/0p1/oper/{t_ev:%Y%m%d}{c_str}0000'
            try:
                obs_get(store, f'{p_cand}-360h-oper-fc-sfc.index')
                pref_run = p_cand
                init_iso = f'{t_ev:%Y-%m-%d}T{c_str}:00:00'
                break
            except Exception:
                continue

        if pref_run is None:
            raise RuntimeError('No se encontró corrida completa de 360h en gs://ecmwf-open-data.')

        init_str  = init_iso
        init_dt64 = array([init_iso], dtype='datetime64[ns]')[0]
        print(f'[{model_id}] Corrida activa seleccionada (GCS Open Data 0.1°): {init_str} UTC', flush=True)

        def leer_paso_hres(h):
            p_step  = f'{pref_run}-{h}h-oper-fc-sfc'
            idx_txt = bytes(obs_get(store, f'{p_step}.index').bytes()).decode()
            meta    = {d['param']: (d['_offset'], d['_length']) for l in idx_txt.splitlines() if l.strip() for d in [loads(l)] if d.get('param') in req_vars}
            out_h   = {}
            for v in req_vars:
                if v in meta:
                    off, tam = meta[v]
                    buf      = bytes(obs_range(store, f'{p_step}.grib2', start=off, end=off + tam))
                    out_h[v] = parse_grib_array(buf, 0).reshape((1801, 3600))[735:951, 950:1201][::-1, :].astype(float32)
                else:
                    out_h[v] = zeros((216, 251), dtype=float32)
            try:
                p_pl   = f'{pref_run}-{h}h-oper-fc-pl'
                pl_txt = bytes(obs_get(store, f'{p_pl}.index').bytes()).decode()
                for l in pl_txt.splitlines():
                    if not l.strip():
                        continue
                    d = loads(l)
                    if d.get('param') in ('u', 'v') and d.get('levelist') in ('850', '500'):
                        buf = bytes(obs_range(store, f'{p_pl}.grib2', start=d['_offset'], end=d['_offset'] + d['_length']))
                        out_h[f"{d['param']}{d['levelist']}"] = parse_grib_array(buf, 0).reshape((1801, 3600))[735:951, 950:1201][::-1, :].astype(float32)
            except Exception:
                pass
            return out_h

        with ThreadPoolExecutor(max_workers=12) as pool:
            lista_pasos = list(pool.map(leer_paso_hres, steps_h))

        lats_asc = arange(lat_min, lat_max + 0.01, 0.1, dtype=float32)[:216]
        lons_360 = (arange(lon_min, lon_max + 0.01, 0.1, dtype=float32)[:251] + 360.0).astype(float32)
        leads_td = array([timedelta64(h, 'h') for h in steps_h[1:]], dtype='timedelta64[ns]')
        step_h   = array(steps_h, dtype=float)
        pl_keys  = [k for k in ('u850', 'v850', 'u500', 'v500') if all(k in p for p in lista_pasos)]
        raw_map  = {v: array([p[v] for p in lista_pasos], dtype=float32) for v in req_vars + pl_keys}

    diff_h = diff(step_h)
    t2m_k  = raw_map['2t'][1:]
    u10    = raw_map['10u'][1:]
    v10    = raw_map['10v'][1:]
    w10    = hypot(u10, v10).astype(float32)
    u100   = raw_map['100u'][1:]
    v100   = raw_map['100v'][1:]
    w100   = hypot(u100, v100).astype(float32)

    tp_diff  = clip(diff(raw_map['tp'], axis=0), 0.0, None)
    ppt_rate = (tp_diff / diff_h[:, None, None]).astype(float32)

    ssrd_diff = clip(diff(raw_map['ssrd'], axis=0), 0.0, None)
    ssrd_rate = (ssrd_diff / diff_h[:, None, None]).astype(float32)

    lcc = clip(raw_map['lcc'][1:], 0.0, 1.0)
    mcc = clip(raw_map['mcc'][1:], 0.0, 1.0)
    hcc = clip(raw_map['hcc'][1:], 0.0, 1.0)
    tcc = (1.0 - (1.0 - lcc) * (1.0 - mcc) * (1.0 - hcc)).astype(float32)

    campos = {
        'total_precipitation_1hr_p10':              ppt_rate,
        'total_precipitation_1hr_p50':              ppt_rate,
        'total_precipitation_1hr_p90':              ppt_rate,
        'temperature_2m_p10':                       t2m_k,
        'temperature_2m_p50':                       t2m_k,
        'temperature_2m_p90':                       t2m_k,
        'u_component_of_wind_10m_p50':              u10,
        'v_component_of_wind_10m_p50':              v10,
        'wind_speed_10m_p10':                       w10,
        'wind_speed_10m_p50':                       w10,
        'wind_speed_10m_p90':                       w10,
        'u_component_of_wind_100m_p50':             u100,
        'v_component_of_wind_100m_p50':             v100,
        'wind_speed_100m_p50':                      w100,
        'surface_solar_radiation_downwards_1hr_p50': ssrd_rate,
        'total_cloud_cover_p50':                    tcc
    }
    for lev in ('850', '500'):
        if f'u{lev}' in raw_map and f'v{lev}' in raw_map:
            campos[f'u_component_of_wind_{lev}hpa_p50'] = raw_map[f'u{lev}'][1:]
            campos[f'v_component_of_wind_{lev}hpa_p50'] = raw_map[f'v{lev}'][1:]
    zip_out = guardar_zarr_estandar(model_id, init_dt64, leads_td, lats_asc, lons_360, campos, cfg)
    return {'model_id': model_id, 'init_time': init_str, 'steps': len(leads_td), 'zip': zip_out, **cfg}

#%% RECORTE DE CHIRPS-GEFS V3 (UCSB CHC, 0.05° DIARIO 16 DÍAS)
def procesar_chirps_gefs(model_id, cfg):
    print(f'\n[{model_id}] Buscando última corrida diaria en data.chc.ucsb.edu...', flush=True)
    ahora      = datetime.now(timezone.utc)
    fecha_base = None
    for delta_d in range(0, 5):
        cand  = ahora - timedelta(days=delta_d)
        u_chk = f'https://data.chc.ucsb.edu/products/CHIRPS-GEFS/v3/daily/global/{cand:%Y/%m/%d}/c3g_{cand:%Y.%m.%d}.tif'
        try:
            urlopen(Request(u_chk, method='HEAD'), timeout=10)
            fecha_base = cand.replace(hour=0, minute=0, second=0, microsecond=0)
            break
        except Exception:
            continue

    if fecha_base is None:
        raise RuntimeError('No se encontró corrida reciente de CHIRPS-GEFS v3.')

    print(f'[{model_id}] Corrida activa: {fecha_base:%Y-%m-%d}', flush=True)

    def leer_dia_chirps(d_idx):
        f_val = fecha_base + timedelta(days=d_idx)
        url_t = f'/vsicurl/https://data.chc.ucsb.edu/products/CHIRPS-GEFS/v3/daily/global/{fecha_base:%Y/%m/%d}/c3g_{f_val:%Y.%m.%d}.tif'
        with rio_open(url_t) as src:
            win = from_bounds(lon_min, lat_min, lon_max, lat_max, src.transform)
            arr = src.read(1, window=win).astype(float32)
            arr[arr < 0] = 0.0
            return flipud(arr) / 1000.0

    with ThreadPoolExecutor(max_workers=8) as pool:
        capas_ppt = list(pool.map(leer_dia_chirps, range(16)))

    h_w, w_w  = capas_ppt[0].shape
    lats_asc  = arange(lat_min, lat_max, (lat_max - lat_min) / h_w, dtype=float32)[:h_w]
    lons_360  = (arange(lon_min, lon_max, (lon_max - lon_min) / w_w, dtype=float32)[:w_w] + 360.0)
    leads_td  = [timedelta64((d_idx + 1) * 24, 'h') for d_idx in range(16)]
    ppt_arr   = array(capas_ppt, dtype=float32)
    ceros     = zeros(ppt_arr.shape, dtype=float32)
    temp_def  = ceros + 293.15

    campos = {
        'total_precipitation_1hr_p10':              ppt_arr,
        'total_precipitation_1hr_p50':              ppt_arr,
        'total_precipitation_1hr_p90':              ppt_arr,
        'temperature_2m_p10':                       temp_def,
        'temperature_2m_p50':                       temp_def,
        'temperature_2m_p90':                       temp_def,
        'u_component_of_wind_10m_p50':              ceros,
        'v_component_of_wind_10m_p50':              ceros,
        'wind_speed_10m_p10':                       ceros,
        'wind_speed_10m_p50':                       ceros,
        'wind_speed_10m_p90':                       ceros,
        'u_component_of_wind_100m_p50':             ceros,
        'v_component_of_wind_100m_p50':             ceros,
        'wind_speed_100m_p50':                      ceros,
        'surface_solar_radiation_downwards_1hr_p50': ceros,
        'total_cloud_cover_p50':                    ceros
    }
    init_dt64 = array([fecha_base.strftime('%Y-%m-%dT00:00:00')], dtype='datetime64[ns]')[0]
    zip_out   = guardar_zarr_estandar(model_id, init_dt64, leads_td, lats_asc, lons_360, campos, cfg)
    return {'model_id': model_id, 'init_time': str(init_dt64)[:19], 'steps': len(leads_td), 'zip': zip_out, **cfg}

#%% RECORTE DE DWD ICON GLOBAL (MALLA ICOSAÉDRICA -> 0.125° COLOMBIA)
def procesar_dwd_icon(model_id, cfg):
    print(f'\n[{model_id}] Consultando última corrida en opendata.dwd.de...', flush=True)
    ahora     = datetime.now(timezone.utc)
    ciclo_sel = None
    fecha_str = None
    for delta_h in [4, 10, 16, 22]:
        t_ev  = ahora - timedelta(hours=delta_h)
        c_str = '12' if t_ev.hour >= 12 else '00'
        f_str = f'{t_ev:%Y%m%d}{c_str}'
        u_chk = f'https://opendata.dwd.de/weather/nwp/icon/grib/{c_str}/t_2m/icon_global_icosahedral_single-level_{f_str}_180_T_2M.grib2.bz2'
        try:
            urlopen(Request(u_chk, method='HEAD'), timeout=10)
            ciclo_sel = c_str
            fecha_str = f_str
            break
        except Exception:
            continue

    if ciclo_sel is None:
        raise RuntimeError('No se encontró corrida completa de DWD ICON Global.')

    print(f'[{model_id}] Corrida activa: {fecha_str}Z', flush=True)
    u_lat = f'https://opendata.dwd.de/weather/nwp/icon/grib/{ciclo_sel}/clat/icon_global_icosahedral_time-invariant_{fecha_str}_CLAT.grib2.bz2'
    u_lon = f'https://opendata.dwd.de/weather/nwp/icon/grib/{ciclo_sel}/clon/icon_global_icosahedral_time-invariant_{fecha_str}_CLON.grib2.bz2'
    clat  = parse_grib_array(decompress(urlopen(u_lat, timeout=20).read()), 0)
    clon  = ((parse_grib_array(decompress(urlopen(u_lon, timeout=20).read()), 0) + 180.0) % 360.0) - 180.0
    mask  = (clat >= lat_min - 0.5) & (clat <= lat_max + 0.5) & (clon >= lon_min - 0.5) & (clon <= lon_max + 0.5)
    idx_c = where(mask)[0]

    lats_asc     = arange(lat_min, lat_max + 0.001, 0.125, dtype=float32)
    lons_reg     = arange(lon_min, lon_max + 0.001, 0.125, dtype=float32)
    lons_360     = (lons_reg + 360.0).astype(float32)
    lon_g, lat_g = meshgrid(lons_reg, lats_asc)
    tree         = cKDTree(column_stack([clat[idx_c], clon[idx_c]]))
    _, nn_idx    = tree.query(column_stack([lat_g.ravel(), lon_g.ravel()]))
    map_idx      = idx_c[nn_idx]
    shape_2d     = lat_g.shape

    horas_paso = list(range(3, 181, 3))
    leads_td   = [timedelta64(h, 'h') for h in horas_paso]

    def descargar_serie_icon(var_dir, var_mayus, lev=None):
        def leer_hora(h):
            pref = f'pressure-level_{fecha_str}_{h:03d}_{lev}_{var_mayus}' if lev else f'single-level_{fecha_str}_{h:03d}_{var_mayus}'
            u_g  = f'https://opendata.dwd.de/weather/nwp/icon/grib/{ciclo_sel}/{var_dir}/icon_global_icosahedral_{pref}.grib2.bz2'
            raw  = parse_grib_array(decompress(urlopen(u_g, timeout=25).read()), 0)
            return raw[map_idx].reshape(shape_2d).astype(float32)
        with ThreadPoolExecutor(max_workers=12) as pool:
            serie = list(pool.map(leer_hora, horas_paso))
        return array(serie, dtype=float32)

    tot_prec            = descargar_serie_icon('tot_prec', 'TOT_PREC')
    ppt_paso            = zeros(tot_prec.shape, dtype=float32)
    ppt_paso[0]         = tot_prec[0] / 3.0
    ppt_paso[1:]        = (tot_prec[1:] - tot_prec[:-1]) / 3.0
    ppt_paso[ppt_paso < 0] = 0.0
    ppt_m               = ppt_paso / 1000.0

    t2m_k    = descargar_serie_icon('t_2m', 'T_2M')
    u10      = descargar_serie_icon('u_10m', 'U_10M')
    v10      = descargar_serie_icon('v_10m', 'V_10M')
    w10      = hypot(u10, v10)
    cld_frac = descargar_serie_icon('clct', 'CLCT') / 100.0
    # Radiación global superficial descendente real (GHI = Directa + Difusa):
    # En DWD OpenData: ASWDIR_S (directa) + ASWDIFD_S (difusa) en W/m2.
    # ASOB_S era radiación NETA (restando albedo), por eso daba ~530 W/m2 en vez de ~900 W/m2.
    try:
        aswdir_s  = descargar_serie_icon('aswdir_s', 'ASWDIR_S')
        aswdifd_s = descargar_serie_icon('aswdifd_s', 'ASWDIFD_S')
        rad_ghi_s = (aswdir_s + aswdifd_s) * 3600.0
    except Exception:
        # Fallback a ASOB_S si alguna de las componentes no está disponible
        rad_ghi_s = descargar_serie_icon('asob_s', 'ASOB_S') * 3600.0

    campos = {
        'total_precipitation_1hr_p10':              ppt_m,
        'total_precipitation_1hr_p50':              ppt_m,
        'total_precipitation_1hr_p90':              ppt_m,
        'temperature_2m_p10':                       t2m_k,
        'temperature_2m_p50':                       t2m_k,
        'temperature_2m_p90':                       t2m_k,
        'u_component_of_wind_10m_p50':              u10,
        'v_component_of_wind_10m_p50':              v10,
        'wind_speed_10m_p10':                       w10,
        'wind_speed_10m_p50':                       w10,
        'wind_speed_10m_p90':                       w10,
        'u_component_of_wind_100m_p50':             u10,
        'v_component_of_wind_100m_p50':             v10,
        'wind_speed_100m_p50':                      w10,
        'surface_solar_radiation_downwards_1hr_p50': rad_ghi_s,
        'total_cloud_cover_p50':                    cld_frac
    }
    for lev in (850, 500):
        try:
            campos[f'u_component_of_wind_{lev}hpa_p50'] = descargar_serie_icon('u', 'U', lev=lev)
            campos[f'v_component_of_wind_{lev}hpa_p50'] = descargar_serie_icon('v', 'V', lev=lev)
        except Exception:
            pass
    init_iso  = f'{fecha_str[:4]}-{fecha_str[4:6]}-{fecha_str[6:8]}T{ciclo_sel}:00:00'
    init_dt64 = array([init_iso], dtype='datetime64[ns]')[0]
    zip_out   = guardar_zarr_estandar(model_id, init_dt64, leads_td, lats_asc, lons_360, campos, cfg)
    return {'model_id': model_id, 'init_time': init_iso, 'steps': len(leads_td), 'zip': zip_out, **cfg}

#%% RECORTE DE MODELOS IA DE NOAA OAR MLWP (GRAPHCAST, AURORA, FOURCASTNET V2, PANGU-WEATHER)
def procesar_mlwp_noaa(model_id, cfg):
    code     = cfg['mlwp_code']
    print(f'\n[{model_id}] Consultando última corrida en s3://noaa-oar-mlwp-data/{code}...', flush=True)
    ahora    = datetime.now(timezone.utc)
    url_nc   = None
    init_iso = None
    for delta_h in [4, 10, 16, 22, 28]:
        t_ev   = ahora - timedelta(hours=delta_h)
        c_str  = '12' if t_ev.hour >= 12 else '00'
        u_cand = f'https://noaa-oar-mlwp-data.s3.amazonaws.com/{code}/{t_ev:%Y}/{t_ev:%m%d}/{code}_{t_ev:%Y%m%d}{c_str}_f000_f240_06.nc'
        try:
            urlopen(Request(u_cand, method='HEAD'), timeout=10)
            url_nc   = u_cand
            init_iso = f'{t_ev:%Y-%m-%d}T{c_str}:00:00'
            break
        except Exception:
            continue

    if url_nc is None:
        raise RuntimeError(f'No se encontró corrida reciente de {code} en NOAA OAR.')

    print(f'[{model_id}] Extrayendo ventana de Colombia vía HDF5 desde {url_nc}...', flush=True)
    fs = filesystem('https', block_size=4194304)
    with fs.open(url_nc) as f_obj:
        with File(f_obj, 'r') as hf:
            lats_raw = hf['latitude'][294:381]
            lons_raw = hf['longitude'][1100:1201]
            t2m_raw  = hf['t2'][1:, 294:381, 1100:1201]
            u10_raw  = hf['u10'][1:, 294:381, 1100:1201]
            v10_raw  = hf['v10'][1:, 294:381, 1100:1201]
            apcp_raw = hf['apcp'][1:, 294:381, 1100:1201] if 'apcp' in hf else None
            u100_raw = hf['u100'][1:, 294:381, 1100:1201] if 'u100' in hf else None
            v100_raw = hf['v100'][1:, 294:381, 1100:1201] if 'v100' in hf else None
            levs     = list(hf['level'][:]) if 'level' in hf else []
            pl_raw   = {}
            if 'u' in hf and 'v' in hf:
                for lev in (850, 500):
                    if lev in levs:
                        il = levs.index(lev)
                        pl_raw[f'u{lev}'] = hf['u'][1:, il, 294:381, 1100:1201]
                        pl_raw[f'v{lev}'] = hf['v'][1:, il, 294:381, 1100:1201]

    lats_asc = lats_raw[::-1].astype(float32)
    lons_360 = lons_raw.astype(float32)
    t2m_k    = nan_to_num(t2m_raw[:, ::-1, :], nan=293.15).astype(float32)
    u10      = nan_to_num(u10_raw[:, ::-1, :], nan=0.0).astype(float32)
    v10      = nan_to_num(v10_raw[:, ::-1, :], nan=0.0).astype(float32)
    w10      = hypot(u10, v10)
    u100     = nan_to_num(u100_raw[:, ::-1, :], nan=0.0).astype(float32) if u100_raw is not None else u10
    v100     = nan_to_num(v100_raw[:, ::-1, :], nan=0.0).astype(float32) if v100_raw is not None else v10
    w100     = hypot(u100, v100)
    ceros    = zeros(t2m_k.shape, dtype=float32)
    ppt_m    = (nan_to_num(apcp_raw[:, ::-1, :], nan=0.0) / 6.0).astype(float32) if apcp_raw is not None else ceros

    n_pasos  = t2m_k.shape[0]
    leads_td = [timedelta64((i + 1) * 6, 'h') for i in range(n_pasos)]

    campos = {
        'total_precipitation_1hr_p10':              ppt_m,
        'total_precipitation_1hr_p50':              ppt_m,
        'total_precipitation_1hr_p90':              ppt_m,
        'temperature_2m_p10':                       t2m_k,
        'temperature_2m_p50':                       t2m_k,
        'temperature_2m_p90':                       t2m_k,
        'u_component_of_wind_10m_p50':              u10,
        'v_component_of_wind_10m_p50':              v10,
        'wind_speed_10m_p10':                       w10,
        'wind_speed_10m_p50':                       w10,
        'wind_speed_10m_p90':                       w10,
        'u_component_of_wind_100m_p50':             u100,
        'v_component_of_wind_100m_p50':             v100,
        'wind_speed_100m_p50':                      w100,
        'surface_solar_radiation_downwards_1hr_p50': ceros,
        'total_cloud_cover_p50':                    ceros
    }
    for k, arr_pl in pl_raw.items():
        campos[f'{k[0]}_component_of_wind_{k[1:]}hpa_p50'] = nan_to_num(arr_pl[:, ::-1, :], nan=0.0).astype(float32)
    init_dt64 = array([init_iso], dtype='datetime64[ns]')[0]
    zip_out   = guardar_zarr_estandar(model_id, init_dt64, leads_td, lats_asc, lons_360, campos, cfg)
    return {'model_id': model_id, 'init_time': init_iso, 'steps': len(leads_td), 'zip': zip_out, **cfg}

#%% RECORTE DE VAISALA XWEATHER FORECAST API (11x13 MALLA -> INTERP 0.25°, 360H)
def procesar_xweather(model_id, cfg):
    cid = getenv('XWEATHER_CLIENT_ID', '')
    sec = getenv('XWEATHER_CLIENT_SECRET', '')
    if not cid or not sec:
        raise RuntimeError('Credenciales XWEATHER_CLIENT_ID / XWEATHER_CLIENT_SECRET no configuradas.')

    lats_c = linspace(lat_min, lat_max, 11)
    lons_c = linspace(lon_min, lon_max, 13)
    fields = 'periods.timestamp,periods.tempC,periods.precipMM,periods.windSpeedMPS,periods.windDirDEG,periods.windSpeed80mMPS,periods.windDir80mDEG,periods.solradWM2,periods.sky'

    print(f'\n[{model_id}] Consultando malla {len(lats_c)}x{len(lons_c)} (143 pts, 360h) en Vaisala Xweather...', flush=True)
    malla_raw = {}
    for i, la in enumerate(lats_c):
        for j, lo in enumerate(lons_c):
            url = f'https://data.api.xweather.com/forecasts/{la:.3f},{lo:.3f}?filter=1hr&limit=360&fields={fields}&client_id={cid}&client_secret={sec}'
            for intento in range(3):
                try:
                    with urlopen(Request(url), timeout=15) as r:
                        body = loads(r.read().decode())
                    if body.get('success') and body.get('response'):
                        malla_raw[(i, j)] = body['response'][0].get('periods', [])
                        break
                except Exception:
                    sleep(2.0 * (intento + 1))
            sleep(0.68)

    if len(malla_raw) < 100:
        raise RuntimeError(f'Respuestas insuficientes de Xweather: {len(malla_raw)}/143 puntos.')

    n_pasos  = min(len(p) for p in malla_raw.values() if p)
    primer_p = next(p for p in malla_raw.values() if p)[0]
    init_dt  = datetime.fromtimestamp(primer_p['timestamp'] - 3600, tz=timezone.utc).replace(minute=0, second=0, microsecond=0)
    init_iso = init_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    shape_c  = (n_pasos, len(lats_c), len(lons_c))
    raw_t2m  = full(shape_c, nan, dtype=float32)
    raw_ppt  = full(shape_c, nan, dtype=float32)
    raw_u10  = full(shape_c, nan, dtype=float32)
    raw_v10  = full(shape_c, nan, dtype=float32)
    raw_u80  = full(shape_c, nan, dtype=float32)
    raw_v80  = full(shape_c, nan, dtype=float32)
    raw_rad  = full(shape_c, nan, dtype=float32)
    raw_cld  = full(shape_c, nan, dtype=float32)

    for (i, j), periods in malla_raw.items():
        for k in range(n_pasos):
            p = periods[k]
            t2m_val = p.get('tempC')
            if t2m_val is not None:
                raw_t2m[k, i, j] = float(t2m_val) + 273.15
            ppt_val = p.get('precipMM')
            if ppt_val is not None:
                raw_ppt[k, i, j] = max(0.0, float(ppt_val)) / 1000.0
            w10_val = p.get('windSpeedMPS')
            d10_val = p.get('windDirDEG')
            if w10_val is not None and d10_val is not None:
                w10 = float(w10_val)
                d10 = deg2rad(float(d10_val))
                raw_u10[k, i, j] = -w10 * sin(d10)
                raw_v10[k, i, j] = -w10 * cos(d10)
            w80_val = p.get('windSpeed80mMPS') if p.get('windSpeed80mMPS') is not None else w10_val
            d80_val = p.get('windDir80mDEG') if p.get('windDir80mDEG') is not None else d10_val
            if w80_val is not None and d80_val is not None:
                w80 = float(w80_val)
                d80 = deg2rad(float(d80_val))
                raw_u80[k, i, j] = -w80 * sin(d80)
                raw_v80[k, i, j] = -w80 * cos(d80)
            rad_val = p.get('solradWM2')
            if rad_val is not None:
                raw_rad[k, i, j] = max(0.0, float(rad_val)) * 3600.0
            cld_val = p.get('sky')
            if cld_val is not None:
                raw_cld[k, i, j] = clip(float(cld_val) / 100.0, 0.0, 1.0)

    coords_c = {'lead': arange(n_pasos), 'lat_0p1': lats_c, 'lon_0p1': lons_c}
    dims_c   = ('lead', 'lat_0p1', 'lon_0p1')
    ds_c     = Dataset({
        't2m': (dims_c, raw_t2m), 'ppt': (dims_c, raw_ppt),
        'u10': (dims_c, raw_u10), 'v10': (dims_c, raw_v10),
        'u80': (dims_c, raw_u80), 'v80': (dims_c, raw_v80),
        'rad': (dims_c, raw_rad), 'cld': (dims_c, raw_cld)
    }, coords=coords_c)
    if len(malla_raw) < len(lats_c) * len(lons_c):
        ds_c = ds_c.interpolate_na(dim='lon_0p1', method='linear').interpolate_na(dim='lat_0p1', method='linear')

    lats_025 = arange(lat_min, lat_max + 0.01, 0.25, dtype=float32)
    lons_025 = arange(lon_min, lon_max + 0.01, 0.25, dtype=float32)
    ds_i     = ds_c.interp(lat_0p1=lats_025, lon_0p1=lons_025, method='linear')

    u10_i  = ds_i['u10'].values.astype(float32)
    v10_i  = ds_i['v10'].values.astype(float32)
    w10_i  = hypot(u10_i, v10_i).astype(float32)
    u80_i  = ds_i['u80'].values.astype(float32)
    v80_i  = ds_i['v80'].values.astype(float32)
    w80_i  = hypot(u80_i, v80_i).astype(float32)
    t2m_i  = ds_i['t2m'].values.astype(float32)
    ppt_i  = ds_i['ppt'].values.astype(float32)
    rad_i  = ds_i['rad'].values.astype(float32)
    cld_i  = ds_i['cld'].values.astype(float32)

    leads_td = [timedelta64(k + 1, 'h') for k in range(n_pasos)]
    campos   = {
        'total_precipitation_1hr_p10':              ppt_i,
        'total_precipitation_1hr_p50':              ppt_i,
        'total_precipitation_1hr_p90':              ppt_i,
        'temperature_2m_p10':                       t2m_i,
        'temperature_2m_p50':                       t2m_i,
        'temperature_2m_p90':                       t2m_i,
        'u_component_of_wind_10m_p50':              u10_i,
        'v_component_of_wind_10m_p50':              v10_i,
        'wind_speed_10m_p10':                       w10_i,
        'wind_speed_10m_p50':                       w10_i,
        'wind_speed_10m_p90':                       w10_i,
        'u_component_of_wind_100m_p50':             u80_i,
        'v_component_of_wind_100m_p50':             v80_i,
        'wind_speed_100m_p50':                      w80_i,
        'surface_solar_radiation_downwards_1hr_p50': rad_i,
        'total_cloud_cover_p50':                    cld_i
    }
    init_dt64 = array([init_iso], dtype='datetime64[ns]')[0]
    zip_out   = guardar_zarr_estandar(model_id, init_dt64, leads_td, lats_025, lons_025 + 360.0, campos, cfg)
    return {'model_id': model_id, 'init_time': init_iso, 'steps': len(leads_td), 'zip': zip_out, **cfg}

def procesar_ideam_wrf(model_id, cfg):
    sesion   = Session()
    url_base = 'https://bart.ideam.gov.co/wrfideam/new_modelo/WRF00COLOMBIA/netcdf/'
    def fetch_range(url, start, length):
        for intento in range(5):
            try:
                r = sesion.get(url, headers={'Range': f'bytes={start}-{start + length - 1}'}, timeout=30)
                r.raise_for_status()
                return r.content
            except Exception:
                if intento == 4:
                    raise
                sleep(3 * (intento + 1))

    html     = sesion.get(url_base, timeout=25).text
    archivos = sorted(set(findall(r'wrfout_d01_\d{4}-\d{2}-\d{2}_\d{2}:00:00', html)))
    if len(archivos) < 24:
        raise RuntimeError(f'Archivos wrfout_d01 insuficientes en WRF00: {len(archivos)}.')

    hdr      = fetch_range(f'{url_base}{archivos[0]}', 0, 65536)
    ver      = hdr[3]
    pos      = 8
    rd_u32   = lambda b, p: (unpack('>I', b[p:p + 4])[0], p + 4)
    def rd_str(b, p):
        n, p = rd_u32(b, p)
        return b[p:p + n].decode('utf-8', 'replace'), p + n + ((4 - (n % 4)) % 4)
    def skip_attrs(b, p):
        tag, p = rd_u32(b, p)
        if tag == 0:
            return rd_u32(b, p)[1]
        cnt, p = rd_u32(b, p)
        for _ in range(cnt):
            _, p      = rd_str(b, p)
            nct, p    = rd_u32(b, p)
            nelems, p = rd_u32(b, p)
            sz        = {1: 1, 2: 1, 3: 2, 4: 4, 5: 4, 6: 8}[nct] * nelems
            p        += sz + ((4 - (sz % 4)) % 4)
        return p

    tag, pos = rd_u32(hdr, pos)
    dims     = []
    if tag == 10:
        ndims, pos = rd_u32(hdr, pos)
        for _ in range(ndims):
            dn, pos = rd_str(hdr, pos)
            dl, pos = rd_u32(hdr, pos)
            dims.append((dn, dl))
    else:
        pos += 4
    d_map      = dict(dims)
    ny_w, nx_w = d_map['south_north'], d_map['west_east']
    pos        = skip_attrs(hdr, pos)
    tag, pos   = rd_u32(hdr, pos)
    nvars, pos = rd_u32(hdr, pos)
    vm         = {}
    for _ in range(nvars):
        vn, pos = rd_str(hdr, pos)
        nd, pos = rd_u32(hdr, pos)
        for _ in range(nd):
            _, pos = rd_u32(hdr, pos)
        pos        = skip_attrs(hdr, pos)
        _, pos     = rd_u32(hdr, pos)
        vsize, pos = rd_u32(hdr, pos)
        b_sz       = 8 if ver == 2 else 4
        begin      = unpack('>Q' if ver == 2 else '>I', hdr[pos:pos + b_sz])[0]
        pos       += b_sz
        vm[vn]     = {'vsize': vsize, 'begin': begin}

    init_dt  = datetime.strptime(archivos[0].replace('wrfout_d01_', ''), '%Y-%m-%d_%H:%M:%S').replace(tzinfo=timezone.utc)
    init_iso = init_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    numrecs  = len(archivos)
    print(f'[{model_id}] Usando WRF00 ({init_iso}, {numrecs - 1} pasos horarios)...', flush=True)

    sz         = vm['XLAT']['vsize']
    geo        = fetch_range(f'{url_base}{archivos[0]}', vm['XLAT']['begin'], (vm['XLONG']['begin'] + sz) - vm['XLAT']['begin'])
    xlat       = frombuffer(geo[:sz], dtype='>f4')
    xlon       = frombuffer(geo[vm['XLONG']['begin'] - vm['XLAT']['begin']:vm['XLONG']['begin'] - vm['XLAT']['begin'] + sz], dtype='>f4')
    lats_01    = arange(lat_min, lat_max + 0.01, 0.1, dtype=float32)
    lons_01    = arange(lon_min, lon_max + 0.01, 0.1, dtype=float32)
    glon, glat = meshgrid(lons_01, lats_01)
    dist, idx_nn = cKDTree(column_stack([xlat, xlon])).query(column_stack([glat.ravel(), glon.ravel()]), distance_upper_bound=0.18)
    valid      = dist < 0.18
    idx_safe   = where(valid, idx_nn, 0)
    ny_t, nx_t = len(lats_01), len(lons_01)
    regrid     = lambda src: where(valid, src[idx_safe], nan).reshape(ny_t, nx_t).astype(float32)

    b_q2, e_v10              = vm['Q2']['begin'], vm['V10']['begin'] + sz
    b_rc, e_rnc              = vm['RAINC']['begin'], vm['RAINNC']['begin'] + sz
    off_t2, off_u10, off_v10 = vm['T2']['begin'] - b_q2, vm['U10']['begin'] - b_q2, vm['V10']['begin'] - b_q2
    off_rsh, off_rnc         = vm['RAINSH']['begin'] - b_rc, vm['RAINNC']['begin'] - b_rc
    nk_pl                    = 19
    sz_u, sz_v, sz_p         = nk_pl * ny_w * (nx_w + 1) * 4, nk_pl * (ny_w + 1) * nx_w * 4, nk_pl * ny_w * nx_w * 4
    pb_pl                    = frombuffer(fetch_range(f'{url_base}{archivos[0]}', vm['PB']['begin'], sz_p), dtype='>f4').reshape((nk_pl, ny_w, nx_w))

    def interp_pl(p_pa, arr_3d, p_obj):
        k_hi  = argmax(p_pa <= p_obj, axis=0)
        k_lo  = clip(k_hi - 1, 0, nk_pl - 2)
        p_lo  = take_along_axis(p_pa, k_lo[None], 0)[0]
        p_hi  = take_along_axis(p_pa, k_hi[None], 0)[0]
        w     = (p_obj - p_lo) / where(p_hi != p_lo, p_hi - p_lo, 1.0)
        val   = (1.0 - w) * take_along_axis(arr_3d, k_lo[None], 0)[0] + w * take_along_axis(arr_3d, k_hi[None], 0)[0]
        valid_p = (p_pa[0] >= p_obj) & (p_pa[-1] <= p_obj) & (k_hi > 0)
        return where(valid_p, val, nan).ravel()

    def leer_paso(t):
        u_f  = f'{url_base}{archivos[t]}'
        blk2 = fetch_range(u_f, b_rc, e_rnc - b_rc)
        r_ac = frombuffer(blk2[:sz], dtype='>f4') + frombuffer(blk2[off_rsh:off_rsh + sz], dtype='>f4') + frombuffer(blk2[off_rnc:off_rnc + sz], dtype='>f4')
        if t == 0:
            return (t, regrid(r_ac)) + (None,) * 8
        blk1 = fetch_range(u_f, b_q2, e_v10 - b_q2)
        sw   = frombuffer(fetch_range(u_f, vm['SWDOWN']['begin'], sz), dtype='>f4') * 3600.0
        u_3d = frombuffer(fetch_range(u_f, vm['U']['begin'], sz_u), dtype='>f4').reshape((nk_pl, ny_w, nx_w + 1))
        v_3d = frombuffer(fetch_range(u_f, vm['V']['begin'], sz_v), dtype='>f4').reshape((nk_pl, ny_w + 1, nx_w))
        p_pa = pb_pl + frombuffer(fetch_range(u_f, vm['P']['begin'], sz_p), dtype='>f4').reshape((nk_pl, ny_w, nx_w))
        u_c  = 0.5 * (u_3d[:, :, :-1] + u_3d[:, :, 1:])
        v_c  = 0.5 * (v_3d[:, :-1, :] + v_3d[:, 1:, :])
        return (t, regrid(r_ac),
                regrid(frombuffer(blk1[off_t2:off_t2 + sz], dtype='>f4')),
                regrid(frombuffer(blk1[off_u10:off_u10 + sz], dtype='>f4')),
                regrid(frombuffer(blk1[off_v10:off_v10 + sz], dtype='>f4')),
                regrid(clip(sw, 0.0, None)),
                regrid(interp_pl(p_pa, u_c, 85000.0)),
                regrid(interp_pl(p_pa, v_c, 85000.0)),
                regrid(interp_pl(p_pa, u_c, 50000.0)),
                regrid(interp_pl(p_pa, v_c, 50000.0)))

    n_out    = numrecs - 1
    shape_o  = (n_out, ny_t, nx_t)
    rain_all = zeros((numrecs, ny_t, nx_t), dtype=float32)
    t2m_all  = zeros(shape_o, dtype=float32)
    u10_all  = zeros(shape_o, dtype=float32)
    v10_all  = zeros(shape_o, dtype=float32)
    rad_all  = zeros(shape_o, dtype=float32)
    u850_all = zeros(shape_o, dtype=float32)
    v850_all = zeros(shape_o, dtype=float32)
    u500_all = zeros(shape_o, dtype=float32)
    v500_all = zeros(shape_o, dtype=float32)

    for t in range(numrecs):
        _, r_ac, t2, u10, v10, sw, u85, v85, u50, v50 = leer_paso(t)
        rain_all[t] = r_ac
        if t > 0:
            t2m_all[t - 1]  = t2
            u10_all[t - 1]  = u10
            v10_all[t - 1]  = v10
            rad_all[t - 1]  = sw
            u850_all[t - 1] = u85
            v850_all[t - 1] = v85
            u500_all[t - 1] = u50
            v500_all[t - 1] = v50
        sleep(0.08)

    ppt_all = clip(diff(rain_all, axis=0), 0.0, None).astype(float32) / 1000.0
    w10_all = hypot(u10_all, v10_all).astype(float32)
    leads_td = [timedelta64(k, 'h') for k in range(1, numrecs)]
    campos   = {
        'total_precipitation_1hr_p10':              ppt_all,
        'total_precipitation_1hr_p50':              ppt_all,
        'total_precipitation_1hr_p90':              ppt_all,
        'temperature_2m_p10':                       t2m_all,
        'temperature_2m_p50':                       t2m_all,
        'temperature_2m_p90':                       t2m_all,
        'u_component_of_wind_10m_p50':              u10_all,
        'v_component_of_wind_10m_p50':              v10_all,
        'wind_speed_10m_p10':                       w10_all,
        'wind_speed_10m_p50':                       w10_all,
        'wind_speed_10m_p90':                       w10_all,
        'u_component_of_wind_850hpa_p50':           u850_all,
        'v_component_of_wind_850hpa_p50':           v850_all,
        'u_component_of_wind_500hpa_p50':           u500_all,
        'v_component_of_wind_500hpa_p50':           v500_all,
        'surface_solar_radiation_downwards_1hr_p50': rad_all
    }
    init_dt64 = array([init_iso], dtype='datetime64[ns]')[0]
    zip_out   = guardar_zarr_estandar(model_id, init_dt64, leads_td, lats_01, lons_01 + 360.0, campos, cfg)
    return {'model_id': model_id, 'init_time': init_iso, 'steps': len(leads_td), 'zip': zip_out, **cfg}

#%% EJECUCIÓN PRINCIPAL DEL WORKER MULTIMODELO
if __name__ == '__main__':
    manifest = {'updated_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'models': {}}
    for m_id, cfg in catalogo_modelos.items():
        if filtro != 'all' and m_id not in filtro.split(','):
            continue
        try:
            if 'bucket' in cfg:
                info_m = procesar_dynamical(m_id, cfg)
            elif m_id == 'ecmwf_ifs_hres':
                info_m = procesar_ecmwf_ifs_hres(m_id, cfg)
            elif m_id == 'chirps_gefs':
                info_m = procesar_chirps_gefs(m_id, cfg)
            elif m_id == 'dwd_icon':
                info_m = procesar_dwd_icon(m_id, cfg)
            elif 'mlwp_code' in cfg:
                info_m = procesar_mlwp_noaa(m_id, cfg)
            elif cfg.get('xweather_api'):
                info_m = procesar_xweather(m_id, cfg)
            elif cfg.get('ideam_wrf'):
                info_m = procesar_ideam_wrf(m_id, cfg)
            manifest['models'][m_id] = info_m
            print(f'[✓ {m_id}] Empaquetado exitoso en {info_m["zip"]} ({info_m["steps"]} pasos).', flush=True)
        except Exception as e:
            print(f'[! {m_id}] Error al procesar fuente: {e}', flush=True)

    with open('models_manifest.json', 'w', encoding='utf-8') as fm:
        dump(manifest, fm, indent=2, ensure_ascii=False)
    print('\nManifiesto multimodelo guardado en models_manifest.json.', flush=True)
