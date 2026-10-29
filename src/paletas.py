"""
Definición centralizada de paletas cromáticas, niveles y rangos para My-4Cast.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.0.1"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-10-29][Duvan]: Paleta y norma centralizada de precipitación horaria.
"""

from matplotlib.colors import BoundaryNorm, ListedColormap

#%% PALETA DE PRECIPITACIÓN (RADAR / NWS METEOROLÓGICA)
COLORES_PPT = [
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

NIVELES_PPT = [0.1, 0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 25.0]

CMAP_PPT = ListedColormap(COLORES_PPT)
CMAP_PPT.set_under('white')
NORM_PPT = BoundaryNorm(NIVELES_PPT, ncolors=len(COLORES_PPT), extend='max')
