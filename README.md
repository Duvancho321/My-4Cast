# My-4Cast — WeatherNext 3 Pipeline for Colombia

Pipeline automatizado de ingesta, recorte espacial, síntesis estadística y visualización meteorológica de alta resolución a partir del modelo **WeatherNext 3** (Google DeepMind / ECMWF data) para el dominio geográfico de Colombia.

---

## 1. Arquitectura del Pipeline

El sistema implementa una arquitectura híbrida desacoplada para optimizar el consumo de ancho de banda y garantizar ejecuciones continuas de alta frecuencia:

```
[Google Cloud Storage (GCS)]
  └── WeatherNext 3 Global Data (126 variables, ~180 GB / corrida)
           │
           ▼
[GitHub Actions Cloud Worker] (scripts/cloud_crop_colombia.py)
  ├── Autenticación con Google ADC
  ├── Recorte espacial al dominio de Colombia (Lat: -5.0° a 16.5°, Lon: -85.0° a -60.0°)
  ├── Filtrado a las 15 variables físicas fundamentales (90 variables con percentiles)
  ├── Lead time: 1 a 360 horas (15 días de horizonte)
  └── Empaquetado y publicación como GitHub Release (colombia-wn3-latest)
           │
           ▼
[Servidor Local UNAL] (scripts/00_fetch_cloud_wn3.py)
  ├── Descarga ultraligera por HTTPS desde GitHub Releases (~2 GB en partes)
  ├── Integración atómica e incremental en formato Zarr (colombia_wn3_full.zarr)
  └── Generación automática de suite gráfica operativa (Precipitación, Viento, Temperatura, Radiación)
```

---

## 2. Variables Físicas Seleccionadas (15 Bases / 90 Campos)

Cada variable se procesa para 6 estadísticas de ensamble (`mean`, `p10`, `p25`, `p50`, `p75`, `p90`):

1. **Precipitación**:
   - `total_precipitation_1hr`
   - `imerg_tp_1hr`
   - `experimental_tp_1hr`
2. **Viento**:
   - `u_component_of_wind_10m`, `v_component_of_wind_10m`, `wind_speed_10m`
   - `u_component_of_wind_100m`, `v_component_of_wind_100m`, `wind_speed_100m`
3. **Temperatura**:
   - `temperature_2m`
4. **Radiación y Nubosidad**:
   - `surface_solar_radiation_downwards_1hr`
   - `total_cloud_cover`, `low_cloud_cover`, `medium_cloud_cover`, `high_cloud_cover`

---

## 3. Instalación y Requisitos

```bash
# Crear entorno conda / micromamba
micromamba create -n my-4cast python=3.11 -y
micromamba activate my-4cast

# Instalar dependencias
pip install -r requirements.txt
```

---

## 4. Ejecución Operativa

### Ingesta Ligera y Actualización Local
```bash
python scripts/00_fetch_cloud_wn3.py
```

### Orquestador Completo (Ingesta + Generación de Videos y Figuras)
```bash
./scripts/run_pipeline.sh
```

Los productos gráficos y animaciones (UHD Master y WhatsApp) se exportan automáticamente a los directorios configurados.

---

## Licencia y Créditos
- **Autor**: Duvan Nieves (`dnieves@unal.edu.co`)
- **Institución**: Universidad Nacional de Colombia
