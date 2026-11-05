"""
paletas.py — Definición centralizada de paletas cromáticas, niveles y rangos para My-4Cast.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.2.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-10-29][Duvan]: Paletas centralizadas de precipitacion, temperatura, viento y radiacion.
"""

from matplotlib.colors import BoundaryNorm, ListedColormap

#%% 1. PRECIPITACIÓN HORARIA (RADAR / NWS METEOROLÓGICA)
colores_ppt = [
    '#a6f2ff',  # 0.1 - 0.5 mm/h: Llovizna muy débil
    '#32a8ff',  # 0.5 - 1.0 mm/h: Lluvia débil
    '#004cff',  # 1.0 - 2.0 mm/h: Lluvia moderada baja
    '#00c800',  # 2.0 - 4.0 mm/h: Lluvia moderada
    '#009600',  # 4.0 - 6.0 mm/h: Lluvia moderada alta
    '#ffea00',  # 6.0 - 8.0 mm/h: Lluvia fuerte inicial
    '#ffa500',  # 8.0 - 10.0 mm/h: Núcleo convectivo fuerte
    '#ff0000',  # 10.0 - 15.0 mm/h: Convección muy intensa
    '#b40000',  # 15.0 - 20.0 mm/h: Torrencial severa
    '#ff00ff',  # 20.0 - 25.0 mm/h: Torrencial extrema
    '#800080',  # > 25.0 mm/h: Torrencial extraordinaria
]
niveles_ppt = [0.1, 0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 25.0]
cmap_ppt    = ListedColormap(colores_ppt)
cmap_ppt.set_under('white')
norm_ppt    = BoundaryNorm(niveles_ppt, ncolors=len(colores_ppt), extend='max')

#%% 2. TEMPERATURA A 2 METROS [°C]
colores_temp = [
    '#1e1b4b',  # < 0 °C: Helada bajo cero (Páramos / Glaciares)
    '#1d4ed8',  # 0 - 4 °C: Muy frío
    '#2563eb',  # 4 - 8 °C: Páramo frío
    '#38bdf8',  # 8 - 12 °C: Clima frío (Sabana)
    '#2dd4bf',  # 12 - 14 °C: Frío moderado
    '#34d399',  # 14 - 16 °C: Templado bajo
    '#4ade80',  # 16 - 18 °C: Templado medio
    '#a3e635',  # 18 - 20 °C: Templado agradable
    '#facc15',  # 20 - 22 °C: Cálido moderado
    '#fde047',  # 22 - 24 °C: Cálido (Valles interandinos)
    '#fbbf24',  # 24 - 26 °C: Cálido alto
    '#f59e0b',  # 26 - 28 °C: Muy cálido
    '#fb923c',  # 28 - 30 °C: Tierras bajas (Caribe / Llanos)
    '#f97316',  # 30 - 32 °C: Calor intenso
    '#ea580c',  # 32 - 34 °C: Calor severo
    '#dc2626',  # 34 - 36 °C: Muy severo (Guajira / Huila)
    '#b91c1c',  # 36 - 38 °C: Extremo
    '#991b1b',  # 38 - 40 °C: Ola de calor crítica
    '#701a75',  # > 40 °C: Calor extraordinario
]
niveles_temp = [0.0, 4.0, 8.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0, 38.0, 40.0]
cmap_temp    = ListedColormap(colores_temp)
norm_temp    = BoundaryNorm(niveles_temp, ncolors=len(colores_temp), extend='both')

#%% 3. MAGNITUD DE VIENTO A 10M / 100M [m/s]
colores_viento = [
    '#e2e8f0',  # 0.5 - 2.0 m/s: Calma / Brisa muy débil
    '#93c5fd',  # 2.0 - 4.0 m/s: Brisa ligera
    '#38bdf8',  # 4.0 - 6.0 m/s: Brisa moderada
    '#2dd4bf',  # 6.0 - 8.0 m/s: Viento regular
    '#4ade80',  # 8.0 - 10.0 m/s: Viento fresco
    '#facc15',  # 10.0 - 12.0 m/s: Viento fuerte (Alisios)
    '#fb923c',  # 12.0 - 14.0 m/s: Muy fuerte
    '#ea580c',  # 14.0 - 16.0 m/s: Ráfagas severas
    '#dc2626',  # 16.0 - 18.0 m/s: Temporal / Vórtice
    '#d946ef',  # 18.0 - 20.0 m/s: Chorro del Chocó extremo
    '#9333ea',  # 20.0 - 25.0 m/s: Tormenta tropical
    '#4c0519',  # > 25.0 m/s: Ciclónico / Huracanado
]
niveles_viento = [0.5, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 25.0]
cmap_viento    = ListedColormap(colores_viento)
cmap_viento.set_under('white')
norm_viento    = BoundaryNorm(niveles_viento, ncolors=len(colores_viento), extend='max')

#%% 4. RADIACIÓN SOLAR SUPERFICIAL [W/m²]
colores_radiacion = [
    '#312e81',  # 50 - 100 W/m²: Penumbra amanecer / atardecer
    '#4338ca',  # 100 - 200 W/m²: Crepúsculo
    '#6366f1',  # 200 - 300 W/m²: Radiación baja nublada
    '#b45309',  # 300 - 400 W/m²: Amanecer despejado
    '#d97706',  # 400 - 500 W/m²: Sol matutino
    '#f59e0b',  # 500 - 600 W/m²: Media mañana
    '#fbbf24',  # 600 - 700 W/m²: Alta radiación
    '#fde047',  # 700 - 800 W/m²: Mediodía típico
    '#fef08a',  # 800 - 900 W/m²: Mediodía despejado
    '#fef9c3',  # 900 - 1000 W/m²: Cenit tropical fuerte
    '#ffedd5',  # 1000 - 1100 W/m²: Radiación extrema
    '#fff7ed',  # > 1100 W/m²: Picos cenitales de montaña
]
niveles_radiacion = [50.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0, 1100.0]
cmap_radiacion    = ListedColormap(colores_radiacion)
cmap_radiacion.set_under('white')
norm_radiacion    = BoundaryNorm(niveles_radiacion, ncolors=len(colores_radiacion), extend='max')

#%% 5. COBERTURA NUBOSA [%]
colores_nubosidad = [
    '#0284c7',  # 10 - 20 %: Cielo mayormente despejado
    '#0ea5e9',  # 20 - 30 %: Nubosidad escasa
    '#38bdf8',  # 30 - 40 %: Nubosidad dispersa
    '#7dd3fc',  # 40 - 50 %: Parcialmente nublado
    '#bae6fd',  # 50 - 60 %: Nubosidad moderada
    '#cbd5e1',  # 60 - 70 %: Mayormente nublado
    '#e2e8f0',  # 70 - 80 %: Cubierto estratiforme
    '#f1f5f9',  # 80 - 90 %: Cubierto denso
    '#ffffff',  # 90 - 100 %: Cobertura total / Tope convectivo
]
niveles_nubosidad = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
cmap_nubosidad    = ListedColormap(colores_nubosidad)
cmap_nubosidad.set_under('white')
norm_nubosidad    = BoundaryNorm(niveles_nubosidad, ncolors=len(colores_nubosidad), extend='neither')

#%% ALIASES DE RETROCOMPATIBILIDAD
CMAP_PPT    = cmap_ppt
NORM_PPT    = norm_ppt
COLORES_PPT = colores_ppt
NIVELES_PPT = niveles_ppt
