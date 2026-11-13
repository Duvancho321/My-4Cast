"""
Escritura de animaciones MP4 desde figuras de matplotlib con imageio/ffmpeg.

__author__: "Duvan Nieves"
__copyright__: "Duvan Nieves Ruiz"
__version__: "0.0.1"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves.sci@gmail.com"
__status__: "Developer"
__changues__:
    - [2026-10-29][Duvan]: Modulo base para streaming de animaciones.
"""

from numpy import asarray
from os.path import exists
from imageio import get_writer
from matplotlib.image import imread

RUTA_LOGO = '/home/dnieves/Documentos/My-4Cast-Web/icons/favicon-192.png'

#%% FUNCIONES
cuadro_desde_figura = lambda fig: (fig.canvas.draw(), asarray(fig.canvas.buffer_rgba())[:, :, :3].copy())[1]


def escribir_mp4(cuadros, ruta, fps=3):
    with get_writer(ruta, fps=fps, quality=8, macro_block_size=16) as escritor:
        [escritor.append_data(cuadro) for cuadro in cuadros]


def agregar_logo(fig, pos_ax, alto=0.068):
    if not exists(RUTA_LOGO):
        return
    ancho   = alto * (fig.get_figheight() / fig.get_figwidth())
    ax_logo = fig.add_axes([pos_ax.x1 + 0.008, pos_ax.y1 + 0.008, ancho, alto])
    ax_logo.imshow(imread(RUTA_LOGO))
    ax_logo.axis('off')
