#!/bin/bash
# run_pipeline.sh — Orquestador del pipeline operativo WeatherNext 3 (My-4Cast)

PYTHON="/home/dnieves/micromamba/envs/my-4cast/bin/python"
DIR_PROYECTO="/home/dnieves/Documentos/My-4Cast"
DIR_WEB="/home/dnieves/Documentos/My-4Cast-Web"
DIR_DATOS_WEB="/mnt/datos/dnieves/WN3/web_data"
LOG_DIR="/mnt/datos/dnieves/WN3/logs"

mkdir -p "$LOG_DIR"

echo "=========================================================="
echo "Inicio pipeline WN3: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "=========================================================="

# 1. Ingesta de corrida más reciente disponible desde la nube (GitHub Release)
$PYTHON "$DIR_PROYECTO/scripts/00_fetch_cloud_wn3.py"
ESTADO=$?

if [ $ESTADO -eq 0 ]; then
    echo "Nueva corrida detectada e integrada."
    
    # 2. Generación de datos y frames espaciales interactivos para la web
    echo "Exportando datos web y frames espaciales de alta resolución..."
    $PYTHON "$DIR_PROYECTO/scripts/02_export_web_data.py"
    
    # 3. Despliegue automático al repositorio web (Cloudflare Pages)
    echo "Sincronizando y publicando en My-4Cast-Web..."
    cp -ru "$DIR_DATOS_WEB"/* "$DIR_WEB/data/"
    cd "$DIR_WEB"
    git add data/
    git commit -m "chore: auto-update forecast $(date '+%Y-%m-%d %H:%M')"
    git push origin main
    
    # 4. Generación opcional de videos MP4 para redes / reportes
    echo "Generando videos mp4 de respaldo..."
    $PYTHON "$DIR_PROYECTO/scripts/01_animate_ppt.py"
    $PYTHON "$DIR_PROYECTO/scripts/01_animate_temp.py"
    $PYTHON "$DIR_PROYECTO/scripts/01_animate_radiation.py"
    echo "Pipeline completado con éxito."
elif [ $ESTADO -eq 10 ]; then
    echo "No hay corridas nuevas en GCS. Se omite la generación gráfica."
else
    echo "Alerta: Error durante la ingesta de WeatherNext 3 (código $ESTADO)."
fi

echo "Pipeline finalizado: $(date '+%Y-%m-%d %H:%M:%S %Z')"
