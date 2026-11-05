"""
modelos.py — Registro centralizado de modelos de pronóstico y política de almacenamiento (WN3 canónico vs. fuentes efímeras).

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.1.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-11-05][Duvan]: Definición de fuentes operativas para Colombia y dominios futuros (ENSO, MJO, Ciclones).
"""

#%% DOMINIOS MACRO DE LA PLATAFORMA
dominios_plataforma = {
    'colombia': {
        'id': 'colombia',
        'nombre': 'Colombia (Alta Resolución)',
        'activo': True,
        'descripcion': 'Pronóstico multimodelo de superficie y viento para las 32 capitales departamentales y municipios prioritarios.'
    },
    'enso': {
        'id': 'enso',
        'nombre': 'ENSO (Pacífico Tropical)',
        'activo': False,
        'descripcion': 'Monitoreo y pronóstico de anomalías térmicas y acoplamiento océano-atmósfera en las regiones Niño.'
    },
    'mjo': {
        'id': 'mjo',
        'nombre': 'MJO (Oscilación Madden-Julian)',
        'activo': False,
        'descripcion': 'Seguimiento subestacional de pulsos convectivos intratropicales y fase activa sobre Suramérica.'
    },
    'ciclones_tropicales': {
        'id': 'ciclones_tropicales',
        'nombre': 'Ciclones Tropicales (Atlántico y Caribe)',
        'activo': False,
        'descripcion': 'Trayectorias de ensamble, intensidad e impactos costeros sobre el mar Caribe y archipiélago.'
    }
}

#%% CATÁLOGO DE MODELOS DE PRONÓSTICO PARA COLOMBIA
modelos_colombia = {
    'wn3': {
        'id': 'wn3',
        'carpeta': 'WN3',
        'nombre': 'WeatherNext 3 (Google DeepMind / ECMWF)',
        'etiqueta_corta': 'WeatherNext 3 (IA Ensamble)',
        'sello_mapa': 'WeatherNext 3\nGoogle DeepMind',
        'tipo': 'IA Ensamble (64 miembros)',
        'resolucion': '0.1° (~11 km)',
        'paso_h': 1,
        'horizonte_h': 360,
        'salto_quiver': 10,
        'salto_web': 6,
        'almacenamiento': 'canonico_historico',
        'ruta_zarr': '/mnt/datos/dnieves/WN3/raw/colombia_wn3_full.zarr',
        'dir_anim': '/mnt/datos/dnieves/WN3/animations/WN3',
        'dir_fig': '/mnt/datos/dnieves/WN3/figures/WN3',
        'variables': [
            'precipitacion', 'precipitacion_imerg', 'precipitacion_exp',
            'temperatura', 'viento', 'viento_100m', 'radiacion',
            'nubosidad_total', 'nubosidad_baja', 'nubosidad_media', 'nubosidad_alta'
        ]
    },
    'ecmwf_aifs_ens': {
        'id': 'ecmwf_aifs_ens',
        'carpeta': 'OTRAS_FUENTES/ECMWF_AIFS_ENS',
        'nombre': 'ECMWF AIFS ENS 15-Day (Open)',
        'etiqueta_corta': 'ECMWF AIFS ENS (IA 51m)',
        'sello_mapa': 'ECMWF AIFS ENS\nOpen AI Forecast',
        'tipo': 'IA Ensamble (51 miembros)',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 360,
        'salto_quiver': 4,
        'salto_web': 3,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': '/mnt/datos/dnieves/WN3/staging/models/ecmwf_aifs_ens.zarr',
        'dir_anim': '/mnt/datos/dnieves/WN3/animations/OTRAS_FUENTES/ECMWF_AIFS_ENS',
        'dir_fig': '/mnt/datos/dnieves/WN3/figures/OTRAS_FUENTES/ECMWF_AIFS_ENS',
        'variables': ['precipitacion', 'temperatura', 'viento', 'viento_100m', 'radiacion', 'nubosidad_total']
    },
    'ecmwf_aifs_single': {
        'id': 'ecmwf_aifs_single',
        'carpeta': 'OTRAS_FUENTES/ECMWF_AIFS_SINGLE',
        'nombre': 'ECMWF AIFS Single 15-Day (Open)',
        'etiqueta_corta': 'ECMWF AIFS Single (IA)',
        'sello_mapa': 'ECMWF AIFS Single\nOpen AI Forecast',
        'tipo': 'IA Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 360,
        'salto_quiver': 4,
        'salto_web': 3,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': '/mnt/datos/dnieves/WN3/staging/models/ecmwf_aifs_single.zarr',
        'dir_anim': '/mnt/datos/dnieves/WN3/animations/OTRAS_FUENTES/ECMWF_AIFS_SINGLE',
        'dir_fig': '/mnt/datos/dnieves/WN3/figures/OTRAS_FUENTES/ECMWF_AIFS_SINGLE',
        'variables': ['precipitacion', 'temperatura', 'viento', 'viento_100m', 'radiacion', 'nubosidad_total']
    },
    'ecmwf_ifs': {
        'id': 'ecmwf_ifs',
        'carpeta': 'OTRAS_FUENTES/ECMWF_IFS',
        'nombre': 'ECMWF IFS ENS 15-Day (Open)',
        'etiqueta_corta': 'ECMWF IFS ENS (51m)',
        'sello_mapa': 'ECMWF IFS ENS\nOpen Forecast',
        'tipo': 'Físico Ensamble (51 miembros)',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 3,
        'horizonte_h': 360,
        'salto_quiver': 4,
        'salto_web': 3,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': '/mnt/datos/dnieves/WN3/staging/models/ecmwf_ifs.zarr',
        'dir_anim': '/mnt/datos/dnieves/WN3/animations/OTRAS_FUENTES/ECMWF_IFS',
        'dir_fig': '/mnt/datos/dnieves/WN3/figures/OTRAS_FUENTES/ECMWF_IFS',
        'variables': ['precipitacion', 'temperatura', 'viento', 'viento_100m', 'radiacion', 'nubosidad_total']
    },
    'noaa_gfs': {
        'id': 'noaa_gfs',
        'carpeta': 'OTRAS_FUENTES/NOAA_GFS',
        'nombre': 'NOAA GFS 16-Day Forecast',
        'etiqueta_corta': 'NOAA GFS (0.25°)',
        'sello_mapa': 'NOAA GFS 0.25°\nNCEP Forecast',
        'tipo': 'Físico Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 1,
        'horizonte_h': 384,
        'salto_quiver': 4,
        'salto_web': 3,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': '/mnt/datos/dnieves/WN3/staging/models/noaa_gfs.zarr',
        'dir_anim': '/mnt/datos/dnieves/WN3/animations/OTRAS_FUENTES/NOAA_GFS',
        'dir_fig': '/mnt/datos/dnieves/WN3/figures/OTRAS_FUENTES/NOAA_GFS',
        'variables': ['precipitacion', 'temperatura', 'viento', 'viento_100m', 'radiacion', 'nubosidad_total']
    },
    'dwd_icon': {
        'id': 'dwd_icon',
        'carpeta': 'OTRAS_FUENTES/DWD_ICON',
        'nombre': 'DWD ICON Global (Open)',
        'etiqueta_corta': 'DWD ICON (0.125°)',
        'sello_mapa': 'DWD ICON Global\nDeutscher Wetterdienst',
        'tipo': 'Físico Determinista',
        'resolucion': '0.125° (~13 km)',
        'paso_h': 3,
        'horizonte_h': 180,
        'salto_quiver': 8,
        'salto_web': 5,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': '/mnt/datos/dnieves/WN3/staging/models/dwd_icon.zarr',
        'dir_anim': '/mnt/datos/dnieves/WN3/animations/OTRAS_FUENTES/DWD_ICON',
        'dir_fig': '/mnt/datos/dnieves/WN3/figures/OTRAS_FUENTES/DWD_ICON',
        'variables': ['precipitacion', 'temperatura', 'viento', 'radiacion', 'nubosidad_total']
    },
    'chirps_gefs': {
        'id': 'chirps_gefs',
        'carpeta': 'OTRAS_FUENTES/CHIRPS_GEFS',
        'nombre': 'UCSB CHIRPS-GEFS v3 16-Day',
        'etiqueta_corta': 'CHIRPS-GEFS v3 (0.05°)',
        'sello_mapa': 'CHIRPS-GEFS v3\nUCSB CHC (0.05°)',
        'tipo': 'Híbrido Satélite + GEFS',
        'resolucion': '0.05° (~5 km)',
        'paso_h': 24,
        'horizonte_h': 384,
        'salto_quiver': 12,
        'salto_web': 10,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': '/mnt/datos/dnieves/WN3/staging/models/chirps_gefs.zarr',
        'dir_anim': '/mnt/datos/dnieves/WN3/animations/OTRAS_FUENTES/CHIRPS_GEFS',
        'dir_fig': '/mnt/datos/dnieves/WN3/figures/OTRAS_FUENTES/CHIRPS_GEFS',
        'variables': ['precipitacion']
    },
    'graphcast_gfs': {
        'id': 'graphcast_gfs',
        'carpeta': 'OTRAS_FUENTES/GRAPHCAST_GFS',
        'nombre': 'GraphCast GFS (Google DeepMind / NOAA)',
        'etiqueta_corta': 'GraphCast GFS (IA)',
        'sello_mapa': 'GraphCast GFS\nGoogle / NOAA MLWP',
        'tipo': 'IA Determinista',
        'resolucion': '0.25° (~28 km)',
        'paso_h': 6,
        'horizonte_h': 240,
        'salto_quiver': 4,
        'salto_web': 3,
        'almacenamiento': 'efimero_visualizacion',
        'ruta_zarr': '/mnt/datos/dnieves/WN3/staging/models/graphcast_gfs.zarr',
        'dir_anim': '/mnt/datos/dnieves/WN3/animations/OTRAS_FUENTES/GRAPHCAST_GFS',
        'dir_fig': '/mnt/datos/dnieves/WN3/figures/OTRAS_FUENTES/GRAPHCAST_GFS',
        'variables': ['precipitacion', 'temperatura', 'viento']
    }
}
