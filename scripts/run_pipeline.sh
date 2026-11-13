#!/bin/bash
# run_pipeline.sh — Orquestador del pipeline operativo Multimodelo (WN3 canónico + fuentes efímeras)

PYTHON="${MY4CAST_PYTHON:-/home/dnieves/micromamba/envs/my-4cast/bin/python}"
DIR_PROYECTO="${MY4CAST_CODE_DIR:-/home/dnieves/Documentos/My-4Cast}"
DIR_WEB="${MY4CAST_WEB_DIR:-/home/dnieves/Documentos/My-4Cast-Web}"
DIR_DATOS="${MY4CAST_DATA_DIR:-/mnt/datos/dnieves/WN3}"
DIR_DATOS_WEB="$DIR_DATOS/web_data"
LOG_DIR="$DIR_DATOS/logs"

mkdir -p "$LOG_DIR"

# Control de concurrencia: evitar ejecuciones simultáneas del pipeline
LOCK_FILE="/tmp/my4cast_pipeline.lock"
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Otra instancia del pipeline está en ejecución. Saliendo sin cambios."
    exit 0
fi

# Auto-curación del microservicio de sondeo local
if ! curl -sf http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Reiniciando sounding_api en GNU Screen..."
    screen -S sounding_api -X quit 2>/dev/null || true
    cd "$DIR_PROYECTO" && screen -dmS sounding_api bash -c "${PYTHON%/*}/uvicorn src.api_sounding:app --host 127.0.0.1 --port 8000 > $LOG_DIR/sounding_api.log 2>&1"
fi

echo "=========================================================="
echo "Inicio pipeline My-4Cast: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "=========================================================="

# 1. Ingesta de corrida canónica de WeatherNext 3 (almacenamiento histórico permanente)
$PYTHON "$DIR_PROYECTO/scripts/00_fetch_cloud_wn3.py"
ESTADO_WN3=$?

# 2. Ingesta efímera de otras fuentes abiertas (solo visualización y animaciones, sin acumulación histórica)
$PYTHON "$DIR_PROYECTO/scripts/00_fetch_cloud_models.py"
ESTADO_MOD=$?

if [ $ESTADO_WN3 -eq 0 ] || [ $ESTADO_MOD -eq 0 ]; then
    echo "Nuevas corridas detectadas (WN3=$ESTADO_WN3, ModelosEfimeros=$ESTADO_MOD)."

    # 3. Generación de datos web, vectores y frames espaciales para todas las fuentes activas
    echo "Exportando datos web y frames espaciales multimodelo..."
    $PYTHON "$DIR_PROYECTO/scripts/02_export_web_data.py" all

    # 4. Despliegue automático al repositorio web (Cloudflare Pages)
    echo "Sincronizando y publicando en My-4Cast-Web..."
    cd "$DIR_WEB"
    git pull --rebase origin main || true
    cp -rf "$DIR_DATOS_WEB"/* "$DIR_WEB/data/"
    git add data/
    git commit -m "chore: auto-update multimodel forecast $(date '+%Y-%m-%d %H:%M')" || true
    git push origin main
    cd "$DIR_PROYECTO"

    # Recargar la caché del microservicio de sondeo local
    curl -s -X POST http://localhost:8000/api/reload > /dev/null 2>&1 || true

    # 5. Generación de animaciones MP4 en carpetas separadas (WN3/ vs OTRAS_FUENTES/<MODELO>/)
    if [ $ESTADO_WN3 -eq 0 ]; then
        echo "Generando animaciones MP4 para WeatherNext 3..."
        $PYTHON "$DIR_PROYECTO/scripts/01_animate_ppt.py" wn3
        $PYTHON "$DIR_PROYECTO/scripts/01_animate_temp.py" wn3
        $PYTHON "$DIR_PROYECTO/scripts/01_animate_radiation.py" wn3
    fi

    if [ $ESTADO_MOD -eq 0 ]; then
        echo "Generando animaciones MP4 efímeras para fuentes externas..."
        $PYTHON "$DIR_PROYECTO/scripts/01_animate_ppt.py" ecmwf_ifs_hres,ecmwf_ifs,ecmwf_aifs_ens,ecmwf_aifs_single,noaa_gfs,dwd_icon,chirps_gefs,graphcast_gfs,xweather,ideam_wrf
        $PYTHON "$DIR_PROYECTO/scripts/01_animate_temp.py" ecmwf_ifs_hres,ecmwf_ifs,ecmwf_aifs_ens,ecmwf_aifs_single,noaa_gfs,dwd_icon,graphcast_gfs,aurora_gfs,fourcastnet_gfs,pangu_gfs,xweather,ideam_wrf
        $PYTHON "$DIR_PROYECTO/scripts/01_animate_radiation.py" ecmwf_ifs_hres,ecmwf_ifs,ecmwf_aifs_ens,ecmwf_aifs_single,noaa_gfs,dwd_icon,xweather,ideam_wrf
    fi

    # 6. Sincronización automática a Google Drive (actual e histórico para todas las fuentes)
    echo "Sincronizando animaciones a Google Drive (estructura actual/ e historico/ por modelo)..."
    $PYTHON "$DIR_PROYECTO/scripts/03_upload_drive.py" all || echo "Aviso: Falló la subida a Drive, verificar credenciales."

    echo "Pipeline completado con éxito."
elif [ $ESTADO_WN3 -eq 10 ] && [ $ESTADO_MOD -eq 10 ]; then
    echo "No hay corridas nuevas en WN3 ni en modelos efímeros. Se omite regeneración."
else
    echo "Alerta: Códigos de retorno WN3=$ESTADO_WN3, ModelosEfimeros=$ESTADO_MOD."
fi

echo "Pipeline finalizado: $(date '+%Y-%m-%d %H:%M:%S %Z')"
