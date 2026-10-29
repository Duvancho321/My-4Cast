---
title: Recolección y Almacenamiento WN3
tags: [my-4cast, wn3, datos, recoleccion]
status: active
created: 2026-10-28
---

# 📥 My-4Cast — Recolección y Almacenamiento WN3

## 1. Visión General
El pipeline de recolección tiene como misión asegurar la ingesta periódica y robusta de las salidas del modelo meteorológico WN3 hacia el almacenamiento local persistente en `/mnt/datos/dnieves/WN3`.

> [!important] Inmutabilidad de Datos Crudos
> Una vez que un archivo NetCDF/GRIB2 entra a `raw/`, queda marcado como de solo lectura. Ningún script de postprocesamiento o análisis debe modificar o sobreescribir datos en esta carpeta.

---

## 2. Estructura de Directorios en Almacenamiento
Ruta base: `/mnt/datos/dnieves/WN3`

```
/mnt/datos/dnieves/WN3/
├── staging/                  # Archivos temporales (.tmp) durante la descarga
├── raw/                      # Archivos de pronóstico confirmados e íntegros
│   └── YYYY/
│       └── MM/
│           └── YYYYMMDD_HH/  # Corrida inicializada en YYYY-MM-DD a las HH UTC
├── processed/                # Datasets consolidados, remuestreados o en Zarr
└── catalog/                  # Inventario de descargas, fechas disponibles y metadatos
```

---

## 3. Principios de Descarga e Integridad
1. **Descarga Atómica**: Se descarga primero en `staging/<nombre>.tmp`. Al finalizar la transferencia, se ejecuta verificación de cabeceras (`netCDF4.Dataset` o checksum) y se mueve a su destino final con `mv`.
2. **Idempotencia**: Si el archivo ya existe en `raw/` con el tamaño correcto, el script omite la descarga y lo registra como existente.
3. **Control de Fallos**: Los reintentos implementan retroceso exponencial. Si un archivo falla 3 veces consecutivas, el incidente se registra en el log sin detener las siguientes descargas.

---

## 4. Próximos Pasos Técnicos
- [ ] Definir endpoints específicos del servidor de origen (HTTP / FTP / NOMADS / SIATA).
- [ ] Implementar el script recolector en `scripts/collect_wn3.py` bajo estándar `python-style`.
- [ ] Integrar supervisión de cron con `loop-operator`.
