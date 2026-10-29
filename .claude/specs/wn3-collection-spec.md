# Especificación Técnica: Recolección y Almacenamiento WN3

## Objetivo
Recolectar automáticamente las salidas de pronóstico meteorológico numérico (WN3 / WRF) hacia `/mnt/datos/dnieves/WN3`, garantizando integridad de archivos y trazabilidad temporal.

## Estructura de Almacenamiento
```
/mnt/datos/dnieves/WN3/
├── raw/                      # Salidas originales NetCDF/GRIB2 (inmutables)
│   └── YYYY/
│       └── MM/
│           └── YYYYMMDD_HH/
├── staging/                  # Descargas en curso (.tmp) antes de verificar integridad
└── catalog/                  # Metadatos, inventario y registros de recolección
```

## Requisitos del Script de Descarga
1. **Atómicidad**: Descargar primero a `.tmp` o `staging/` y mover a `raw/` solo tras verificar integridad del archivo (mediante validación de cabecera con `netCDF4.Dataset` o tamaño mínimo).
2. **Idempotencia**: Si una corrida ya existe y es íntegra, no volver a descargar.
3. **Resiliencia**: Manejo de timeouts y códigos HTTP con backoff controlado.
4. **Minimalismo (`python-style`)**: Sin módulos auxiliares innecesarios ni dependencias ajenas al stack principal.
