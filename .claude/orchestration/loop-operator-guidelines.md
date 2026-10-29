# Orquestación con Loop Operator

## Misión de Supervisión
Garantizar que procesos desatendidos (ej. descargas cíclicas de pronósticos, reprocesamiento de series históricas WN3, pipelines de inferencia) operen de forma segura, trazable y sin fugas de recursos ni bucles infinitos de reintento.

## Protocolo de Checkpoints
- Cada pipeline largo debe persistir checkpoints en formato JSON o metadata clara:
  - Timestamp de inicio y fin por ciclo o corrida.
  - Archivos procesados con hashes o tamaños comprobados.
  - Conteo de fallos y causas raíz identificadas.
- En caso de dos checkpoints consecutivos con error idéntico (ej. fallo de conexión a servidor externo, timeout HTTP, archivo corrupto truncado), se **detiene** el bucle y se notifica con diagnóstico preciso.

## Anti-patrones Prohibidos
- Tormentas de reintentos continuos sin retroceso exponencial (exponential backoff).
- Silenciamiento de excepciones (`except: pass`) en descargas o parsing de NetCDF.
- Modificación directa de datos históricos confirmados en `/mnt/datos/dnieves/WN3/raw`.
