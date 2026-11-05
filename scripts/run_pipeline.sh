#!/bin/bash
# run_pipeline.sh — Orquestador del pipeline operativo Multimodelo (WN3 canónico + fuentes efímeras)

PYTHON="/home/dnieves/micromamba/envs/my-4cast/bin/python"
DIR_PROYECTO="/home/dnieves/Documentos/My-4Cast"
DIR_WEB="/home/dnieves/Documentos/My-4Cast-Web"
DIR_DATOS_WEB="/mnt/datos/dnieves/WN3/web_data"
LOG_DIR="/mnt/datos/dnieves/WN3/logs"

mkdir -p "$LOG_DIR"

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

    # 5. Generación de animaciones MP4 en carpetas separadas (WN3/ vs OTRAS_FUENTES/<MODELO>/)
    if [ $ESTADO_WN3 -eq 0 ]; then
        echo "Generando animaciones MP4 para WeatherNext 3..."
        $PYTHON "$DIR_PROYECTO/scripts/01_animate_ppt.py" wn3
        $PYTHON "$DIR_PROYECTO/scripts/01_animate_temp.py" wn3
        $PYTHON "$DIR_PROYECTO/scripts/01_animate_radiation.py" wn3
    fi

    if [ $ESTADO_MOD -eq 0 ]; then
        echo "Generando animaciones MP4 efímeras para fuentes externas..."
        $PYTHON "$DIR_PROYECTO/scripts/01_animate_ppt.py" ecmwf_aifs_ens,ecmwf_aifs_single,ecmwf_ifs,noaa_gfs,dwd_icon,chirps_gefs,graphcast_gfs
        $PYTHON "$DIR_PROYECTO/scripts/01_animate_temp.py" ecmwf_aifs_ens,ecmwf_aifs_single,ecmwf_ifs,noaa_gfs,dwd_icon,graphcast_gfs
        $PYTHON "$DIR_PROYECTO/scripts/01_animate_radiation.py" ecmwf_aifs_ens,ecmwf_aifs_single,ecmwf_ifs,noaa_gfs,dwd_icon
    fi

    # 6. Sincronización automática a Google Drive (WN3 con histórico; otras fuentes solo actual)
    echo "Sincronizando animaciones a Google Drive (estructura WN3 vs OTRAS_FUENTES)..."
    $PYTHON "$DIR_PROYECTO/scripts/03_upload_drive.py" all || echo "Aviso: Falló la subida a Drive, verificar credenciales."

    echo "Pipeline completado con éxito."
elif [ $ESTADO_WN3 -eq 10 ] && [ $ESTADO_MOD -eq 10 ]; then
    echo "No hay corridas nuevas en WN3 ni en modelos efímeros. Se omite regeneración."
else
    echo "Alerta: Códigos de retorno WN3=$ESTADO_WN3, ModelosEfimeros=$ESTADO_MOD."
fi

echo "Pipeline finalizado: $(date '+%Y-%m-%d %H:%M:%S %Z')"
