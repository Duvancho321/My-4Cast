#!/bin/bash
# watch_and_run_wn3.sh — Espera a que GitHub Actions termine de empaquetar WN3 y corre el pipeline local

LOG="/mnt/datos/dnieves/WN3/logs/wn3_watcher.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando monitoreo de GitHub Action 42215157690..." > "$LOG"

while true; do
    RESP=$(curl -s "https://api.github.com/repos/Duvancho321/My-4Cast/actions/runs/42215157690")
    STATUS=$(python3 -c "import json; d=json.loads('''$RESP'''); print(d.get('status'), d.get('conclusion'))" 2>/dev/null)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Estado: $STATUS" >> "$LOG"

    if [[ "$STATUS" == "completed success" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Release de WN3 publicado exitosamente. Ejecutando run_pipeline.sh..." >> "$LOG"
        /home/dnieves/Documentos/My-4Cast/scripts/run_pipeline.sh >> /mnt/datos/dnieves/WN3/logs/cron_pipeline.log 2>&1
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Limpiando cache del microservicio de sondeo..." >> "$LOG"
        curl -s -X POST http://localhost:8000/api/reload >> "$LOG" 2>&1
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Actualización completada con éxito." >> "$LOG"
        break
    elif [[ "$STATUS" == "completed failure" || "$STATUS" == "completed cancelled" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Error: El workflow en GitHub Actions finalizo con estado: $STATUS" >> "$LOG"
        break
    fi
    sleep 45
done
