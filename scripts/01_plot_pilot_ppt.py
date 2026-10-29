"""
01_plot_pilot_ppt.py — Mapa piloto de precipitación para Colombia (WN3).

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.0.8"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-10-29][Duvan]: Título superior sin redundancia y texto inferior centrado.
"""

from sys import argv
from sys import path as ruta_sys
from pathlib import Path
ruta_sys.append(str(Path(__file__).resolve().parents[1]))
from xarray import open_zarr
from numpy import timedelta64
from cartopy.crs import PlateCarree
from matplotlib.pyplot import figure
from src.paletas import CMAP_PPT, NORM_PPT
from cartopy.feature import BORDERS, COASTLINE, NaturalEarthFeature

#%% PARÁMETROS
hora_idx  = int(argv[1]) if len(argv) > 1 else 12
ruta_zarr = '/mnt/datos/dnieves/WN3/raw/colombia_weathernext3.zarr'
ruta_png  = '/mnt/datos/dnieves/WN3/figures/piloto_ppt_colombia.png'

#%% CARGA Y TRANSFORMACIÓN
ds        = open_zarr(ruta_zarr)
lead_val  = ds.lead_time.values[hora_idx]
lead_h    = int(lead_val / 3.6e12)
init_ts   = ds.init_time.values[0] - timedelta64(5, 'h')
init_str  = f"{str(init_ts)[:10]} {str(init_ts)[11:13]}h HL"
valid_ts  = init_ts + lead_val
valid_str = f"{str(valid_ts)[:10]} {str(valid_ts)[11:13]}h HL"
ppt       = ds['total_precipitation_1hr_p50'].isel(init_time=0, lead_time=hora_idx) * 1000
lon_cor   = ds.lon_0p1 - 360
lat_cor   = ds.lat_0p1

#%% CONFIGURACIÓN GRÁFICA
deptos = NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lines', scale='10m', facecolor='none')

fig = figure(figsize=(7, 8))
gs  = fig.add_gridspec(1, 2, width_ratios=[1, 0.04], wspace=0.08)
ax  = fig.add_subplot(gs[0, 0], projection=PlateCarree())
cax = fig.add_subplot(gs[0, 1])

[spine.set_visible(False) for spine in ax.spines.values()]
ax.gridlines(draw_labels={'bottom': True, 'left': True},
             linewidth=0.5, color='gray', alpha=0.3, linestyle='--')
ax.add_feature(COASTLINE, linewidth=0.9, edgecolor='#222222')
ax.add_feature(BORDERS, linewidth=0.8, edgecolor='#444444')
ax.add_feature(deptos, linewidth=0.45, edgecolor='#777777', linestyle=':')

#%% RENDERIZADO
im = ax.pcolormesh(lon_cor, lat_cor, ppt, cmap=CMAP_PPT, norm=NORM_PPT,
                   transform=PlateCarree())
ax.set_extent([-80, -66, -4.5, 13.5], crs=PlateCarree())
ax.set_title(f'Válido: {valid_str} (+{lead_h:02d}h)\nCorrida: {init_str} — P50 Ensamble (64 miembros)',
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

#%% GUARDADO
Path(ruta_png).parent.mkdir(parents=True, exist_ok=True)
fig.savefig(ruta_png, dpi=300, bbox_inches='tight')
