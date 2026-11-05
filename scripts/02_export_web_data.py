"""
02_export_web_data.py — Extractor y generador de datos meteorológicos y frames para el portal web.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.6.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-11-04][Duvan]: Paletas científicas y eliminación de emojis.
    - [2026-11-04][Duvan]: Radiación teórica ToA y PPT acumulada.
"""

from sys import path
path.insert(0, '/home/dnieves/Documentos/My-4Cast')

from PIL import Image
from os import makedirs
from os.path import exists
from json import dump, load
from xarray import open_zarr
from pandas import to_datetime
from src.paletas import cmap_ppt, cmap_temp, cmap_viento, norm_ppt, norm_temp, norm_viento
from numpy import arctan2, cos, cumsum, deg2rad, flipud, isnan, maximum, nan_to_num, pi, rad2deg, round, sin, timedelta64, uint8

#%% CONFIGURACIÓN DE PARÁMETROS Y RUTAS
ruta_zarr  = '/mnt/datos/dnieves/WN3/raw/colombia_wn3_full.zarr'
dir_sal    = '/mnt/datos/dnieves/WN3/web_data'
dir_frames = f'{dir_sal}/frames'
ruta_json  = f'{dir_sal}/latest_weather.json'
makedirs(dir_sal, exist_ok=True)
makedirs(dir_frames, exist_ok=True)

#%% CATÁLOGO DE MUNICIPIOS Y ESTACIONES PRIORITARIAS (SIN EMOJIS, FORMATO CIENTÍFICO)
estaciones = {
    'velez': {
        'nombre': 'Vélez',
        'depto': 'Santander',
        'lat': 6.0139,
        'lon': -73.6739,
        'altitud': 2050,
        'tag': 'Sede Principal'
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
    }
}

#%% EXTRACCIÓN Y SERIALIZACIÓN
if __name__ == '__main__':
    print('Abriendo dataset canónico...', flush=True)
    ds = open_zarr(ruta_zarr)

    latest = None
    for idx in range(len(ds.init_time) - 1, -1, -1):
        cand = ds.isel(init_time=idx)
        sample = cand['temperature_2m_p50'].isel(lat_0p1=100, lon_0p1=100).values
        if not isnan(sample).any() and len(sample) == 360:
            latest = cand
            print(f"Seleccionada corrida completa: {str(cand.init_time.values)[:19]} UTC (índice {idx})", flush=True)
            break

    if latest is None:
        raise ValueError('No se encontró ninguna corrida con 360 horas completas.')

    init_utc_raw = latest.init_time.values
    init_utc_str = str(init_utc_raw)[:19] + ' UTC'
    init_hl_raw  = init_utc_raw - timedelta64(5, 'h')
    init_hl_str  = str(init_hl_raw)[:19] + ' HL (Colombia)'

    lead_horas = [int(i + 1) for i in range(len(latest.lead_time))]
    valid_hl   = [str(init_hl_raw + timedelta64(h, 'h'))[:16] for h in lead_horas]

    resultado = {
        'modelo': 'WeatherNext 3 (Google DeepMind / ECMWF)',
        'resolucion': '0.1° (~11 km)',
        'init_utc': init_utc_str,
        'init_hl': init_hl_str,
        'lead_hours': lead_horas,
        'valid_hl': valid_hl,
        'bounds': [[-5.0, -85.0], [16.5, -60.0]],
        'frame_hours': 360,
        'regiones': {
            'nacional': {'nombre': 'Colombia (Nacional)', 'centro': [4.5, -73.5], 'zoom': 6},
            'santander': {'nombre': 'Santander (Vélez & Serranía)', 'centro': [6.4, -73.4], 'zoom': 8},
            'boyaca': {'nombre': 'Boyacá (Tunja & Altiplano)', 'centro': [5.7, -73.4], 'zoom': 8},
            'san_andres': {'nombre': 'Archipiélago de San Andrés', 'centro': [12.8, -81.5], 'zoom': 9},
            'antioquia': {'nombre': 'Antioquia (Medellín & Valle)', 'centro': [6.5, -75.5], 'zoom': 8}
        },
        'estaciones': {}
    }

    print(f'Extrayendo series de tiempo para {len(estaciones)} municipios...', flush=True)
    dts      = to_datetime([init_utc_raw + timedelta64(h, 'h') for h in lead_horas])
    theta_d  = 2 * pi * (dts.day_of_year.values - 1) / 365.0
    rc_dis   = 1.00011 + 0.034221 * cos(theta_d) + 0.00128 * sin(theta_d) + 0.000719 * cos(2 * theta_d) + 0.000077 * sin(2 * theta_d)
    rc_dec   = 0.006918 - 0.39912 * cos(theta_d) + 0.070257 * sin(theta_d) - 0.006758 * cos(2 * theta_d) + 0.000907 * sin(2 * theta_d) - 0.002697 * cos(3 * theta_d) + 0.00148 * sin(3 * theta_d)
    utc_hour = dts.hour.values + dts.minute.values / 60.0

    for k, info in estaciones.items():
        lat_t = info['lat']
        lon_t = 360.0 + info['lon'] if info['lon'] < 0 else info['lon']

        pt = latest.sel(lat_0p1=lat_t, lon_0p1=lon_t, method='nearest')

        t2m_p50 = round(nan_to_num(pt['temperature_2m_p50'].values - 273.15, nan=20.0), 1).tolist()
        t2m_p10 = round(nan_to_num(pt['temperature_2m_p10'].values - 273.15, nan=15.0), 1).tolist()
        t2m_p90 = round(nan_to_num(pt['temperature_2m_p90'].values - 273.15, nan=25.0), 1).tolist()

        ppt_p50 = round(nan_to_num(pt['total_precipitation_1hr_p50'].values * 1000.0, nan=0.0), 2).tolist()
        ppt_p10 = round(nan_to_num(pt['total_precipitation_1hr_p10'].values * 1000.0, nan=0.0), 2).tolist()
        ppt_p90 = round(nan_to_num(pt['total_precipitation_1hr_p90'].values * 1000.0, nan=0.0), 2).tolist()

        wspd_p50 = round(nan_to_num(pt['wind_speed_10m_p50'].values, nan=2.0), 1).tolist()
        wspd_p10 = round(nan_to_num(pt['wind_speed_10m_p10'].values, nan=1.0), 1).tolist()
        wspd_p90 = round(nan_to_num(pt['wind_speed_10m_p90'].values, nan=4.0), 1).tolist()

        u = nan_to_num(pt['u_component_of_wind_10m_p50'].values, nan=0.0)
        v = nan_to_num(pt['v_component_of_wind_10m_p50'].values, nan=0.0)
        wdir = round((180 + rad2deg(arctan2(u, v))) % 360, 0).astype(int).tolist()

        rad_p50 = round(nan_to_num(pt['surface_solar_radiation_downwards_1hr_p50'].values / 3600.0, nan=0.0), 0).tolist()
        cld_p50 = round(nan_to_num(pt['total_cloud_cover_p50'].values * 100, nan=50.0), 0).tolist()

        omega   = deg2rad(15.0 * ((utc_hour + info['lon'] / 15.0) % 24 - 12.0))
        lat_rad = deg2rad(info['lat'])
        cos_z   = sin(lat_rad) * sin(rc_dec) + cos(lat_rad) * cos(rc_dec) * cos(omega)
        rad_toa = round(maximum(0.0, 1361.0 * rc_dis * cos_z), 0).astype(int).tolist()

        resultado['estaciones'][k] = {
            'info': info,
            'temperatura': {'p10': t2m_p10, 'p50': t2m_p50, 'p90': t2m_p90},
            'precipitacion': {
                'p10': ppt_p10,
                'p50': ppt_p50,
                'p90': ppt_p90,
                'acumulada_p10': round(cumsum(ppt_p10), 2).tolist(),
                'acumulada': round(cumsum(ppt_p50), 2).tolist(),
                'acumulada_p90': round(cumsum(ppt_p90), 2).tolist()
            },
            'viento': {'p10': wspd_p10, 'p50': wspd_p50, 'p90': wspd_p90, 'dir': wdir},
            'radiacion_solar': {'p50': rad_p50, 'teorica': rad_toa},
            'nubosidad': {'p50': cld_p50}
        }

    prev_init = load(open(ruta_json, encoding='utf-8')).get('init_utc') if exists(ruta_json) else None
    with open(ruta_json, 'w', encoding='utf-8') as f:
        dump(resultado, f, ensure_ascii=False)
    print(f'✓ JSON guardado en: {ruta_json}', flush=True)

    #%% GENERACIÓN DE FRAMES ESPACIALES (0-360h / 15 DÍAS) CON PALETAS OFICIALES
    if prev_init == init_utc_str and exists(f'{dir_frames}/viento_360.png') and exists(f'{dir_frames}/precipitacion_360.png'):
        print('✓ Frames espaciales (1080) ya existen en disco para esta corrida. Omitiendo regeneración.', flush=True)
    else:
        n_frames = 360
        print(f'\nGenerando 1080 frames con paletas científicas (src/paletas.py)...', flush=True)

        # 1. Precipitación Horaria (mm/h con CMAP_PPT y NORM_PPT)
        print('  - Renderizando 360 frames de precipitación...', flush=True)
        ppt_arr = nan_to_num(latest['total_precipitation_1hr_p50'].values * 1000.0, nan=0.0)
        for i in range(n_frames):
            data = flipud(ppt_arr[i])
            norm_val = norm_ppt(data)
            rgba = cmap_ppt(norm_val)
            rgba[data < 0.1, 3] = 0.0
            rgba[data >= 0.1, 3] = 0.85
            img = Image.fromarray((rgba * 255).astype(uint8))
            img.save(f'{dir_frames}/precipitacion_{i+1:03d}.png', optimize=True)

        # 2. Temperatura a 2m (°C con CMAP_TEMP y NORM_TEMP)
        print('  - Renderizando 360 frames de temperatura...', flush=True)
        t2m_arr = nan_to_num(latest['temperature_2m_p50'].values - 273.15, nan=20.0)
        for i in range(n_frames):
            data = flipud(t2m_arr[i])
            norm_val = norm_temp(data)
            rgba = cmap_temp(norm_val)
            rgba[:, :, 3] = 0.72
            img = Image.fromarray((rgba * 255).astype(uint8))
            img.save(f'{dir_frames}/temperatura_{i+1:03d}.png', optimize=True)

        # 3. Intensidad de Viento a 10m (m/s con CMAP_VIENTO y NORM_VIENTO)
        print('  - Renderizando 360 frames de viento...', flush=True)
        wspd_arr = nan_to_num(latest['wind_speed_10m_p50'].values, nan=0.0)
        for i in range(n_frames):
            data = flipud(wspd_arr[i])
            norm_val = norm_viento(data)
            rgba = cmap_viento(norm_val)
            rgba[data < 0.5, 3] = 0.0
            rgba[data >= 0.5, 3] = 0.80
            img = Image.fromarray((rgba * 255).astype(uint8))
            img.save(f'{dir_frames}/viento_{i+1:03d}.png', optimize=True)

        print(f'✓ Todos los {n_frames * 3} frames generados exitosamente con paletas exactas.', flush=True)
