"""
02_export_web_data.py — Extractor y generador de datos meteorológicos y frames para el portal web.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.2.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-11-03][Duvan]: Agregado catálogo extendido de 36 estaciones y generador de frames espaciales.
"""

from sys import path
path.insert(0, '/home/dnieves/Documentos/My-4Cast')

from os import makedirs
from json import dump
from PIL import Image
import matplotlib.pyplot as plt
from numpy import arctan2, clip, datetime64, flipud, rad2deg, round, timedelta64, uint8
from xarray import open_zarr

#%% CONFIGURACIÓN DE PARÁMETROS Y RUTAS
ruta_zarr  = '/mnt/datos/dnieves/WN3/raw/colombia_wn3_full.zarr'
dir_sal    = '/mnt/datos/dnieves/WN3/web_data'
dir_frames = f'{dir_sal}/frames'
ruta_json  = f'{dir_sal}/latest_weather.json'
makedirs(dir_sal, exist_ok=True)
makedirs(dir_frames, exist_ok=True)

#%% CATÁLOGO DE MUNICIPIOS Y ESTACIONES PRIORITARIAS
estaciones = {
    'velez': {
        'nombre': 'Vélez',
        'depto': 'Santander',
        'lat': 6.0139,
        'lon': -73.6739,
        'altitud': 2050,
        'tag': 'Residencia & Enfoque'
    },
    'guavata': {
        'nombre': 'Guavatá',
        'depto': 'Santander',
        'lat': 5.9264,
        'lon': -73.7153,
        'altitud': 1950,
        'tag': 'Santander Sur'
    },
    'barbosa': {
        'nombre': 'Barbosa',
        'depto': 'Santander',
        'lat': 5.9322,
        'lon': -73.6178,
        'altitud': 1610,
        'tag': 'Santander Sur'
    },
    'san_gil': {
        'nombre': 'San Gil',
        'depto': 'Santander',
        'lat': 6.5561,
        'lon': -73.1369,
        'altitud': 1117,
        'tag': 'Guanentá'
    },
    'socorro': {
        'nombre': 'Socorro',
        'depto': 'Santander',
        'lat': 6.4678,
        'lon': -73.2625,
        'altitud': 1230,
        'tag': 'Comunera'
    },
    'bucaramanga': {
        'nombre': 'Bucaramanga',
        'depto': 'Santander',
        'lat': 7.1193,
        'lon': -73.1227,
        'altitud': 960,
        'tag': 'Capital Santander'
    },
    'chiquinquira': {
        'nombre': 'Chiquinquirá',
        'depto': 'Boyacá',
        'lat': 5.6186,
        'lon': -73.8175,
        'altitud': 2550,
        'tag': 'Boyacá Occidente'
    },
    'tunja': {
        'nombre': 'Tunja',
        'depto': 'Boyacá',
        'lat': 5.5353,
        'lon': -73.3678,
        'altitud': 2800,
        'tag': 'Capital Boyacá'
    },
    'moniquira': {
        'nombre': 'Moniquirá',
        'depto': 'Boyacá',
        'lat': 5.8756,
        'lon': -73.5739,
        'altitud': 1669,
        'tag': 'Boyacá Ricaurte'
    },
    'villa_de_leyva': {
        'nombre': 'Villa de Leyva',
        'depto': 'Boyacá',
        'lat': 5.6322,
        'lon': -73.5244,
        'altitud': 2149,
        'tag': 'Boyacá Alto Ricaurte'
    },
    'duitama': {
        'nombre': 'Duitama',
        'depto': 'Boyacá',
        'lat': 5.8267,
        'lon': -73.0336,
        'altitud': 2530,
        'tag': 'Tundama'
    },
    'sogamoso': {
        'nombre': 'Sogamoso',
        'depto': 'Boyacá',
        'lat': 5.7144,
        'lon': -72.9339,
        'altitud': 2569,
        'tag': 'Sugamuxi'
    },
    'san_andres': {
        'nombre': 'San Andrés Islas',
        'depto': 'San Andrés y Providencia',
        'lat': 12.5847,
        'lon': -81.7006,
        'altitud': 2,
        'tag': 'Caribe Insular'
    },
    'providencia': {
        'nombre': 'Providencia',
        'depto': 'San Andrés y Providencia',
        'lat': 13.3561,
        'lon': -81.3719,
        'altitud': 10,
        'tag': 'Caribe Insular'
    },
    'medellin': {
        'nombre': 'Medellín',
        'depto': 'Antioquia',
        'lat': 6.2442,
        'lon': -75.5812,
        'altitud': 1495,
        'tag': 'Capital Antioquia'
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
        'tag': 'Urabá Antioqueño'
    },
    'ibague': {
        'nombre': 'Ibagué',
        'depto': 'Tolima',
        'lat': 4.4389,
        'lon': -75.2322,
        'altitud': 1285,
        'tag': 'Capital Tolima'
    },
    'bogota': {
        'nombre': 'Bogotá D.C.',
        'depto': 'Cundinamarca',
        'lat': 4.7110,
        'lon': -74.0721,
        'altitud': 2640,
        'tag': 'Distrito Capital'
    },
    'cali': {
        'nombre': 'Cali',
        'depto': 'Valle del Cauca',
        'lat': 3.4516,
        'lon': -76.5320,
        'altitud': 1018,
        'tag': 'Pacífico Sur'
    },
    'barranquilla': {
        'nombre': 'Barranquilla',
        'depto': 'Atlántico',
        'lat': 10.9685,
        'lon': -74.7813,
        'altitud': 18,
        'tag': 'Caribe Norte'
    },
    'cartagena': {
        'nombre': 'Cartagena',
        'depto': 'Bolívar',
        'lat': 10.3910,
        'lon': -75.4794,
        'altitud': 2,
        'tag': 'Caribe'
    },
    'santa_marta': {
        'nombre': 'Santa Marta',
        'depto': 'Magdalena',
        'lat': 11.2408,
        'lon': -74.1990,
        'altitud': 6,
        'tag': 'Sierra Nevada'
    },
    'pereira': {
        'nombre': 'Pereira',
        'depto': 'Risaralda',
        'lat': 4.8133,
        'lon': -75.6961,
        'altitud': 1411,
        'tag': 'Eje Cafetero'
    },
    'manizales': {
        'nombre': 'Manizales',
        'depto': 'Caldas',
        'lat': 5.0689,
        'lon': -75.5174,
        'altitud': 2150,
        'tag': 'Eje Cafetero'
    },
    'armenia': {
        'nombre': 'Armenia',
        'depto': 'Quindío',
        'lat': 4.5339,
        'lon': -75.6811,
        'altitud': 1551,
        'tag': 'Eje Cafetero'
    },
    'cucuta': {
        'nombre': 'Cúcuta',
        'depto': 'Norte de Santander',
        'lat': 7.8939,
        'lon': -72.5078,
        'altitud': 320,
        'tag': 'Frontera Oriente'
    },
    'pasto': {
        'nombre': 'Pasto',
        'depto': 'Nariño',
        'lat': 1.2136,
        'lon': -77.2811,
        'altitud': 2527,
        'tag': 'Suroccidente'
    },
    'popayan': {
        'nombre': 'Popayán',
        'depto': 'Cauca',
        'lat': 2.4448,
        'lon': -76.6147,
        'altitud': 1760,
        'tag': 'Cauca'
    },
    'neiva': {
        'nombre': 'Neiva',
        'depto': 'Huila',
        'lat': 2.9273,
        'lon': -75.2819,
        'altitud': 442,
        'tag': 'Alto Magdalena'
    },
    'villavicencio': {
        'nombre': 'Villavicencio',
        'depto': 'Meta',
        'lat': 4.1420,
        'lon': -73.6266,
        'altitud': 467,
        'tag': 'Llanos Orientales'
    },
    'monteria': {
        'nombre': 'Montería',
        'depto': 'Córdoba',
        'lat': 8.7479,
        'lon': -75.8814,
        'altitud': 18,
        'tag': 'Sinú'
    },
    'valledupar': {
        'nombre': 'Valledupar',
        'depto': 'Cesar',
        'lat': 10.4631,
        'lon': -73.2532,
        'altitud': 168,
        'tag': 'Valle del Cacique'
    },
    'riohacha': {
        'nombre': 'Riohacha',
        'depto': 'La Guajira',
        'lat': 11.5444,
        'lon': -72.9072,
        'altitud': 5,
        'tag': 'Guajira'
    },
    'quibdo': {
        'nombre': 'Quibdó',
        'depto': 'Chocó',
        'lat': 5.6919,
        'lon': -76.6583,
        'altitud': 43,
        'tag': 'Chocó Biogeográfico'
    },
    'leticia': {
        'nombre': 'Leticia',
        'depto': 'Amazonas',
        'lat': -4.2153,
        'lon': -69.9406,
        'altitud': 96,
        'tag': 'Amazonía'
    }
}

#%% EXTRACCIÓN Y SERIALIZACIÓN
if __name__ == '__main__':
    print('Abriendo dataset canónico...', flush=True)
    ds     = open_zarr(ruta_zarr)
    latest = ds.isel(init_time=-1)

    init_utc_raw = latest.init_time.values
    init_utc_str = str(init_utc_raw)[:19] + ' UTC'
    init_hl_raw  = init_utc_raw - timedelta64(5, 'h')
    init_hl_str  = str(init_hl_raw)[:19] + ' HL (Colombia)'

    lead_horas = [int(i + 1) for i in range(len(latest.lead_time))]
    valid_hl   = [str(init_hl_raw + timedelta64(h, 'h'))[:16] for h in lead_horas]

    resultado = {
        'modelo': 'WeatherNext 3 (Google DeepMind / ECMWF)',
        'init_utc': init_utc_str,
        'init_hl': init_hl_str,
        'lead_hours': lead_horas,
        'valid_hl': valid_hl,
        'bounds': [[-5.0, -85.0], [16.5, -60.0]],
        'frame_hours': 72,
        'regiones': {
            'nacional': {'nombre': 'Colombia (Nacional)', 'centro': [4.5, -73.5], 'zoom': 6},
            'santander': {'nombre': 'Santander (Vélez & Guavatá)', 'centro': [6.4, -73.4], 'zoom': 8},
            'boyaca': {'nombre': 'Boyacá (Tunja & Chiquinquirá)', 'centro': [5.7, -73.4], 'zoom': 8},
            'san_andres': {'nombre': 'San Andrés y Providencia', 'centro': [12.8, -81.5], 'zoom': 9},
            'antioquia': {'nombre': 'Antioquia (Medellín & Valle)', 'centro': [6.5, -75.5], 'zoom': 8}
        },
        'estaciones': {}
    }

    print(f'Extrayendo series de tiempo para {len(estaciones)} municipios...', flush=True)
    for k, info in estaciones.items():
        lat_t = info['lat']
        lon_t = 360.0 + info['lon'] if info['lon'] < 0 else info['lon']

        pt = latest.sel(lat_0p1=lat_t, lon_0p1=lon_t, method='nearest')

        t2m_p50 = round(pt['temperature_2m_p50'].values - 273.15, 1).tolist()
        t2m_p10 = round(pt['temperature_2m_p10'].values - 273.15, 1).tolist()
        t2m_p90 = round(pt['temperature_2m_p90'].values - 273.15, 1).tolist()

        ppt_p50 = round(pt['total_precipitation_1hr_p50'].values, 2).tolist()
        ppt_p10 = round(pt['total_precipitation_1hr_p10'].values, 2).tolist()
        ppt_p90 = round(pt['total_precipitation_1hr_p90'].values, 2).tolist()

        wspd_p50 = round(pt['wind_speed_10m_p50'].values, 1).tolist()
        wspd_p10 = round(pt['wind_speed_10m_p10'].values, 1).tolist()
        wspd_p90 = round(pt['wind_speed_10m_p90'].values, 1).tolist()

        u = pt['u_component_of_wind_10m_p50'].values
        v = pt['v_component_of_wind_10m_p50'].values
        wdir = round((180 + rad2deg(arctan2(u, v))) % 360, 0).astype(int).tolist()

        rad_p50 = round(pt['surface_solar_radiation_downwards_1hr_p50'].values / 3600.0, 0).tolist()
        cld_p50 = round(pt['total_cloud_cover_p50'].values * 100, 0).tolist()

        resultado['estaciones'][k] = {
            'info': info,
            'temperatura': {'p10': t2m_p10, 'p50': t2m_p50, 'p90': t2m_p90},
            'precipitacion': {'p10': ppt_p10, 'p50': ppt_p50, 'p90': ppt_p90},
            'viento': {'p10': wspd_p10, 'p50': wspd_p50, 'p90': wspd_p90, 'dir': wdir},
            'radiacion_solar': {'p50': rad_p50},
            'nubosidad': {'p50': cld_p50}
        }

    with open(ruta_json, 'w', encoding='utf-8') as f:
        dump(resultado, f, ensure_ascii=False)
    print(f'✓ JSON guardado en: {ruta_json}', flush=True)

    #%% GENERACIÓN DE FRAMES ESPACIALES (0-72h)
    print('\nGenerando frames espaciales optimizados (72 horas)...', flush=True)
    n_frames = 72

    # 1. Precipitación (mm/h)
    print('  - Renderizando frames de precipitación...', flush=True)
    ppt_arr = latest['total_precipitation_1hr_p50'].isel(lead_time=slice(0, n_frames)).values
    cmap_ppt = plt.get_cmap('turbo')
    for i in range(n_frames):
        data = flipud(ppt_arr[i])
        norm = clip(data / 25.0, 0, 1)
        rgba = cmap_ppt(norm)
        rgba[data < 0.15, 3] = 0.0
        rgba[data >= 0.15, 3] = 0.75
        img = Image.fromarray((rgba * 255).astype(uint8))
        img.save(f'{dir_frames}/precipitacion_{i+1}.png', optimize=True)

    # 2. Temperatura (°C)
    print('  - Renderizando frames de temperatura...', flush=True)
    t2m_arr = latest['temperature_2m_p50'].isel(lead_time=slice(0, n_frames)).values - 273.15
    cmap_t2m = plt.get_cmap('RdYlBu_r')
    for i in range(n_frames):
        data = flipud(t2m_arr[i])
        norm = clip((data - 5.0) / 30.0, 0, 1)
        rgba = cmap_t2m(norm)
        rgba[:, :, 3] = 0.60
        img = Image.fromarray((rgba * 255).astype(uint8))
        img.save(f'{dir_frames}/temperatura_{i+1}.png', optimize=True)

    # 3. Viento (m/s)
    print('  - Renderizando frames de viento...', flush=True)
    wspd_arr = latest['wind_speed_10m_p50'].isel(lead_time=slice(0, n_frames)).values
    cmap_wspd = plt.get_cmap('viridis')
    for i in range(n_frames):
        data = flipud(wspd_arr[i])
        norm = clip(data / 18.0, 0, 1)
        rgba = cmap_wspd(norm)
        rgba[data < 1.0, 3] = 0.0
        rgba[data >= 1.0, 3] = 0.70
        img = Image.fromarray((rgba * 255).astype(uint8))
        img.save(f'{dir_frames}/viento_{i+1}.png', optimize=True)

    print('✓ Todos los frames generados exitosamente.', flush=True)
