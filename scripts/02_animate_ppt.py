"""
02_animate_ppt.py — Animación MP4 de pronóstico horario de precipitación (360h) para Colombia.

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.0.8"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-10-29][Duvan]: Dominio ampliado con San Andres, Caribe y Pacifico.
"""

from sys import path as ruta_sys
from pathlib import Path
ruta_sys.append(str(Path(__file__).resolve().parents[1]))
from xarray import open_zarr
from numpy import timedelta64
from cartopy.crs import PlateCarree
from matplotlib.pyplot import close, figure
from src.paletas import CMAP_PPT, NORM_PPT
from cartopy.feature import BORDERS, NaturalEarthFeature
from src.animacion import cuadro_desde_figura, escribir_mp4

#%% PARÁMETROS
ruta_zarr = '/mnt/datos/dnieves/WN3/raw/colombia_weathernext3.zarr'
ruta_mp4  = '/mnt/datos/dnieves/WN3/animations/animacion_ppt_colombia_360h.mp4'
fps_video = 12

#%% CARGA DE METADATOS Y MALLA
ds        = open_zarr(ruta_zarr)
lon_cor   = ds.lon_0p1 - 360
lat_cor   = ds.lat_0p1
n_pasos   = len(ds.lead_time)
init_ts   = ds.init_time.values[0] - timedelta64(5, 'h')
init_str  = f"{str(init_ts)[:10]} {str(init_ts)[11:13]}h HL"

#%% CONFIGURACIÓN DE FIGURA
costas = NaturalEarthFeature(category='physical', name='coastline', scale='10m', facecolor='none')
deptos = NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lines', scale='10m', facecolor='none')

fig = figure(figsize=(8.2, 7.2))
gs  = fig.add_gridspec(1, 2, width_ratios=[1, 0.035], wspace=0.06)
ax  = fig.add_subplot(gs[0, 0], projection=PlateCarree())
cax = fig.add_subplot(gs[0, 1])

[spine.set_visible(False) for spine in ax.spines.values()]
ax.gridlines(draw_labels={'bottom': True, 'left': True},
             linewidth=0.5, color='gray', alpha=0.3, linestyle='--')
ax.add_feature(costas, linewidth=0.9, edgecolor='#222222')
ax.add_feature(BORDERS, linewidth=0.8, edgecolor='#444444')
ax.add_feature(deptos, linewidth=0.45, edgecolor='#777777', linestyle=':')
ax.set_extent([-85, -60, -5.0, 16.5], crs=PlateCarree())

ppt_ini = ds['total_precipitation_1hr_p50'].isel(init_time=0, lead_time=0).values * 1000
im      = ax.pcolormesh(lon_cor, lat_cor, ppt_ini, cmap=CMAP_PPT, norm=NORM_PPT,
                        transform=PlateCarree())
titulo  = ax.set_title(f'Válido: {init_str} (+01h)\nCorrida: {init_str} — P50 Ensamble (64 miembros)',
                       loc='left', fontsize=9, fontweight='bold', linespacing=1.3)
ax.text(0.985, 0.02, 'WeatherNext 3\nGoogle DeepMind', transform=ax.transAxes,
        ha='right', va='bottom', multialignment='center', fontsize=7.5, color='#333333', linespacing=1.2,
        bbox=dict(boxstyle='square,pad=0.25', facecolor='white', alpha=0.75, edgecolor='none'))

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
        valid_ts  = init_ts + lead_val
        valid_str = f"{str(valid_ts)[:10]} {str(valid_ts)[11:13]}h HL"
        ppt_arr   = (ds['total_precipitation_1hr_p50'].isel(init_time=0, lead_time=idx).values * 1000).ravel()
        im.set_array(ppt_arr)
        titulo.set_text(f'Válido: {valid_str} (+{lead_h:02d}h)\nCorrida: {init_str} — P50 Ensamble (64 miembros)')
        yield cuadro_desde_figura(fig)

#%% COMPILACIÓN DE ANIMACIÓN
Path(ruta_mp4).parent.mkdir(parents=True, exist_ok=True)
escribir_mp4(iterar_cuadros(), ruta_mp4, fps=fps_video)
close(fig)
