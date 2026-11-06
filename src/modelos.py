"""
modelos.py — Registro centralizado de modelos de pronóstico y política de almacenamiento (WN3 canónico vs. fuentes efímeras).

__author__: "Duvan Nieves"
__copyright__: "Duvan Nieves Ruiz"
__version__: "0.2.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves.sci@gmail.com"
__status__: "Developer"
__changues__:
    - [2026-11-05][Duvan]: Inclusión de Aurora, FourCastNet v2, GraphCast y Pangu-Weather; carpeta individual por fuente en Drive.
"""

from os import getenv

#%% CONFIGURACIÓN DE RUTAS
DIR_BASE = getenv('MY4CAST_DATA_DIR', '/mnt/datos/dnieves/WN3')

#%% DOMINIOS MACRO DE LA PLATAFORMA
dominios_plataforma = {
    'colombia': {
        'id': 'colombia',
        'nombre': 'Colombia',
        'activo': True,
        'descripcion': 'Pronóstico multimodelo de superficie y viento para las 32 capitales departamentales y municipios prioritarios.'
    },
    'enso': {
        'id': 'enso',
        'nombre': 'ENSO',
        'activo': False,
        'descripcion': 'Monitoreo y pronóstico de anomalías térmicas y acoplamiento océano-atmósfera en las regiones Niño.'
    },
    'mjo': {
        'id': 'mjo',
        'nombre': 'MJO',
        'activo': False,
        'descripcion': 'Seguimiento subestacional de pulsos convectivos intratropicales y fase activa sobre Suramérica.'
    },
    'ciclones_tropicales': {
        'id': 'ciclones_tropicales',
        'nombre': 'Ciclones Tropicales',
        'activo': False,
        'descripcion': 'Trayectorias de ensamble, intensidad e impactos costeros sobre el mar Caribe y archipiélago.'
    }
}

#%% CATÁLOGO DE 11 FUENTES DE PRONÓSTICO PARA COLOMBIA (1 CANÓNICA + 10 EFÍMERAS)
modelos_colombia = {
    'wn3': {
        'id': 'wn3',
        'carpeta': 'GOOGLE_WN3',
        'nombre': 'WeatherNext 3 (Google DeepMind)',
        'etiqueta_corta': 'WeatherNext 3 · IA Ensamble (64m)',
        'etiqueta_fuente': 'WN3 · Google DeepMind (IA Ensamble)',
        'sello_mapa': 'WeatherNext 3\nGoogle DeepMind (IA 64m)',
        'tipo': 'IA Ensamble (64 miembros)',
        'resolucion': '0.1° (~11 km)',
        'paso_h': 1,
        'horizonte_h': 360,
        'salto_quiver': 10,
        'salto_web': 6,
        'almacenamiento': 'canonico_historico',
        'ruta_zarr': f'{DIR_BASE}/raw/colombia_wn3_full.zarr',
        'dir_anim': f'{DIR_BASE}/animations/WN3',
        'dir_fig': f'{DIR_BASE}/figures/WN3',
        'variables': [
            'precipitacion', 'precipitacion_imerg', 'precipitacion_exp',
            'temperatura', 'viento', 'viento_100m', 'radiacion',
            'nubosidad_total', 'nubosidad_baja', 'nubosidad_media', 'nubosidad_alta'
        ]
    },
    'ecmwf_ifs': {
        'id': 'ecmwf_ifs',
        'carpeta': 'ECMWF_IFS',
        'nombre': 'ECMWF IFS ENS 15-Day (Open)',
        'etiqueta_corta': 'ECMWF IFS · Físico Ensamble (51m)',
        'etiqueta_fuente': 'ECMWF IFS · Físico Ensamble (51m)',
        'sello_mapa': 'ECMWF IFS ENS (51m)\nFísico Open Data',
        'tipo': 'Físico Ensamble (51 miembros)',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 3,
        'horizonte_h': 360,
        'salto_quiver': 4,
        'salto_web': 3,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': f'{DIR_BASE}/staging/models/ecmwf_ifs.zarr',
        'dir_anim': f'{DIR_BASE}/animations/ECMWF_IFS',
        'dir_fig': f'{DIR_BASE}/figures/ECMWF_IFS',
        'variables': ['precipitacion', 'temperatura', 'viento', 'viento_100m', 'radiacion', 'nubosidad_total']
    },
    'ecmwf_aifs_ens': {
        'id': 'ecmwf_aifs_ens',
        'carpeta': 'ECMWF_AIFS_ENS',
        'nombre': 'ECMWF AIFS ENS 15-Day (Open)',
        'etiqueta_corta': 'ECMWF AIFS ENS · IA Ensamble (51m)',
        'etiqueta_fuente': 'ECMWF AIFS ENS · IA Ensamble (51m)',
        'sello_mapa': 'ECMWF AIFS ENS (51m)\nIA Ensamble Open Data',
        'tipo': 'IA Ensamble (51 miembros)',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 360,
        'salto_quiver': 4,
        'salto_web': 3,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': f'{DIR_BASE}/staging/models/ecmwf_aifs_ens.zarr',
        'dir_anim': f'{DIR_BASE}/animations/ECMWF_AIFS_ENS',
        'dir_fig': f'{DIR_BASE}/figures/ECMWF_AIFS_ENS',
        'variables': ['precipitacion', 'temperatura', 'viento', 'viento_100m', 'radiacion', 'nubosidad_total']
    },
    'ecmwf_aifs_single': {
        'id': 'ecmwf_aifs_single',
        'carpeta': 'ECMWF_AIFS_SINGLE',
        'nombre': 'ECMWF AIFS Single 15-Day (Open)',
        'etiqueta_corta': 'ECMWF AIFS Single · IA Determinista',
        'etiqueta_fuente': 'ECMWF AIFS Single · IA Determinista',
        'sello_mapa': 'ECMWF AIFS Single\nIA Determinista Open Data',
        'tipo': 'IA Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 360,
        'salto_quiver': 4,
        'salto_web': 3,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': f'{DIR_BASE}/staging/models/ecmwf_aifs_single.zarr',
        'dir_anim': f'{DIR_BASE}/animations/ECMWF_AIFS_SINGLE',
        'dir_fig': f'{DIR_BASE}/figures/ECMWF_AIFS_SINGLE',
        'variables': ['precipitacion', 'temperatura', 'viento', 'viento_100m', 'radiacion', 'nubosidad_total']
    },
    'noaa_gfs': {
        'id': 'noaa_gfs',
        'carpeta': 'NOAA_GFS',
        'nombre': 'NOAA GFS 16-Day Forecast',
        'etiqueta_corta': 'NOAA GFS · Físico Determinista',
        'etiqueta_fuente': 'NOAA GFS · NCEP Físico (0.25°)',
        'sello_mapa': 'NOAA GFS 0.25°\nNCEP Físico Determinista',
        'tipo': 'Físico Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 1,
        'horizonte_h': 384,
        'salto_quiver': 4,
        'salto_web': 3,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': f'{DIR_BASE}/staging/models/noaa_gfs.zarr',
        'dir_anim': f'{DIR_BASE}/animations/NOAA_GFS',
        'dir_fig': f'{DIR_BASE}/figures/NOAA_GFS',
        'variables': ['precipitacion', 'temperatura', 'viento', 'viento_100m', 'radiacion', 'nubosidad_total']
    },
    'dwd_icon': {
        'id': 'dwd_icon',
        'carpeta': 'DWD_ICON',
        'nombre': 'DWD ICON Global (Open)',
        'etiqueta_corta': 'DWD ICON · Físico (0.125°)',
        'etiqueta_fuente': 'DWD ICON Global · Físico (0.125°)',
        'sello_mapa': 'DWD ICON Global 0.125°\nDeutscher Wetterdienst',
        'tipo': 'Físico Determinista',
        'resolucion': '0.125° (~13 km)',
        'paso_h': 3,
        'horizonte_h': 180,
        'salto_quiver': 8,
        'salto_web': 5,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': f'{DIR_BASE}/staging/models/dwd_icon.zarr',
        'dir_anim': f'{DIR_BASE}/animations/DWD_ICON',
        'dir_fig': f'{DIR_BASE}/figures/DWD_ICON',
        'variables': ['precipitacion', 'temperatura', 'viento', 'radiacion', 'nubosidad_total']
    },
    'chirps_gefs': {
        'id': 'chirps_gefs',
        'carpeta': 'UCSB_CHIRPS_GEFS',
        'nombre': 'UCSB CHIRPS-GEFS v3 16-Day',
        'etiqueta_corta': 'CHIRPS-GEFS v3 · Satélite+GEFS (0.05°)',
        'etiqueta_fuente': 'CHIRPS-GEFS v3 · UCSB CHC (0.05°)',
        'sello_mapa': 'CHIRPS-GEFS v3 (0.05°)\nUCSB Climate Hazards Center',
        'tipo': 'Híbrido Satélite + GEFS',
        'resolucion': '0.05° (~5 km)',
        'paso_h': 24,
        'horizonte_h': 384,
        'salto_quiver': 12,
        'salto_web': 10,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': f'{DIR_BASE}/staging/models/chirps_gefs.zarr',
        'dir_anim': f'{DIR_BASE}/animations/CHIRPS_GEFS',
        'dir_fig': f'{DIR_BASE}/figures/CHIRPS_GEFS',
        'variables': ['precipitacion']
    },
    'graphcast_gfs': {
        'id': 'graphcast_gfs',
        'carpeta': 'NOAA_GRAPHCAST_GFS',
        'nombre': 'GraphCast GFS (Google DeepMind / NOAA)',
        'etiqueta_corta': 'GraphCast GFS · IA Determinista',
        'etiqueta_fuente': 'GraphCast GFS · Google / NOAA (IA)',
        'sello_mapa': 'GraphCast GFS (IA)\nGoogle DeepMind / NOAA MLWP',
        'tipo': 'IA Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 240,
        'salto_quiver': 4,
        'salto_web': 3,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': f'{DIR_BASE}/staging/models/graphcast_gfs.zarr',
        'dir_anim': f'{DIR_BASE}/animations/GRAPHCAST_GFS',
        'dir_fig': f'{DIR_BASE}/figures/GRAPHCAST_GFS',
        'variables': ['precipitacion', 'temperatura', 'viento']
    },
    'aurora_gfs': {
        'id': 'aurora_gfs',
        'carpeta': 'NOAA_AURORA_GFS',
        'nombre': 'Microsoft Aurora GFS (NOAA MLWP)',
        'etiqueta_corta': 'Microsoft Aurora · IA Determinista',
        'etiqueta_fuente': 'Aurora GFS · Microsoft / NOAA (IA)',
        'sello_mapa': 'Microsoft Aurora (IA)\nMicrosoft Research / NOAA MLWP',
        'tipo': 'IA Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 240,
        'salto_quiver': 4,
        'salto_web': 3,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': f'{DIR_BASE}/staging/models/aurora_gfs.zarr',
        'dir_anim': f'{DIR_BASE}/animations/AURORA_GFS',
        'dir_fig': f'{DIR_BASE}/figures/AURORA_GFS',
        'variables': ['temperatura', 'viento']
    },
    'fourcastnet_gfs': {
        'id': 'fourcastnet_gfs',
        'carpeta': 'NOAA_FOURCASTNET_GFS',
        'nombre': 'NVIDIA FourCastNet v2 GFS (NOAA MLWP)',
        'etiqueta_corta': 'FourCastNet v2 · IA Determinista',
        'etiqueta_fuente': 'FourCastNet v2 · NVIDIA / NOAA (IA)',
        'sello_mapa': 'NVIDIA FourCastNet v2 (IA)\nNVIDIA / NOAA MLWP',
        'tipo': 'IA Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 240,
        'salto_quiver': 4,
        'salto_web': 3,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': f'{DIR_BASE}/staging/models/fourcastnet_gfs.zarr',
        'dir_anim': f'{DIR_BASE}/animations/FOURCASTNET_GFS',
        'dir_fig': f'{DIR_BASE}/figures/FOURCASTNET_GFS',
        'variables': ['temperatura', 'viento', 'viento_100m']
    },
    'pangu_gfs': {
        'id': 'pangu_gfs',
        'carpeta': 'NOAA_PANGU_GFS',
        'nombre': 'Huawei Pangu-Weather GFS (NOAA MLWP)',
        'etiqueta_corta': 'Pangu-Weather · IA Determinista',
        'etiqueta_fuente': 'Pangu-Weather · Huawei / NOAA (IA)',
        'sello_mapa': 'Huawei Pangu-Weather (IA)\nHuawei Cloud / NOAA MLWP',
        'tipo': 'IA Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 240,
        'salto_quiver': 4,
        'salto_web': 3,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': f'{DIR_BASE}/staging/models/pangu_gfs.zarr',
        'dir_anim': f'{DIR_BASE}/animations/PANGU_GFS',
        'dir_fig': f'{DIR_BASE}/figures/PANGU_GFS',
        'variables': ['temperatura', 'viento']
    }
}
