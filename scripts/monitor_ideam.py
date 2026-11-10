"""
Monitoreo ligero de publicación de corridas WRF IDEAM (00Z y 12Z, 10km y 5km)

__author__: "Duvan Nieves"
__copyright__: "Duvan Nieves Ruiz"
__version__: "0.1.0"
__maintaner__: "Duvan Nieves Ruiz"
__email__: "dnieves.sci@gmail.com"
__status__: "Developer"
__changues__:
    - [2026-11-10][Duvan]: monitor ligero de sondeo HTTP para registrar horarios reales de subida.
"""

#%%
from re import findall
from os import getenv, makedirs
from json import load, dump
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen

#%%
DIR_DATOS  = getenv('MY4CAST_DATA_DIR', '/mnt/datos/dnieves/WN3')
DIR_LOGS   = Path(DIR_DATOS) / 'logs'
PATH_LOG   = DIR_LOGS / 'monitor_ideam.log'
PATH_STATE = DIR_LOGS / 'monitor_ideam_state.json'
TZ_COT     = timezone(timedelta(hours=-5))

#%%
def consultar_ciclo(ciclo: str) -> dict:
    url_base = f'https://bart.ideam.gov.co/wrfideam/new_modelo/WRF{ciclo}COLOMBIA/netcdf/'
    resultado = {
        'ciclo': ciclo,
        'nc_modificado': None,
        'nc_gb': None,
        'wrfout_conteo': 0,
        'wrfout_primero': None,
        'wrfout_ultimo': None,
        'dir_5km': False,
        'archivos_5km': 0,
        'error': None
    }
    try:
        with urlopen(Request(url_base), timeout=12) as res:
            html = res.read().decode('utf-8', errors='ignore')
    except Exception as exc:
        resultado['error'] = f'Error listando directorio {ciclo}: {exc}'
        return resultado

    nc_url = f'{url_base}Colombia10kmX10km{ciclo}Z.nc'
    try:
        req_head = Request(nc_url, method='HEAD')
        with urlopen(req_head, timeout=12) as r_head:
            resultado['nc_modificado'] = r_head.getheader('Last-Modified')
            tam = int(r_head.getheader('Content-Length', 0))
            resultado['nc_gb']         = round(tam / (1024**3), 2)
    except Exception as exc_head:
        resultado['nc_modificado'] = f'No disponible ({exc_head})'

    wrfouts = sorted(set(findall(r'wrfout_d01_[0-9_\-:]+', html)))
    resultado['wrfout_conteo']  = len(wrfouts)
    resultado['wrfout_primero'] = wrfouts[0] if wrfouts else None
    resultado['wrfout_ultimo']  = wrfouts[-1] if wrfouts else None

    if 'Colombia_5km/' in html:
        resultado['dir_5km'] = True
        try:
            with urlopen(Request(f'{url_base}Colombia_5km/'), timeout=12) as res5:
                html5 = res5.read().decode('utf-8', errors='ignore')
                links = [f for f in findall(r'href="([^"]+)"', html5) if not f.startswith(('?', '/', '.'))]
                resultado['archivos_5km'] = len(links)
        except Exception:
            resultado['archivos_5km'] = -1

    return resultado

#%%
def registrar_vigilancia() -> None:
    DIR_LOGS.mkdir(parents=True, exist_ok=True)
    ahora_cot = datetime.now(TZ_COT)
    marca     = ahora_cot.strftime('%Y-%m-%d %H:%M:%S COT')

    estado_anterior = {}
    if PATH_STATE.exists():
        try:
            with open(PATH_STATE, 'r', encoding='utf-8') as f:
                estado_anterior = load(f)
        except Exception:
            estado_anterior = {}

    nuevo_estado = {
        'ultima_inspeccion': marca,
        'ciclos': {
            '00': consultar_ciclo('00'),
            '12': consultar_ciclo('12')
        }
    }

    lineas_evento = []
    hay_cambio    = False

    for c in ('00', '12'):
        actual   = nuevo_estado['ciclos'][c]
        previo   = estado_anterior.get('ciclos', {}).get(c, {})

        if actual.get('error'):
            lineas_evento.append(f'[{marca}] [ALERTA] WRF{c} error: {actual["error"]}')
            continue

        cambio_nc   = actual['nc_modificado'] != previo.get('nc_modificado')
        cambio_wrf  = actual['wrfout_conteo'] != previo.get('wrfout_conteo')
        cambio_5km  = actual['archivos_5km'] != previo.get('archivos_5km')

        if cambio_nc or cambio_wrf or cambio_5km or not previo:
            hay_cambio = True
            lineas_evento.append(
                f'[{marca}] [CAMBIO WRF{c}] '
                f'nc_modificado="{actual["nc_modificado"]}" ({actual["nc_gb"]} GB) | '
                f'wrfouts={actual["wrfout_conteo"]} '
                f'(primero={actual["wrfout_primero"] or "—"}, ultimo={actual["wrfout_ultimo"] or "—"}) | '
                f'5km={actual["archivos_5km"]} archivos'
            )

    if not hay_cambio:
        if ahora_cot.minute < 10 or not PATH_LOG.exists():
            lineas_evento.append(
                f'[{marca}] [HEARTBEAT] '
                f'WRF00: nc="{nuevo_estado["ciclos"]["00"]["nc_modificado"]}" (wrfouts={nuevo_estado["ciclos"]["00"]["wrfout_conteo"]}) | '
                f'WRF12: nc="{nuevo_estado["ciclos"]["12"]["nc_modificado"]}" (wrfouts={nuevo_estado["ciclos"]["12"]["wrfout_conteo"]})'
            )

    if lineas_evento:
        with open(PATH_LOG, 'a', encoding='utf-8') as flog:
            for l in lineas_evento:
                flog.write(l + '\n')
                print(l)

    with open(PATH_STATE, 'w', encoding='utf-8') as fstate:
        dump(nuevo_estado, fstate, indent=2, ensure_ascii=False)

#%%
if __name__ == '__main__':
    registrar_vigilancia()
