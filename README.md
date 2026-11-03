# My-4Cast: Operational Weather Pipeline for Colombia (WeatherNext 3)

Pipeline científico automatizado para la extracción, recorte espacial, condensación estadística, almacenamiento en Zarr y generación de productos visuales de alta resolución a partir del modelo meteorológico **WeatherNext 3** (Google DeepMind) enfocado en el territorio continental, insular y marítimo de Colombia.

---

## 1. Contexto Científico y Datos

**WeatherNext 3** es un modelo numérico y de inteligencia artificial de última generación desarrollado por Google DeepMind, que asimila observaciones globales y análisis del ECMWF para generar pronósticos deterministas y probabilísticos a escala planetaria:
- **Resolución espacial**: Malla regular latitud-longitud de $0.1^\circ \times 0.1^\circ$ (~11 km).
- **Horizonte temporal**: 360 horas de anticipación (15 días de pronóstico horario continuo, paso de 1 hora).
- **Frecuencia operativa**: 4 corridas sinópticas diarias (00:00, 06:00, 12:00 y 18:00 UTC).
- **Dominio de Colombia**:
  - Latitud: $[-5.0^\circ, 16.5^\circ\text{ N}]$ (216 celdas, cubriendo desde el Trapecio Amazónico hasta el Archipiélago de San Andrés, Providencia y Santa Catalina).
  - Longitud: $[-85.0^\circ, -60.0^\circ\text{ E}]$ (251 celdas, abarcando las cuencas oceánicas del Pacífico Oriental, Caribe y la transición a la Orinoquía/Amazonía).

---

## 2. Arquitectura del Pipeline: Desacoplamiento Nube / Servidor Local

El dataset global de WeatherNext 3 se publica en Google Cloud Storage (`weathernext3_statistics_spatial`) con particiones espaciales globales completas comprimidas con Zstandard ($1 \times 1801 \times 3600$). Una consulta directa desde un servidor local implicaría descargar ~180 GB por corrida, saturando la red institucional.

Para resolver este desafío, **My-4Cast** implementa una arquitectura híbrida de alto rendimiento:

```
┌─────────────────────────────────────────────────────────────┐
│                 Google Cloud Storage (GCS)                  │
│   weathernext_3_0_0_statistics (126 variables globales)     │
└──────────────────────────────┬──────────────────────────────┘
                               │ Conexión interna 10 Gbps
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Cloud Worker (GitHub Actions Runner en GCP)        │
│          scripts/cloud_crop_colombia.py                     │
│  - Autenticación con Application Default Credentials (ADC)  │
│  - Recorte dimensional estricto a Colombia (216 x 251)      │
│  - Filtrado a 15 métricas físicas clave (90 variables)      │
│  - Segmentación en fragmentos de 1.0 GB (colombia_part_*)   │
│  - Publicación automática de Releases en GitHub             │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS CDN (Descarga estática)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Servidor Local UNAL (Medellín, Colombia)           │
│          scripts/00_fetch_cloud_wn3.py                      │
│  - Verificación ligera mediante manifest.json (< 1 KB)      │
│  - Descarga y reensamblado seguro de partes                 │
│  - Apilado atómico en almacén Zarr local (init_time)        │
│  - Generación de suite visual operativa (UHD y WhatsApp)    │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Catálogo de Variables Físicas Seleccionadas (90 Campos)

Se procesan **15 métricas físicas fundamentales**, cada una calculada para **6 estadísticas de ensamble** (`mean`, `p10`, `p25`, `p50`, `p75`, `p90`), totalizando 90 variables en el almacén:

| Grupo | Variable Base | Descripción Física | Unidad |
| :--- | :--- | :--- | :---: |
| **Precipitación** | `total_precipitation_1hr` | Precipitación horaria acumulada del ensamble | $\text{kg m}^{-2}$ ($\text{mm}$) |
| | `imerg_tp_1hr` | Precipitación calibrada con satélite IMERG | $\text{kg m}^{-2}$ ($\text{mm}$) |
| | `experimental_tp_1hr` | Estimación experimental de alta resolución | $\text{kg m}^{-2}$ ($\text{mm}$) |
| **Viento** | `u_component_of_wind_10m` | Componente zonal zonal a 10 metros | $\text{m s}^{-1}$ |
| | `v_component_of_wind_10m` | Componente meridional a 10 metros | $\text{m s}^{-1}$ |
| | `wind_speed_10m` | Magnitud escalar del viento a 10 metros | $\text{m s}^{-1}$ |
| | `u_component_of_wind_100m` | Componente zonal a 100 metros (eólica) | $\text{m s}^{-1}$ |
| | `v_component_of_wind_100m` | Componente meridional a 100 metros | $\text{m s}^{-1}$ |
| | `wind_speed_100m` | Magnitud escalar del viento a 100 metros | $\text{m s}^{-1}$ |
| **Temperatura** | `temperature_2m` | Temperatura del aire a 2 metros de superficie | $\text{K}$ (convertido a $^\circ\text{C}$) |
| **Radiación** | `surface_solar_radiation_downwards_1hr` | Radiación solar incidente en superficie | $\text{J m}^{-2}$ (o $\text{W m}^{-2}$) |
| **Nubosidad** | `total_cloud_cover` | Cobertura total de nubosidad | Fracción $[0, 1]$ |
| | `low_cloud_cover` | Nubosidad en niveles bajos | Fracción $[0, 1]$ |
| | `medium_cloud_cover` | Nubosidad en niveles medios | Fracción $[0, 1]$ |
| | `high_cloud_cover` | Nubosidad en niveles altos (cirros) | Fracción $[0, 1]$ |

---

## 4. Estructura del Almacén Zarr

El almacén definitivo opera en formato **Zarr v3** en `/mnt/datos/dnieves/WN3/raw/colombia_wn3_full.zarr`:
- **Dimensión incremental**: `init_time` (fecha/hora sinóptica de emisión).
- **Dimensión de pronóstico**: `lead_time` ($1\text{ h}$ a $360\text{ h}$).
- **Dimensiones espaciales**: `lat_0p1` (216 valores) y `lon_0p1` (251 valores).
- **Escritura atómica**: Utiliza directorios de staging temporales (`tmp_append.zarr`) para evitar corrupción ante interrupciones de red o de proceso.

---

## 5. Suite Gráfica y Productos Operativos

El pipeline genera productos visuales optimizados para análisis sinóptico y difusión ejecutiva:
1. **Precipitación horaria + Viento 10m**:
   - Paleta oficial discreta de alta legibilidad (Cifras de 0 a >70 mm).
   - Superposición de vectores de viento en malla regular espaciada.
2. **Temperatura superficial a 2m + Viento**:
   - Gradiente divergente continuo térmico ($10^\circ\text{C}$ a $38^\circ\text{C}$).
3. **Radiación solar incidente (SSRD)**:
   - Representación del ciclo diurno solar superficial en $\text{W m}^{-2}$.
4. **Formatos de exportación**:
   - **Master UHD**: $2400 \times 2160$ px a 300 DPI (3 FPS, 120 segundos para las 360 horas).
   - **WhatsApp / Móvil**: MP4 H.264 baseline con `yuv420p` y `+faststart` (< 16 MB para compatibilidad total con mensajería instantánea).

---

## 6. Instalación y Uso

### Configuración del Entorno
```bash
# Clonar repositorio
git clone https://github.com/Duvancho321/My-4Cast.git
cd My-4Cast

# Crear e instalar dependencias con micromamba o conda
micromamba create -n my-4cast python=3.11 -y
micromamba activate my-4cast
pip install -r requirements.txt
```

### Ejecución Manual del Pipeline
```bash
# Ingesta de la última corrida recortada desde GitHub Releases
python scripts/00_fetch_cloud_wn3.py

# Generación gráfica de animaciones
python scripts/01_animate_ppt.py
python scripts/01_animate_temp.py
python scripts/01_animate_radiation.py
```

### Ejecución Automatizada (Cron)
El script [`scripts/run_pipeline.sh`](scripts/run_pipeline.sh) integra todo el flujo operativo con validación de códigos de retorno (`exit 10` cuando no hay corrida nueva):
```bash
# En crontab -e:
15 0,6,12,18 * * * /home/dnieves/Documentos/My-4Cast/scripts/run_pipeline.sh >> /mnt/datos/dnieves/WN3/logs/cron_pipeline.log 2>&1
```

---

## 7. Créditos y Autoría

- **Desarrollador y Operador**: Duvan Nieves (`dnieves@unal.edu.co`)
- **Afiliación**: Universidad Nacional de Colombia (UNAL), Sede Medellín.
- **Modelo Base**: WeatherNext 3 — Google DeepMind / ECMWF.
