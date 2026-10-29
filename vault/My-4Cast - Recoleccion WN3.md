---
title: Recolección y Acceso WeatherNext 3 (WN3)
tags: [my-4cast, wn3, weathernext, deepmind, zarr]
status: active
created: 2026-10-28
---

# 📥 My-4Cast — Recolección y Acceso a Google WeatherNext 3 (WN3)

## 1. Visión General y Acceso Aprobado
El acceso a los datasets de **WeatherNext 3 (WN3)** de **Google DeepMind & Google Research** ha sido aprobado formalmente para la cuenta `dnieves@unal.edu.co`.

WeatherNext 3 representa el estado del arte en pronóstico meteorológico numérico basado en Inteligencia Artificial:
- **Frecuencia**: Inicializaciones y pronósticos globales actualizados **cada hora**.
- **Resolución**: ~5 km en variables de superficie y ~10 km en variables de niveles de presión.
- **Formato**: Formato Zarr optimizado para la nube (*Analysis-Ready, Cloud-Optimized*).
- **Almacenamiento remoto**: Google Cloud Storage (GCS).

---

## 2. Repositorios Remotos en Google Cloud Storage
- **Bucket Espacial Principal**:
  `gs://weathernext3_spatial/weathernext_3_0_0/zarr/`
- **Bucket de Estadísticas y Ensamble**:
  `gs://weathernext3_statistics_spatial/weathernext_3_0_0_statistics/zarr/`
- **Modalidad de Facturación**: *Requester Pays* (requiere especificar el ID de proyecto GCP asociado a la cuenta de la UNAL para computar peticiones y transferencias).

---

## 3. Estrategia de Descarga y Persistencia Local
Ruta base de almacenamiento local: `/mnt/datos/dnieves/WN3`

```
/mnt/datos/dnieves/WN3/
├── staging/                  # Descargas temporales en curso o chunks en extracción
├── raw/                      # Zarr stores o NetCDF recortados confirmados
│   └── YYYY/
│       └── MM/
│           └── YYYYMMDD_HH/  # Corrida horaria de WeatherNext 3
├── processed/                # Extracciones tabulares por estación o cubos recortados
└── catalog/                  # Inventario de corridas disponibles y metadatos
```

> [!tip] Ventaja Arquitectónica de Zarr + xarray
> Al estar alojado en Zarr, **no es necesario descargar el globo completo**. Podemos realizar consultas y recortes espaciotemporales remotos (streaming con `xarray` + `gcsfs` / `obstore`) delimitando la caja geográfica de Colombia o dominio de interés, persistiendo en `/mnt/datos/dnieves/WN3/raw/` únicamente los subconjuntos relevantes.

---

## 4. Requisitos para el Acceso Operativo
1. **Autenticación GCP**:
   Configurar credenciales con la cuenta autorizada `dnieves@unal.edu.co` mediante `gcloud auth application-default login`.
2. **Proyecto GCP (Requester Pays)**:
   Definir el ID del proyecto de Google Cloud (`gcp_project_id`) donde se imputarán las operaciones de lectura.
3. **Librerías Python**:
   - `xarray`
   - `zarr`
   - `gcsfs` o `obstore`
