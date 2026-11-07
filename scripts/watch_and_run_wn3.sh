#!/bin/bash
# watch_and_run_wn3.sh — Espera a que GitHub Actions termine de empaquetar WN3 y corre el pipeline local
#
# Uso:
#   ./scripts/watch_and_run_wn3.sh [RUN_ID]
# Si no se indica RUN_ID, consulta el último run del workflow crop_colombia.yml.

DIR_PROYECTO="${MY4CAST_CODE_DIR:-/home/dnieves/Documentos/My-4Cast}"
DIR_DATOS="${MY4CAST_DATA_DIR:-/mnt/datos/dnieves/WN3}"
LOG_DIR="$DIR_DATOS/logs"
LOG="$LOG_DIR/wn3_watcher.log"

mkdir -p "$LOG_DIR"

# Obtención de token de GitHub si existe
TOKEN="${GITHUB_TOKEN:-}"
if [ -z "$TOKEN" ] && [ -f "$HOME/.git-credentials" ]; then
    TOKEN=$(grep 'github.com' "$HOME/.git-credentials" 2>/dev/null | head -n1 | sed -E 's/.*:([^@]+)@.*/\1/')
fi

AUTH_HEADER=()
if [ -n "$TOKEN" ]; then
    AUTH_HEADER=(-H "Authorization: Bearer $TOKEN")
fi

RUN_ID="$1"
if [ -z "$RUN_ID" ]; then
    RESP_LATEST=$(curl -s "${AUTH_HEADER[@]}" "https://api.github.com/repos/Duvancho321/My-4Cast/actions/workflows/crop_colombia.yml/runs?per_page=1")
    RUN_ID=$(python3 -c "import json, sys; d=json.loads(sys.stdin.read()); runs=d.get('workflow_runs', []); print(runs[0]['id'] if runs else '')" <<< "$RESP_LATEST" 2>/dev/null)
fi

if [ -z "$RUN_ID" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Error: No se pudo determinar el ID de ejecución de GitHub Actions." | tee -a "$LOG"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando monitoreo de GitHub Action $RUN_ID..." > "$LOG"

while true; do
    RESP=$(curl -s "${AUTH_HEADER[@]}" "https://api.github.com/repos/Duvancho321/My-4Cast/actions/runs/$RUN_ID")
    STATUS=$(python3 -c "import json, sys; d=json.loads(sys.stdin.read()); print(d.get('status'), d.get('conclusion'))" <<< "$RESP" 2>/dev/null)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Estado: $STATUS" >> "$LOG"

    if [[ "$STATUS" == "completed success" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Release de WN3 publicado exitosamente. Ejecutando run_pipeline.sh..." >> "$LOG"
        "$DIR_PROYECTO/scripts/run_pipeline.sh" >> "$LOG_DIR/cron_pipeline.log" 2>&1
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Limpiando cache del microservicio de sondeo..." >> "$LOG"
        curl -s -X POST http://localhost:8000/api/reload >> "$LOG" 2>&1
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Actualización completada con éxito." >> "$LOG"
        break
    elif [[ "$STATUS" == "completed failure" || "$STATUS" == "completed cancelled" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Error: El workflow en GitHub Actions finalizo con estado: $STATUS" >> "$LOG"
        break
    fi
    sleep 60
done
