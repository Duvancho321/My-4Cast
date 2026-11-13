"""
02_export_web_data.py — Extractor y generador de datos meteorológicos y frames para el portal web.

__author__: "Duvan Nieves"
__copyright__: "Duvan Nieves Ruiz"
__version__: "0.7.2"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves.sci@gmail.com"
__status__: "Developer"
__changues__:
    - [2026-11-08][Duvan]: Acumulado PPT con paso real (pasos variables).
    - [2026-11-06][Duvan]: Exportar institucion, familia y licencia de modelos.
    - [2026-11-05][Duvan]: Inclusión de todas las 32 capitales departamentales.
    - [2026-11-04][Duvan]: Paletas científicas y eliminación de emojis.
    - [2026-11-04][Duvan]: Radiación teórica ToA y PPT acumulada.
"""

from sys import argv, path
from pathlib import Path
path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image
from os.path import exists
from json import dump, load
from os import getenv, makedirs
from xarray import open_zarr
from pandas import to_datetime
from src.modelos import dominios_plataforma, modelos_colombia
from src.paletas import cmap_nubosidad, cmap_ppt, cmap_radiacion, cmap_temp, cmap_viento, norm_nubosidad, norm_ppt, norm_radiacion, norm_temp, norm_viento
from numpy import arctan2, array, cos, cumsum, deg2rad, diff, flipud, isnan, maximum, nan_to_num, pi, rad2deg, round, sin, timedelta64, uint8, zeros

#%% CONFIGURACIÓN DE PARÁMETROS Y RUTAS
dir_web_base = f"{getenv('MY4CAST_DATA_DIR', '/mnt/datos/dnieves/WN3')}/web_data"
makedirs(dir_web_base, exist_ok=True)

#%% CATÁLOGO DE MUNICIPIOS Y ESTACIONES PRIORITARIAS (SIN EMOJIS, FORMATO CIENTÍFICO)
estaciones = {
    'velez': {
        'nombre': 'Vélez',
        'depto': 'Santander',
        'lat': 6.0139,
        'lon': -73.6739,
        'altitud': 2050,
        'tag': 'Provincia de Vélez'
    },
    'guavata': {
        'nombre': 'Guavatá',
        'depto': 'Santander',
        'lat': 5.9264,
        'lon': -73.7153,
        'altitud': 1950,
        'tag': 'Provincia de Vélez'
    },
    'barbosa': {
        'nombre': 'Barbosa',
        'depto': 'Santander',
        'lat': 5.9322,
        'lon': -73.6178,
        'altitud': 1610,
        'tag': 'Río Suárez'
    },
    'san_gil': {
        'nombre': 'San Gil',
        'depto': 'Santander',
        'lat': 6.5561,
        'lon': -73.1369,
        'altitud': 1117,
        'tag': 'Provincia Guanentina'
    },
    'socorro': {
        'nombre': 'Socorro',
        'depto': 'Santander',
        'lat': 6.4678,
        'lon': -73.2625,
        'altitud': 1230,
        'tag': 'Provincia Comunera'
    },
    'bucaramanga': {
        'nombre': 'Bucaramanga',
        'depto': 'Santander',
        'lat': 7.1193,
        'lon': -73.1227,
        'altitud': 960,
        'tag': 'Área Metropolitana'
    },
    'chiquinquira': {
        'nombre': 'Chiquinquirá',
        'depto': 'Boyacá',
        'lat': 5.6186,
        'lon': -73.8175,
        'altitud': 2550,
        'tag': 'Occidente de Boyacá'
    },
    'tunja': {
        'nombre': 'Tunja',
        'depto': 'Boyacá',
        'lat': 5.5353,
        'lon': -73.3678,
        'altitud': 2800,
        'tag': 'Distrito Histórico'
    },
    'moniquira': {
        'nombre': 'Moniquirá',
        'depto': 'Boyacá',
        'lat': 5.8756,
        'lon': -73.5739,
        'altitud': 1669,
        'tag': 'Provincia de Ricaurte'
    },
    'villa_de_leyva': {
        'nombre': 'Villa de Leyva',
        'depto': 'Boyacá',
        'lat': 5.6322,
        'lon': -73.5244,
        'altitud': 2149,
        'tag': 'Alto Ricaurte'
    },
    'duitama': {
        'nombre': 'Duitama',
        'depto': 'Boyacá',
        'lat': 5.8267,
        'lon': -73.0336,
        'altitud': 2530,
        'tag': 'Provincia de Tundama'
    },
    'sogamoso': {
        'nombre': 'Sogamoso',
        'depto': 'Boyacá',
        'lat': 5.7144,
        'lon': -72.9339,
        'altitud': 2569,
        'tag': 'Provincia de Sugamuxi'
    },
    'san_andres': {
        'nombre': 'San Andrés',
        'depto': 'San Andrés y Providencia',
        'lat': 12.5847,
        'lon': -81.7006,
        'altitud': 2,
        'tag': 'Caribe Occidental'
    },
    'providencia': {
        'nombre': 'Providencia',
        'depto': 'San Andrés y Providencia',
        'lat': 13.3561,
        'lon': -81.3719,
        'altitud': 10,
        'tag': 'Sector Insular Norte'
    },
    'medellin': {
        'nombre': 'Medellín',
        'depto': 'Antioquia',
        'lat': 6.2442,
        'lon': -75.5812,
        'altitud': 1495,
        'tag': 'Valle de Aburrá'
    },
    'rionegro': {
        'nombre': 'Rionegro',
        'depto': 'Antioquia',
        'lat': 6.1552,
        'lon': -75.3737,
        'altitud': 2125,
        'tag': 'Oriente Antioqueño'
    },
    'apartado': {
        'nombre': 'Apartadó',
        'depto': 'Antioquia',
        'lat': 7.8833,
        'lon': -76.6333,
        'altitud': 30,
        'tag': 'Eje Bananero de Urabá'
    },
    'ibague': {
        'nombre': 'Ibagué',
        'depto': 'Tolima',
        'lat': 4.4389,
        'lon': -75.2322,
        'altitud': 1285,
        'tag': 'Piedemonte Cordillera Central'
    },
    'bogota': {
        'nombre': 'Bogotá D.C.',
        'depto': 'Cundinamarca',
        'lat': 4.7110,
        'lon': -74.0721,
        'altitud': 2640,
        'tag': 'Sabana de Bogotá'
    },
    'cali': {
        'nombre': 'Cali',
        'depto': 'Valle del Cauca',
        'lat': 3.4516,
        'lon': -76.5320,
        'altitud': 1018,
        'tag': 'Valle Geográfico del Río Cauca'
    },
    'barranquilla': {
        'nombre': 'Barranquilla',
        'depto': 'Atlántico',
        'lat': 10.9685,
        'lon': -74.7813,
        'altitud': 18,
        'tag': 'Bocadivisa del Magdalena'
    },
    'cartagena': {
        'nombre': 'Cartagena',
        'depto': 'Bolívar',
        'lat': 10.3910,
        'lon': -75.4794,
        'altitud': 2,
        'tag': 'Litoral Caribe Central'
    },
    'santa_marta': {
        'nombre': 'Santa Marta',
        'depto': 'Magdalena',
        'lat': 11.2408,
        'lon': -74.1990,
        'altitud': 6,
        'tag': 'Piedemonte Sierra Nevada'
    },
    'pereira': {
        'nombre': 'Pereira',
        'depto': 'Risaralda',
        'lat': 4.8133,
        'lon': -75.6961,
        'altitud': 1411,
        'tag': 'Vertiente Río Otún'
    },
    'manizales': {
        'nombre': 'Manizales',
        'depto': 'Caldas',
        'lat': 5.0689,
        'lon': -75.5174,
        'altitud': 2150,
        'tag': 'Piedemonte Nevado del Ruiz'
    },
    'armenia': {
        'nombre': 'Armenia',
        'depto': 'Quindío',
        'lat': 4.5339,
        'lon': -75.6811,
        'altitud': 1551,
        'tag': 'Meseta del Quindío'
    },
    'cucuta': {
        'nombre': 'Cúcuta',
        'depto': 'Norte de Santander',
        'lat': 7.8939,
        'lon': -72.5078,
        'altitud': 320,
        'tag': 'Valle del Pamplonita'
    },
    'pasto': {
        'nombre': 'Pasto',
        'depto': 'Nariño',
        'lat': 1.2136,
        'lon': -77.2811,
        'altitud': 2527,
        'tag': 'Valle de Atriz'
    },
    'popayan': {
        'nombre': 'Popayán',
        'depto': 'Cauca',
        'lat': 2.4448,
        'lon': -76.6147,
        'altitud': 1760,
        'tag': 'Valle de Pubenza'
    },
    'neiva': {
        'nombre': 'Neiva',
        'depto': 'Huila',
        'lat': 2.9273,
        'lon': -75.2819,
        'altitud': 442,
        'tag': 'Valle Alto del Magdalena'
    },
    'villavicencio': {
        'nombre': 'Villavicencio',
        'depto': 'Meta',
        'lat': 4.1420,
        'lon': -73.6266,
        'altitud': 467,
        'tag': 'Piedemonte Llanero'
    },
    'monteria': {
        'nombre': 'Montería',
        'depto': 'Córdoba',
        'lat': 8.7479,
        'lon': -75.8814,
        'altitud': 18,
        'tag': 'Valle del Sinú'
    },
    'valledupar': {
        'nombre': 'Valledupar',
        'depto': 'Cesar',
        'lat': 10.4631,
        'lon': -73.2532,
        'altitud': 168,
        'tag': 'Valle del Río Guatapurí'
    },
    'riohacha': {
        'nombre': 'Riohacha',
        'depto': 'La Guajira',
        'lat': 11.5444,
        'lon': -72.9072,
        'altitud': 5,
        'tag': 'Costa de La Guajira'
    },
    'quibdo': {
        'nombre': 'Quibdó',
        'depto': 'Chocó',
        'lat': 5.6919,
        'lon': -76.6583,
        'altitud': 43,
        'tag': 'Atrato Medio'
    },
    'leticia': {
        'nombre': 'Leticia',
        'depto': 'Amazonas',
        'lat': -4.2153,
        'lon': -69.9406,
        'altitud': 96,
        'tag': 'Trapecio Amazónico'
    },
    'florencia': {
        'nombre': 'Florencia',
        'depto': 'Caquetá',
        'lat': 1.6144,
        'lon': -75.6062,
        'altitud': 242,
        'tag': 'Piedemonte Amazónico'
    },
    'yopal': {
        'nombre': 'Yopal',
        'depto': 'Casanare',
        'lat': 5.3378,
        'lon': -72.3959,
        'altitud': 350,
        'tag': 'Piedemonte Llanero'
    },
    'arauca': {
        'nombre': 'Arauca',
        'depto': 'Arauca',
        'lat': 7.0847,
        'lon': -70.7591,
        'altitud': 125,
        'tag': 'Llanos de Arauca'
    },
    'sincelejo': {
        'nombre': 'Sincelejo',
        'depto': 'Sucre',
        'lat': 9.3047,
        'lon': -75.3978,
        'altitud': 213,
        'tag': 'Sabanas de Sucre'
    },
    'mocoa': {
        'nombre': 'Mocoa',
        'depto': 'Putumayo',
        'lat': 1.1528,
        'lon': -76.6528,
        'altitud': 604,
        'tag': 'Piedemonte de Putumayo'
    },
    'san_jose_guaviare': {
        'nombre': 'San José del Guaviare',
        'depto': 'Guaviare',
        'lat': 2.5729,
        'lon': -72.6459,
        'altitud': 175,
        'tag': 'Puerta de la Amazonía'
    },
    'inirida': {
        'nombre': 'Inírida',
        'depto': 'Guainía',
        'lat': 3.8653,
        'lon': -67.9239,
        'altitud': 100,
        'tag': 'Estrella Fluvial de Inírida'
    },
    'mitu': {
        'nombre': 'Mitú',
        'depto': 'Vaupés',
        'lat': 1.2514,
        'lon': -70.2333,
        'altitud': 183,
        'tag': 'Selva del Vaupés'
    },
    'puerto_carreno': {
        'nombre': 'Puerto Carreño',
        'depto': 'Vichada',
        'lat': 6.1890,
        'lon': -67.4859,
        'altitud': 51,
        'tag': 'Confluencia Orinoco-Meta'
    }
}

#%% EXTRACCIÓN Y SERIALIZACIÓN POR FUENTE DE PRONÓSTICO
def exportar_modelo_web(model_id, cfg):
    ruta_zarr = cfg['ruta_zarr']
    if not exists(ruta_zarr):
        return None

    salto_vec   = cfg['salto_web']
    dir_sal     = dir_web_base if model_id == 'wn3' else f'{dir_web_base}/models/{model_id}'
    dir_frames  = f'{dir_sal}/frames'
    ruta_json   = f'{dir_sal}/latest_weather.json'
    ruta_viento = f'{dir_sal}/wind_vectors.json'
    makedirs(dir_sal, exist_ok=True)
    makedirs(dir_frames, exist_ok=True)

    print(f'\n[{model_id.upper()}] Abriendo dataset en {ruta_zarr}...', flush=True)
    ds = open_zarr(ruta_zarr)

    latest = None
    for idx in range(len(ds.init_time) - 1, -1, -1):
        cand   = ds.isel(init_time=idx)
        sample = cand['temperature_2m_p50'].isel(lat_0p1=len(cand.lat_0p1) // 2, lon_0p1=len(cand.lon_0p1) // 2).values
        if not isnan(sample).all():
            if model_id != 'wn3' or (not isnan(sample).any() and len(sample) == 360):
                latest = cand
                print(f'[{model_id.upper()}] Seleccionada corrida: {str(cand.init_time.values)[:19]} UTC (índice {idx})', flush=True)
                break

    if latest is None:
        print(f'[{model_id.upper()}] No se encontró corrida válida.', flush=True)
        return None

    init_utc_raw = latest.init_time.values
    init_utc_str = str(init_utc_raw)[:19] + ' UTC'
    init_hl_raw  = init_utc_raw - timedelta64(5, 'h')
    init_hl_str  = str(init_hl_raw)[:19] + ' HL (Colombia)'

    lead_horas = [int(td / timedelta64(1, 'h')) for td in latest.lead_time.values]
    valid_hl   = [str(init_hl_raw + timedelta64(h, 'h'))[:16] for h in lead_horas]
    n_frames   = len(lead_horas)

    resultado = {
        'model_id': model_id,
        'modelo': cfg['nombre'],
        'etiqueta_corta': cfg['etiqueta_corta'],
        'etiqueta_fuente': cfg['etiqueta_fuente'],
        'carpeta_drive': cfg['carpeta'],
        'tipo': cfg['tipo'],
        'almacenamiento': cfg['almacenamiento'],
        'resolucion': cfg['resolucion'],
        'paso_h': cfg['paso_h'],
        'init_utc': init_utc_str,
        'init_hl': init_hl_str,
        'lead_hours': lead_horas,
        'valid_hl': valid_hl,
        'bounds': [[-5.0, -85.0], [16.5, -60.0]],
        'frame_hours': n_frames,
        'variables_disponibles': cfg['variables'],
        'regiones': {
            'nacional': {'nombre': 'Colombia (Nacional)', 'centro': [4.5, -73.5], 'zoom': 6},
            'santander': {'nombre': 'Santander (Vélez & Serranía)', 'centro': [6.4, -73.4], 'zoom': 8},
            'boyaca': {'nombre': 'Boyacá (Tunja & Altiplano)', 'centro': [5.7, -73.4], 'zoom': 8},
            'san_andres': {'nombre': 'Archipiélago de San Andrés', 'centro': [12.8, -81.5], 'zoom': 9},
            'antioquia': {'nombre': 'Antioquia', 'centro': [6.5, -75.5], 'zoom': 8}
        },
        'estaciones': {}
    }

    print(f'[{model_id.upper()}] Extrayendo series de tiempo para {len(estaciones)} puntos...', flush=True)
    dts      = to_datetime([init_utc_raw + timedelta64(h, 'h') for h in lead_horas])
    theta_d  = 2 * pi * (dts.day_of_year.values - 1) / 365.0
    rc_dis   = 1.00011 + 0.034221 * cos(theta_d) + 0.00128 * sin(theta_d) + 0.000719 * cos(2 * theta_d) + 0.000077 * sin(2 * theta_d)
    rc_dec   = 0.006918 - 0.39912 * cos(theta_d) + 0.070257 * sin(theta_d) - 0.006758 * cos(2 * theta_d) + 0.000907 * sin(2 * theta_d) - 0.002697 * cos(3 * theta_d) + 0.00148 * sin(3 * theta_d)
    utc_hour = dts.hour.values + dts.minute.values / 60.0

    for k, info in estaciones.items():
        lat_t = info['lat']
        lon_t = 360.0 + info['lon'] if info['lon'] < 0 else info['lon']
        pt    = latest.sel(lat_0p1=lat_t, lon_0p1=lon_t, method='nearest')
        pt_05 = latest.sel(lat_0p05=lat_t, lon_0p05=lon_t, method='nearest') if 'lat_0p05' in latest.coords else pt
        ceros_pt = zeros(n_frames, dtype=float)

        t_var = 'station_head_temperature_2m' if ('station_head_temperature_2m_p50' in latest.data_vars and not isnan(pt_05['station_head_temperature_2m_p50'].values).all()) else 'temperature_2m'
        pt_t  = pt_05 if t_var.startswith('station_head') else pt
        t2m_p50 = round(nan_to_num(pt_t[f'{t_var}_p50'].values.astype(float) - 273.15, nan=20.0), 1).tolist()
        t2m_p10 = round(nan_to_num(pt_t[f'{t_var}_p10'].values.astype(float) - 273.15, nan=15.0), 1).tolist()
        t2m_p90 = round(nan_to_num(pt_t[f'{t_var}_p90'].values.astype(float) - 273.15, nan=25.0), 1).tolist()

        ppt_p50 = round(nan_to_num(pt['total_precipitation_1hr_p50'].values.astype(float) * 1000.0, nan=0.0), 2).tolist()
        ppt_p10 = round(nan_to_num(pt['total_precipitation_1hr_p10'].values.astype(float) * 1000.0, nan=0.0), 2).tolist()
        ppt_p90 = round(nan_to_num(pt['total_precipitation_1hr_p90'].values.astype(float) * 1000.0, nan=0.0), 2).tolist()

        wspd_p50 = round(nan_to_num(pt['wind_speed_10m_p50'].values.astype(float), nan=2.0), 1).tolist()
        wspd_p10 = round(nan_to_num(pt['wind_speed_10m_p10'].values.astype(float), nan=1.0), 1).tolist()
        wspd_p90 = round(nan_to_num(pt['wind_speed_10m_p90'].values.astype(float), nan=4.0), 1).tolist()

        u    = nan_to_num(pt['u_component_of_wind_10m_p50'].values.astype(float), nan=0.0)
        v    = nan_to_num(pt['v_component_of_wind_10m_p50'].values.astype(float), nan=0.0)
        wdir = round((180 + rad2deg(arctan2(u, v))) % 360, 0).astype(int).tolist()

        rad_p50   = round(nan_to_num(pt['surface_solar_radiation_downwards_1hr_p50'].values.astype(float) / 3600.0, nan=0.0), 0).astype(int).tolist()
        cld_p50   = round(nan_to_num(pt['total_cloud_cover_p50'].values.astype(float) * 100.0, nan=50.0), 0).astype(int).tolist() if 'total_cloud_cover_p50' in pt else ceros_pt.astype(int).tolist()
        cldl_p50  = round(nan_to_num(pt['low_cloud_cover_p50'].values.astype(float) * 100.0, nan=0.0), 0).astype(int).tolist() if 'low_cloud_cover_p50' in pt else ceros_pt.astype(int).tolist()
        cldm_p50  = round(nan_to_num(pt['medium_cloud_cover_p50'].values.astype(float) * 100.0, nan=0.0), 0).astype(int).tolist() if 'medium_cloud_cover_p50' in pt else ceros_pt.astype(int).tolist()
        cldh_p50  = round(nan_to_num(pt['high_cloud_cover_p50'].values.astype(float) * 100.0, nan=0.0), 0).astype(int).tolist() if 'high_cloud_cover_p50' in pt else ceros_pt.astype(int).tolist()
        imerg_p50 = round(nan_to_num(pt['imerg_tp_1hr_p50'].values.astype(float) * 1000.0, nan=0.0), 2).tolist() if 'imerg_tp_1hr_p50' in pt else ppt_p50
        exptp_p50 = round(nan_to_num(pt['experimental_tp_1hr_p50'].values.astype(float) * 1000.0, nan=0.0), 2).tolist() if 'experimental_tp_1hr_p50' in pt else ppt_p50
        w100_p50  = round(nan_to_num(pt['wind_speed_100m_p50'].values.astype(float), nan=2.0), 1).tolist() if 'wind_speed_100m_p50' in pt else wspd_p50
        u100      = nan_to_num(pt['u_component_of_wind_100m_p50'].values.astype(float), nan=0.0) if 'u_component_of_wind_100m_p50' in pt else u
        v100      = nan_to_num(pt['v_component_of_wind_100m_p50'].values.astype(float), nan=0.0) if 'v_component_of_wind_100m_p50' in pt else v
        wdir100   = round((180 + rad2deg(arctan2(u100, v100))) % 360, 0).astype(int).tolist()

        omega   = deg2rad(15.0 * ((utc_hour + info['lon'] / 15.0) % 24 - 12.0))
        lat_rad = deg2rad(info['lat'])
        cos_z   = sin(lat_rad) * sin(rc_dec) + cos(lat_rad) * cos(rc_dec) * cos(omega)
        rad_toa = round(maximum(0.0, 1361.0 * rc_dis * cos_z), 0).astype(int).tolist()

        # PPT es tasa (mm/h) en pasos sub-diarios; el acumulado usa la duración real de cada intervalo (GFS, IFS y HRES cambian de paso).
        paso_f = diff([0] + lead_horas) if cfg['paso_h'] < 24 else 1.0
        resultado['estaciones'][k] = {
            'info': info,
            'temperatura': {'p10': t2m_p10, 'p50': t2m_p50, 'p90': t2m_p90},
            'precipitacion': {
                'p10': ppt_p10,
                'p50': ppt_p50,
                'p90': ppt_p90,
                'acumulada_p10': round(cumsum(array(ppt_p10) * paso_f), 2).tolist(),
                'acumulada': round(cumsum(array(ppt_p50) * paso_f), 2).tolist(),
                'acumulada_p90': round(cumsum(array(ppt_p90) * paso_f), 2).tolist()
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

    prev_init = load(open(ruta_json, encoding='utf-8')).get('init_utc') if exists(ruta_json) else None
    with open(ruta_json, 'w', encoding='utf-8') as f:
        dump(resultado, f, ensure_ascii=False, separators=(',', ':'))
    print(f'[{model_id.upper()}] ✓ JSON guardado en: {ruta_json}', flush=True)

    #%% EXPORTACIÓN DE MALLA VECTORIAL DE VIENTO (10M Y 100M)
    vec_data = {
        'init_utc': init_utc_str,
        'lats': round(latest.lat_0p1.values[::salto_vec].astype(float), 2).tolist(),
        'lons': round(latest.lon_0p1.values[::salto_vec].astype(float) - 360.0, 2).tolist(),
        'u10': round(nan_to_num(latest['u_component_of_wind_10m_p50'].values[:, ::salto_vec, ::salto_vec].astype(float), nan=0.0), 1).tolist(),
        'v10': round(nan_to_num(latest['v_component_of_wind_10m_p50'].values[:, ::salto_vec, ::salto_vec].astype(float), nan=0.0), 1).tolist(),
        'u100': round(nan_to_num(latest['u_component_of_wind_100m_p50' if 'u_component_of_wind_100m_p50' in latest else 'u_component_of_wind_10m_p50'].values[:, ::salto_vec, ::salto_vec].astype(float), nan=0.0), 1).tolist(),
        'v100': round(nan_to_num(latest['v_component_of_wind_100m_p50' if 'v_component_of_wind_100m_p50' in latest else 'v_component_of_wind_10m_p50'].values[:, ::salto_vec, ::salto_vec].astype(float), nan=0.0), 1).tolist()
    }
    with open(ruta_viento, 'w', encoding='utf-8') as fv:
        dump(vec_data, fv, separators=(',', ':'))

    #%% GENERACIÓN DE FRAMES ESPACIALES CON PALETAS OFICIALES
    t_capa = 'station_head_temperature_2m_p50' if ('station_head_temperature_2m_p50' in latest.data_vars and not isnan(latest['station_head_temperature_2m_p50'].values).all()) else 'temperature_2m_p50'
    todas_capas = [
        ('precipitacion',       'total_precipitation_1hr_p50',              1000.0, 0.0,     cmap_ppt,       norm_ppt,       0.1,  0.85),
        ('precipitacion_imerg', 'imerg_tp_1hr_p50',                         1000.0, 0.0,     cmap_ppt,       norm_ppt,       0.1,  0.85),
        ('precipitacion_exp',   'experimental_tp_1hr_p50',                  1000.0, 0.0,     cmap_ppt,       norm_ppt,       0.1,  0.85),
        ('temperatura',         t_capa,                                     1.0,    -273.15, cmap_temp,      norm_temp,      None, 0.72),
        ('viento',              'wind_speed_10m_p50',                       1.0,    0.0,     cmap_viento,    norm_viento,    0.5,  0.80),
        ('viento_100m',         'wind_speed_100m_p50',                      1.0,    0.0,     cmap_viento,    norm_viento,    0.5,  0.80),
        ('radiacion',           'surface_solar_radiation_downwards_1hr_p50', 1/3600, 0.0,     cmap_radiacion, norm_radiacion, 50.0, 0.82),
        ('nubosidad_total',     'total_cloud_cover_p50',                    100.0,  0.0,     cmap_nubosidad, norm_nubosidad, 10.0, 0.78),
        ('nubosidad_baja',      'low_cloud_cover_p50',                      100.0,  0.0,     cmap_nubosidad, norm_nubosidad, 10.0, 0.78),
        ('nubosidad_media',     'medium_cloud_cover_p50',                   100.0,  0.0,     cmap_nubosidad, norm_nubosidad, 10.0, 0.78),
        ('nubosidad_alta',      'high_cloud_cover_p50',                     100.0,  0.0,     cmap_nubosidad, norm_nubosidad, 10.0, 0.78),
    ]
    capas_cfg = [c for c in todas_capas if c[0] in cfg['variables'] and c[1] in latest.data_vars]

    if prev_init == init_utc_str and all(exists(f'{dir_frames}/{c[0]}_{n_frames:03d}.png') for c in capas_cfg):
        print(f'[{model_id.upper()}] ✓ Frames espaciales ({len(capas_cfg) * n_frames}) ya existen en disco.', flush=True)
    else:
        print(f'[{model_id.upper()}] Generando {len(capas_cfg) * n_frames} frames espaciales...', flush=True)
        for prefijo, var_zarr, factor, offset, cmap_fn, norm_fn, umbral, opacidad in capas_cfg:
            if prev_init == init_utc_str and exists(f'{dir_frames}/{prefijo}_{n_frames:03d}.png'):
                continue
            arr_val = nan_to_num(latest[var_zarr].values * factor + offset, nan=0.0)
            for i in range(n_frames):
                data     = flipud(arr_val[i])
                norm_val = norm_fn(data)
                rgba     = cmap_fn(norm_val)
                if umbral is not None:
                    rgba[data < umbral, 3]  = 0.0
                    rgba[data >= umbral, 3] = opacidad
                else:
                    rgba[:, :, 3] = opacidad
                img = Image.fromarray((rgba * 255).astype(uint8))
                img.save(f'{dir_frames}/{prefijo}_{i+1:03d}.png', optimize=True)

    return {
        'id': model_id,
        'carpeta': cfg['carpeta'],
        'nombre': cfg['nombre'],
        'institucion': cfg.get('institucion', ''),
        'familia': cfg.get('familia', ''),
        'licencia': cfg.get('licencia', ''),
        'etiqueta_corta': cfg['etiqueta_corta'],
        'etiqueta_fuente': cfg['etiqueta_fuente'],
        'tipo': cfg['tipo'],
        'almacenamiento': cfg['almacenamiento'],
        'resolucion': cfg['resolucion'],
        'paso_h': cfg['paso_h'],
        'horizonte_h': cfg['horizonte_h'],
        'init_utc': init_utc_str,
        'init_hl': init_hl_str,
        'n_frames': n_frames,
        'disponible': True,
        'variables': cfg['variables'],
        'base_path': 'data' if model_id == 'wn3' else f'data/models/{model_id}'
    }

if __name__ == '__main__':
    objetivo        = argv[1] if len(argv) > 1 else 'all'
    resumen_modelos = {}

    for m_id, cfg in modelos_colombia.items():
        if objetivo != 'all' and m_id not in objetivo.split(','):
            continue
        meta_m = exportar_modelo_web(m_id, cfg)
        if meta_m:
            resumen_modelos[m_id] = meta_m

    catalogo_web = {
        'dominios': dominios_plataforma,
        'dominio_por_defecto': 'colombia',
        'modelo_por_defecto': 'wn3',
        'modelos_colombia': {
            m_id: resumen_modelos.get(m_id, {
                'id': m_id,
                'carpeta': cfg['carpeta'],
                'nombre': cfg['nombre'],
                'institucion': cfg.get('institucion', ''),
                'familia': cfg.get('familia', ''),
                'licencia': cfg.get('licencia', ''),
                'etiqueta_corta': cfg['etiqueta_corta'],
                'etiqueta_fuente': cfg['etiqueta_fuente'],
                'tipo': cfg['tipo'],
                'almacenamiento': cfg['almacenamiento'],
                'resolucion': cfg['resolucion'],
                'paso_h': cfg['paso_h'],
                'horizonte_h': cfg['horizonte_h'],
                'disponible': exists(cfg['ruta_zarr']),
                'variables': cfg['variables'],
                'base_path': 'data' if m_id == 'wn3' else f'data/models/{m_id}'
            })
            for m_id, cfg in modelos_colombia.items()
        }
    }
    ruta_cat = f'{dir_web_base}/models_catalog.json'
    with open(ruta_cat, 'w', encoding='utf-8') as fc:
        dump(catalogo_web, fc, indent=2, ensure_ascii=False)
    print(f'\n✓ Catálogo multimodelo web guardado en: {ruta_cat}', flush=True)
