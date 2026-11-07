"""
01_animate_temp.py — Generación de figura clave y animación de temperatura a 2m por fuente de pronóstico.

__author__: "Duvan Nieves"
__copyright__: "Duvan Nieves Ruiz"
__version__: "0.2.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves.sci@gmail.com"
__status__: "Developer"
__changues__:
    - [2026-11-05][Duvan]: Soporte multimodelo con separación de carpetas y prefijo por fuente.
    - [2026-10-29][Duvan]: Pipeline de temperatura a 2m con vectores de viento y exportacion dual.
"""

from sys import argv, path
path.insert(0, '/home/dnieves/Documentos/My-4Cast')

from os import system
from pathlib import Path
from os.path import exists
from xarray import open_zarr
from numpy import timedelta64
from cartopy.crs import PlateCarree
from src.modelos import modelos_colombia
from matplotlib.pyplot import close, figure
from src.paletas import cmap_temp, norm_temp
from cartopy.feature import BORDERS, NaturalEarthFeature
from src.animacion import cuadro_desde_figura, escribir_mp4

#%% FUNCIÓN DE RENDERIZADO POR MODELO
def animar_modelo_temp(model_id, cfg):
    if 'temperatura' not in cfg['variables'] or not exists(cfg['ruta_zarr']):
        return

    salto     = cfg['salto_quiver']
    fps_video = 3
    dir_anim  = cfg['dir_anim']
    dir_fig   = cfg['dir_fig']
    Path(dir_anim).mkdir(parents=True, exist_ok=True)
    Path(dir_fig).mkdir(parents=True, exist_ok=True)

    ruta_png  = f'{dir_fig}/{model_id}_piloto_temp_colombia.png'
    ruta_mp4  = f'{dir_anim}/{model_id}_animacion_temp_master.mp4'
    ruta_wapp = f'{dir_anim}/{model_id}_animacion_temp.mp4'

    ds           = open_zarr(cfg['ruta_zarr'])
    lon_cor      = ds.lon_0p1.values - 360.0
    lat_cor      = ds.lat_0p1.values
    lon_q        = lon_cor[::salto]
    lat_q        = lat_cor[::salto]
    n_pasos      = len(ds.lead_time)
    hora_fig     = min(12, n_pasos - 1)
    var_temp     = 'temperature_2m_p50' if 'temperature_2m_p50' in ds.data_vars else 'temperature_2m_mean'
    tiene_viento = ('viento' in cfg['variables']
                    and 'u_component_of_wind_10m_p50' in ds.data_vars
                    and 'v_component_of_wind_10m_p50' in ds.data_vars)
    init_ts      = ds.init_time.values[-1] - timedelta64(5, 'h')
    init_str     = f"{str(init_ts)[:10]} {str(init_ts)[11:13]}h HL"

    costas = NaturalEarthFeature(category='physical', name='coastline', scale='10m', facecolor='none')
    deptos = NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lines', scale='10m', facecolor='none')

    fig = figure(figsize=(8.0, 6.4), dpi=300)
    gs  = fig.add_gridspec(1, 2, width_ratios=[1, 0.035], wspace=0.03, left=0.07, right=0.88, top=0.91, bottom=0.07)
    ax  = fig.add_subplot(gs[0, 0], projection=PlateCarree())
    cax = fig.add_subplot(gs[0, 1])

    [spine.set_visible(False) for spine in ax.spines.values()]
    gl = ax.gridlines(draw_labels={'bottom': True, 'left': True},
                      linewidth=0.5, color='gray', alpha=0.3, linestyle='--')
    gl.top_labels   = False
    gl.right_labels = False
    ax.add_feature(costas, linewidth=0.9, edgecolor='#222222')
    ax.add_feature(BORDERS, linewidth=0.8, edgecolor='#444444')
    ax.add_feature(deptos, linewidth=0.45, edgecolor='#777777', linestyle=':')
    ax.set_extent([-85, -60, -5.0, 16.5], crs=PlateCarree())

    temp_ini = ds[var_temp].isel(init_time=-1, lead_time=0).values - 273.15
    im       = ax.pcolormesh(lon_cor, lat_cor, temp_ini, cmap=cmap_temp, norm=norm_temp, transform=PlateCarree())

    if tiene_viento:
        u_ini = ds['u_component_of_wind_10m_p50'].isel(init_time=-1, lead_time=0).values[::salto, ::salto]
        v_ini = ds['v_component_of_wind_10m_p50'].isel(init_time=-1, lead_time=0).values[::salto, ::salto]
        qv    = ax.quiver(lon_q, lat_q, u_ini, v_ini, transform=PlateCarree(),
                          scale=200, width=0.0022, color='#0f172a', alpha=0.80,
                          pivot='mid', headwidth=3.2, headlength=4.0)
        ax.quiverkey(qv, 0.12, 0.045, 10, '10 m/s', labelpos='E',
                     coordinates='axes', fontproperties={'size': 8, 'weight': 'bold'},
                     facecolor='white', edgecolor='none')

    subtitulo = f"{cfg['etiqueta_corta']} — T2M y Viento 10m" if tiene_viento else f"{cfg['etiqueta_corta']} — T2M"
    titulo    = ax.set_title(f'Válido: {init_str} (+01h)\nCorrida: {init_str} — {subtitulo}',
                             loc='left', fontsize=9, fontweight='bold', linespacing=1.3)
    ax.text(0.985, 0.02, cfg['sello_mapa'], transform=ax.transAxes,
            ha='right', va='bottom', multialignment='center', fontsize=7.5, color='#333333', linespacing=1.2,
            bbox=dict(boxstyle='square,pad=0.25', facecolor='white', alpha=0.75, edgecolor='none'))

    cbar = fig.colorbar(im, cax=cax, extend='both')
    cbar.set_label('T2M [°C]', labelpad=8)
    cbar.outline.set_visible(False)

    fig.canvas.draw()
    pos_ax = ax.get_position()
    cax.set_position([pos_ax.x1 + 0.02, pos_ax.y0, 0.025, pos_ax.height])

    def iterar_cuadros():
        for idx in range(n_pasos):
            lead_val  = ds.lead_time.values[idx]
            lead_h    = int(lead_val / timedelta64(1, 'h'))
            valid_ts  = init_ts + lead_val
            valid_str = f"{str(valid_ts)[:10]} {str(valid_ts)[11:13]}h HL"
            temp_arr  = (ds[var_temp].isel(init_time=-1, lead_time=idx).values - 273.15).ravel()
            im.set_array(temp_arr)
            if tiene_viento:
                u_arr = ds['u_component_of_wind_10m_p50'].isel(init_time=-1, lead_time=idx).values[::salto, ::salto]
                v_arr = ds['v_component_of_wind_10m_p50'].isel(init_time=-1, lead_time=idx).values[::salto, ::salto]
                qv.set_UVC(u_arr, v_arr)
            titulo.set_text(f'Válido: {valid_str} (+{lead_h:02d}h)\nCorrida: {init_str} — {subtitulo}')
            if idx == hora_fig:
                fig.savefig(ruta_png, dpi=300, bbox_inches='tight')
            yield cuadro_desde_figura(fig)

    print(f'[{model_id}] Renderizando animación de temperatura ({n_pasos} cuadros) -> {ruta_wapp}...', flush=True)
    escribir_mp4(iterar_cuadros(), ruta_mp4, fps=fps_video)
    close(fig)
    cmd_wapp = f'ffmpeg -y -i "{ruta_mp4}" -vf "scale=1200:960" -c:v libx264 -pix_fmt yuv420p -profile:v main -movflags +faststart -crf 23 "{ruta_wapp}" > /dev/null 2>&1 && rm -f "{ruta_mp4}"'
    system(cmd_wapp)

#%% EJECUCIÓN PRINCIPAL
if __name__ == '__main__':
    objetivo = argv[1] if len(argv) > 1 else 'wn3'
    for m_id, cfg in modelos_colombia.items():
        if objetivo in ('all', m_id) or m_id in objetivo.split(','):
            animar_modelo_temp(m_id, cfg)
