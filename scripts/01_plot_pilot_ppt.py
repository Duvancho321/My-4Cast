"""
01_plot_pilot_ppt.py — Mapa piloto de precipitación para Colombia (WN3).

__author__: "Duvan Nieves"
__copyright__: "Universidad Nacional de Colombia"
__version__: "0.0.1"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves@unal.edu.co"
__status__: "Developer"
__changues__:
    - [2026-10-29][Duvan]: Piloto de mapa de precipitación según plots-style.
"""

from sys import argv
from pathlib import Path
from xarray import open_zarr
from matplotlib import colormaps
from cartopy.crs import PlateCarree
from matplotlib.pyplot import figure
from cartopy.feature import BORDERS, COASTLINE

#%% PARÁMETROS
hora_idx  = int(argv[1]) if len(argv) > 1 else 12
ruta_zarr = '/mnt/datos/dnieves/WN3/raw/colombia_weathernext3.zarr'
ruta_png  = 'figures/piloto_ppt_colombia.png'
vmax_ppt  = 15.0

#%% CARGA Y TRANSFORMACIÓN
ds        = open_zarr(ruta_zarr)
lead_val  = ds.lead_time.values[hora_idx]
lead_h    = int(lead_val / 3.6e12)
ppt       = ds['total_precipitation_1hr_p50'].isel(init_time=0, lead_time=hora_idx) * 1000
lon_cor   = ds.lon_0p1 - 360
lat_cor   = ds.lat_0p1

#%% CONFIGURACIÓN GRÁFICA
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

#%% RENDERIZADO
im   = ax.pcolormesh(lon_cor, lat_cor, ppt, cmap=cmap, vmin=0.1, vmax=vmax_ppt,
                     transform=PlateCarree())
ax.set_extent([-80, -66, -4.5, 13.5], crs=PlateCarree())
ax.set_title(f'+{lead_h:02d} h (Mediana)', loc='left', fontsize=11, fontweight='bold')

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
