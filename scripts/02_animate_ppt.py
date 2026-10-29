"""
02_animate_ppt.py — Animación MP4 de pronóstico horario de precipitación (360h) para Colombia.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.0.1"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-10-29][Duvan]: Versión inicial con streaming y actualización de cuadros.
"""

from sys import path as ruta_sys
from pathlib import Path
ruta_sys.append(str(Path(__file__).resolve().parents[1]))
from xarray import open_zarr
from matplotlib import colormaps
from cartopy.crs import PlateCarree
from matplotlib.pyplot import close, figure
from cartopy.feature import BORDERS, COASTLINE
from src.animacion import cuadro_desde_figura, escribir_mp4

#%% PARÁMETROS
ruta_zarr = '/mnt/datos/dnieves/WN3/raw/colombia_weathernext3.zarr'
ruta_mp4  = '/mnt/datos/dnieves/WN3/animations/animacion_ppt_colombia_360h.mp4'
vmax_ppt  = 15.0
fps_video = 12

#%% CARGA DE METADATOS Y MALLA
ds        = open_zarr(ruta_zarr)
lon_cor   = ds.lon_0p1 - 360
lat_cor   = ds.lat_0p1
n_pasos   = len(ds.lead_time)

#%% CONFIGURACIÓN DE FIGURA
cmap = colormaps['YlGnBu'].copy()
cmap.set_under('white')

fig = figure(figsize=(7, 8))
gs  = fig.add_gridspec(1, 2, width_ratios=[1, 0.04], wspace=0.08)
ax  = fig.add_subplot(gs[0, 0], projection=PlateCarree())
cax = fig.add_subplot(gs[0, 1])

[spine.set_visible(False) for spine in ax.spines.values()]
ax.gridlines(draw_labels={'bottom': True, 'left': True},
             linewidth=0.5, color='gray', alpha=0.3, linestyle='--')
ax.add_feature(COASTLINE, linewidth=0.8, edgecolor='#333333')
ax.add_feature(BORDERS, linewidth=0.6, edgecolor='#555555', linestyle=':')
ax.set_extent([-80, -66, -4.5, 13.5], crs=PlateCarree())

ppt_ini = ds['total_precipitation_1hr_p50'].isel(init_time=0, lead_time=0).values * 1000
im      = ax.pcolormesh(lon_cor, lat_cor, ppt_ini, cmap=cmap, vmin=0.1, vmax=vmax_ppt,
                        transform=PlateCarree())
titulo  = ax.set_title('+001 h (Mediana)', loc='left', fontsize=11, fontweight='bold')

cbar = fig.colorbar(im, cax=cax, extend='max')
cbar.set_label('PPT [mm/h]', labelpad=8)
cbar.outline.set_visible(False)

fig.canvas.draw()
pos_ax  = ax.get_position()
pos_cax = cax.get_position()
cax.set_position([pos_cax.x0, pos_ax.y0, pos_cax.width, pos_ax.height])

#%% GENERADOR DE STREAMING
def iterar_cuadros():
    for idx in range(n_pasos):
        lead_val  = ds.lead_time.values[idx]
        lead_h    = int(lead_val / 3.6e12)
        valid_ts  = ds.init_time.values[0] + lead_val
        valid_str = str(valid_ts)[:13].replace('T', ' ') + ':00 UTC'
        ppt_arr   = (ds['total_precipitation_1hr_p50'].isel(init_time=0, lead_time=idx).values * 1000).ravel()
        im.set_array(ppt_arr)
        titulo.set_text(f'+{lead_h:03d} h | {valid_str} (Mediana)')
        yield cuadro_desde_figura(fig)

#%% COMPILACIÓN DE ANIMACIÓN
Path(ruta_mp4).parent.mkdir(parents=True, exist_ok=True)
escribir_mp4(iterar_cuadros(), ruta_mp4, fps=fps_video)
close(fig)
