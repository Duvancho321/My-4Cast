---
title: Catálogo Completo de Variables — WeatherNext 3 (WN3)
tags: [my-4cast, wn3, variables, catalogo, metadatos]
status: active
created: 2026-10-29
---

# 📊 Catálogo de Variables de Google WeatherNext 3 (WN3)

El dataset de estadísticas espaciales de WeatherNext 3 (`gs://weathernext3_statistics_spatial`) contiene **126 variables predictivas**, derivadas de **21 variables físicas fundamentales**.

Cada variable física cuenta con **6 métricas de distribución probabilística** calculadas sobre el ensamble de 64 miembros del modelo:
- `_mean`: Media del ensamble (valor esperado determinista).
- `_p10`: Percentil 10 (límite inferior de incertidumbre, 80% intervalo de confianza).
- `_p25`: Percentil 25 (primer cuartil).
- `_p50`: Mediana del ensamble (robusta a valores atípicos y extremos asimétricos).
- `_p75`: Percentil 75 (tercer cuartil).
- `_p90`: Percentil 90 (límite superior de incertidumbre, eventos extremos).

---

## 1. Tabla Maestra de Variables Físicas

| # | Variable Base | Resolución | Unidad Nativa | Conversión Operativa | Descripción Física |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | `station_head_temperature_2m` | **0.05° (~5 km)** | $\text{K}$ | $T(^\circ\text{C}) = T(\text{K}) - 273.15$ | Temperatura del aire a 2 m corregida para estaciones terrestres. |
| **2** | `station_head_dewpoint_temperature_2m` | **0.05° (~5 km)** | $\text{K}$ | $T_d(^\circ\text{C}) = T_d(\text{K}) - 273.15$ | Temperatura de punto de rocío a 2 m para estaciones terrestres. |
| **3** | `temperature_2m` | 0.1° (~10 km) | $\text{K}$ | $T(^\circ\text{C}) = T(\text{K}) - 273.15$ | Temperatura del aire a 2 m en grilla estándar. |
| **4** | `dewpoint_temperature_2m` | 0.1° (~10 km) | $\text{K}$ | $T_d(^\circ\text{C}) = T_d(\text{K}) - 273.15$ | Punto de rocío a 2 m en grilla estándar. |
| **5** | `total_precipitation_1hr` | 0.1° (~10 km) | $\text{m}$ | $P(\text{mm}) = P(\text{m}) \times 1000$ | Precipitación total acumulada en la última hora. |
| **6** | `imerg_tp_1hr` | 0.1° (~10 km) | $\text{m}$ | $P(\text{mm}) = P(\text{m}) \times 1000$ | Precipitación horaria calibrada con radar/satélite GPM IMERG. |
| **7** | `experimental_tp_1hr` | 0.1° (~10 km) | $\text{m}$ | $P(\text{mm}) = P(\text{m}) \times 1000$ | Modelo experimental de precipitación horaria. |
| **8** | `u_component_of_wind_10m` | 0.1° (~10 km) | $\text{m s}^{-1}$ | Directo ($\text{m/s}$) | Viento zonal (oeste-este, positivo hacia el este) a 10 m. |
| **9** | `v_component_of_wind_10m` | 0.1° (~10 km) | $\text{m s}^{-1}$ | Directo ($\text{m/s}$) | Viento meridional (sur-norte, positivo hacia el norte) a 10 m. |
| **10** | `wind_speed_10m` | 0.1° (~10 km) | $\text{m s}^{-1}$ | Directo ($\text{m/s}$) | Magnitud del vector velocidad del viento a 10 m. |
| **11** | `u_component_of_wind_100m` | 0.1° (~10 km) | $\text{m s}^{-1}$ | Directo ($\text{m/s}$) | Viento zonal a 100 m (capa límite y transporte atmosférico). |
| **12** | `v_component_of_wind_100m` | 0.1° (~10 km) | $\text{m s}^{-1}$ | Directo ($\text{m/s}$) | Viento meridional a 100 m. |
| **13** | `wind_speed_100m` | 0.1° (~10 km) | $\text{m s}^{-1}$ | Directo ($\text{m/s}$) | Magnitud de la velocidad del viento a 100 m. |
| **14** | `surface_solar_radiation_downwards_1hr` | 0.1° (~10 km) | $\text{J m}^{-2}$ | $I(\text{W/m}^2) = E / 3600$ | Radiación solar global descendente acumulada en 1 hora. |
| **15** | `total_sky_direct_solar_radiation_at_surface_1hr` | 0.1° (~10 km) | $\text{J m}^{-2}$ | $I_{\text{dir}}(\text{W/m}^2) = E / 3600$ | Radiación solar directa en superficie acumulada en 1 hora. |
| **16** | `mean_sea_level_pressure` | 0.1° (~10 km) | $\text{Pa}$ | $P(\text{hPa}) = P(\text{Pa}) / 100$ | Presión atmosférica reducida al nivel medio del mar. |
| **17** | `total_cloud_cover` | 0.1° (~10 km) | Fracción $(0 - 1)$ | $\%$ cobertura $= f \times 100$ | Fracción de cielo cubierto por nubosidad total. |
| **18** | `low_cloud_cover` | 0.1° (~10 km) | Fracción $(0 - 1)$ | $\%$ cobertura $= f \times 100$ | Nubosidad baja ($< 2 \text{ km}$). |
| **19** | `medium_cloud_cover` | 0.1° (~10 km) | Fracción $(0 - 1)$ | $\%$ cobertura $= f \times 100$ | Nubosidad media ($2 - 6 \text{ km}$). |
| **20** | `high_cloud_cover` | 0.1° (~10 km) | Fracción $(0 - 1)$ | $\%$ cobertura $= f \times 100$ | Nubosidad alta ($> 6 \text{ km}$, cirros). |
| **21** | `sea_surface_temperature` | 0.1° (~10 km) | $\text{K}$ | $T_{\text{sst}}(^\circ\text{C}) = T - 273.15$ | Temperatura superficial del mar (Pacífico y Caribe). |

---

## 2. Variables Descargadas en la Prueba Inicial
En la prueba rápida de extracción sobre Colombia (`/mnt/datos/dnieves/WN3/staging/colombia_24h_test.nc`) se incluyeron únicamente **3 variables** representativas para evaluar rendimiento de I/O y transferencia:
1. `station_head_temperature_2m_mean`
2. `wind_speed_10m_mean`
3. `total_precipitation_1hr_mean`

---

## 3. Subconjunto Recomendado para el Pipeline Operativo My-4Cast

Para la ingesta periódica de Colombia (24h a 48h de horizonte), se recomienda agrupar en un paquete operativo estándar de **10 variables físicas clave** (cada una con `_mean`, `_p10`, `_p90`):

1. **Termodinámica de Superficie**: `station_head_temperature_2m`, `station_head_dewpoint_temperature_2m`.
2. **Hidrometeorología**: `total_precipitation_1hr`, `imerg_tp_1hr`.
3. **Dinámica y Transporte**: `u_component_of_wind_10m`, `v_component_of_wind_10m`, `wind_speed_10m`, `wind_speed_100m`.
4. **Radiación y Fotoquímica**: `surface_solar_radiation_downwards_1hr`.
5. **Estado Sinóptico**: `mean_sea_level_pressure`, `total_cloud_cover`.

Este conjunto balancea completitud física para modelación meteorológica y dispersión de contaminantes con un almacenamiento ultraligero (~25 MB por archivo diario comprimido).


---

## 4. Variables Atmosféricas en la Vertical (3D Pressure Levels)

WeatherNext 3 **sí incluye perfiles en la vertical**, pero están alojados en el bucket del ensamble completo:
👉 `gs://weathernext3_spatial/weathernext_3_0_0/zarr/`

> [!important] Diferencia entre los dos Buckets
> - **`gs://weathernext3_statistics_spatial` (El que usamos actualmente)**: Contiene **únicamente variables de superficie (2D)** a alta resolución (5 km y 10 km). Su gran ventaja es que **Requester Pays está DESACTIVADO** (100% gratuito sin facturación).
> - **`gs://weathernext3_spatial` (Ensamble completo 3D)**: Contiene la atmósfera tridimensional en **13 niveles de presión** y los 64 miembros individuales. Opera con **Requester Pays ACTIVADO** (requiere Billing Account en GCP).

### Niveles de Presión Disponibles (13 niveles estándar):
$$1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50 \text{ hPa}$$

### Variables Físicas 3D en cada Nivel:
1. **Geopotencial / Altura Geopotencial** ($\Phi$, $\text{m}^2 \text{s}^{-2}$ o $\text{m}$): Clave para identificación de dorsales, vaguadas y altura de geopotencial (ej. 500 hPa).
2. **Temperatura del Aire** ($T$, $\text{K}$): Perfiles térmicos verticales, estabilidad y capas de inversión térmica.
3. **Humedad Específica** ($q$, $\text{kg kg}^{-1}$): Contenido de vapor de agua en la troposfera baja y media.
4. **Viento Zonal** ($u$, $\text{m s}^{-1}$): Componente este-oeste en altura.
5. **Viento Meridional** ($v$, $\text{m s}^{-1}$): Componente norte-sur en altura.
6. **Velocidad Vertical** ($w$ o $\omega$, $\text{Pa s}^{-1}$): Ascensos/descensos dinámicos y forzamiento convectivo.
