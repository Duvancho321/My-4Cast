#!/bin/bash
# run_pipeline.sh — Orquestador del pipeline operativo WeatherNext 3 (My-4Cast)

PYTHON="/home/dnieves/micromamba/envs/my-4cast/bin/python"
DIR_PROYECTO="/home/dnieves/Documentos/My-4Cast"
LOG_DIR="/mnt/datos/dnieves/WN3/logs"

mkdir -p "$LOG_DIR"

echo "=========================================================="
echo "Inicio pipeline WN3: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "=========================================================="

# 1. Ingesta de corrida más reciente disponible en GCS
$PYTHON "$DIR_PROYECTO/scripts/00_get_wn3.py"
ESTADO=$?

if [ $ESTADO -eq 0 ]; then
    echo "Nueva corrida detectada e integrada. Generando figura y animacion..."
    $PYTHON "$DIR_PROYECTO/scripts/01_animate_ppt.py"
    echo "Actualizacion visual completada."
elif [ $ESTADO -eq 10 ]; then
    echo "No hay corridas nuevas en GCS. Se omite la generacion grafica."
else
    echo "Alerta: Error durante la ingesta de WeatherNext 3 (codigo $ESTADO)."
fi

echo "Pipeline finalizado: $(date '+%Y-%m-%d %H:%M:%S %Z')"
