---
title: My-4Cast - Paletas y Rangos
date: 2026-10-29
tags: [my-4cast, cartografia, paletas, diseno, estandares]
status: active
---

# 🎨 Catálogo de Paletas y Rangos Físicos — My-4Cast

Este documento mantiene el registro persistente de las escalas cromáticas, niveles de corte y justificaciones físicas para cada variable pronosticada en **My-4Cast**.

Todas las paletas están implementadas de forma centralizada en [`src/paletas.py`](file:///home/dnieves/Documentos/My-4Cast/src/paletas.py).

---

## 1. Precipitación Horaria (`total_precipitation_1hr`)

- **Objetos**: `cmap_ppt`, `norm_ppt`, `colores_ppt`, `niveles_ppt`
- **Tipo**: Escala discreta meteorológica tipo Radar / NWS.
- **Unidad**: $\text{mm/h}$ (acumulado en 1 hora).
- **Manejo de Cero**: Cero o valores menores a $0.1\text{ mm/h}$ en blanco estricto (`cmap.set_under('white')`).

| Intervalo [mm/h] | Color Hex | Color Visual | Categoría Fenomenológica |
| :---: | :---: | :---: | :--- |
| **0.1 – 0.5** | `#a6f2ff` | Cian muy claro | Llovizna / precipitación marginal |
| **0.5 – 1.0** | `#32a8ff` | Cian azulado | Lluvia débil estratiforme |
| **1.0 – 2.0** | `#004cff` | Azul puro | Lluvia moderada baja |
| **2.0 – 4.0** | `#00c800` | Verde brillante | Lluvia moderada típica |
| **4.0 – 6.0** | `#009600` | Verde oscuro | Lluvia moderada a fuerte |
| **6.0 – 8.0** | `#ffea00` | Amarillo | Inicio de núcleo convectivo |
| **8.0 – 10.0** | `#ffa500` | Naranja | Celda convectiva organizada |
| **10.0 – 15.0** | `#ff0000` | Rojo intenso | Convección profunda / Chorro de bajo nivel |
| **15.0 – 20.0** | `#b40000` | Rojo oscuro | Precipitación torrencial severa |
| **20.0 – 25.0** | `#ff00ff` | Magenta brillante | Torrencial extrema local |
| **> 25.0** | `#800080` | Púrpura | Evento extraordinario / Flash flood |

---

## 2. Temperatura a 2 Metros (`temperature_2m`)

- **Objetos**: `cmap_temp`, `norm_temp`, `colores_temp`, `niveles_temp`
- **Tipo**: Gradiente bioclimático continuo extendido en ambos extremos (`extend='both'`).
- **Unidad**: $^\circ\text{C}$ (conversión de Kelvin: $T - 273.15$).
- **Manejo de Extremos**: Bajo cero en azul noche (`#1e1b4b`), calor $>40^\circ\text{C}$ en púrpura térmico (`#701a75`).

| Intervalo [°C] | Color Hex | Región / Piso Térmico en Colombia |
| :---: | :---: | :--- |
| **< 0** | `#1e1b4b` | Helada bajo cero / Glaciares y súper páramo |
| **0 – 4** | `#1d4ed8` | Páramo alto andino |
| **4 – 8** | `#2563eb` | Páramo bajo / Bosque altoandino |
| **8 – 12** | `#38bdf8` | Clima frío (Sabana de Bogotá, Pasto, Tunja) |
| **12 – 14** | `#2dd4bf` | Frío moderado de transición |
| **14 – 16** | `#34d399` | Templado bajo |
| **16 – 18** | `#4ade80` | Templado medio (Manizales, Popayán) |
| **18 – 20** | `#a3e635` | Templado cálido (Rionegro, Pereira) |
| **20 – 22** | `#facc15` | Valle de Aburrá / Medellín |
| **22 – 24** | `#fde047` | Valles interandinos medios |
| **24 – 26** | `#fbbf24` | Valle del Cauca (Cali) / Santander |
| **26 – 28** | `#f59e0b` | Tierras cálidas bajas (Neiva, Ibagué) |
| **28 – 30** | `#fb923c` | Costa Caribe / Llanos Orientales |
| **30 – 32** | `#f97316` | Calor intenso en llanura caribeña |
| **32 – 34** | `#ea580c` | Calor severo en valles secos |
| **34 – 36** | `#dc2626` | Valle del Magdalena / Desierto de La Tatacoa |
| **36 – 38** | `#b91c1c` | Desierto de La Guajira / Ola de calor |
| **38 – 40** | `#991b1b` | Calor extremo sinóptico |
| **> 40** | `#701a75` | Evento térmico extraordinario |

---

## 3. Magnitud de Viento a 10m / 100m (`wind_speed_10m`, `wind_speed_100m`)

- **Objetos**: `cmap_viento`, `norm_viento`, `colores_viento`, `niveles_viento`
- **Tipo**: Escala eólica secuencial con saturación cromática hacia ráfagas y ciclones.
- **Unidad**: $\text{m/s}$ ($1\text{ m/s} = 3.6\text{ km/h}$).
- **Manejo de Calma**: $< 0.5\text{ m/s}$ en blanco (`cmap.set_under('white')`).

| Intervalo [m/s] | Equivalente [km/h] | Color Hex | Categoría Eólica |
| :---: | :---: | :---: | :--- |
| **0.5 – 2.0** | $1.8 – 7.2$ | `#e2e8f0` | Calma / Ventolina muy leve |
| **2.0 – 4.0** | $7.2 – 14.4$ | `#93c5fd` | Brisa muy débil |
| **4.0 – 6.0** | $14.4 – 21.6$ | `#38bdf8` | Brisa moderada |
| **6.0 – 8.0** | $21.6 – 28.8$ | `#2dd4bf` | Viento regular |
| **8.0 – 10.0** | $28.8 – 36.0$ | `#4ade80` | Viento fresco |
| **10.0 – 12.0** | $36.0 – 43.2$ | `#facc15` | Viento fuerte (Alisios estándar) |
| **12.0 – 14.0** | $43.2 – 50.4$ | `#fb923c` | Muy fuerte (Alisios intensos en Guajira) |
| **14.0 – 16.0** | $50.4 – 57.6$ | `#ea580c` | Ráfagas severas locales |
| **16.0 – 18.0** | $57.6 – 64.8$ | `#dc2626` | Temporal / Vaguada caribeña |
| **18.0 – 20.0** | $64.8 – 72.0$ | `#d946ef` | Chorro del Chocó extremo |
| **20.0 – 25.0** | $72.0 – 90.0$ | `#9333ea` | Vendaval severo / Tormenta tropical |
| **> 25.0** | $> 90.0$ | `#4c0519` | Vientos ciclónicos / Huracanados |

---

## 4. Radiación Solar Superficial Horaria (`surface_solar_radiation_downwards_1hr`)

- **Objetos**: `cmap_radiacion`, `norm_radiacion`, `colores_radiacion`, `niveles_radiacion`
- **Tipo**: Escala de flujo radiativo solar con transición crepúsculo-cenit.
- **Unidad**: $\text{W/m}^2$ (conversión de Joules acumulados: $\text{SSRD} / 3600$).
- **Manejo de Noche**: $< 50\text{ W/m}^2$ en blanco (`cmap.set_under('white')`).

| Intervalo [W/m²] | Color Hex | Fase Diurna / Fenómeno Radiativo |
| :---: | :---: | :--- |
| **50 – 100** | `#312e81` | Penumbra crepuscular amanecer / atardecer |
| **100 – 200** | `#4338ca` | Luz difusa en crepúsculo |
| **200 – 300** | `#6366f1` | Amanecer nublado / Radiación baja |
| **300 – 400** | `#b45309` | Amanecer despejado / Ocre solar |
| **400 – 500** | `#d97706` | Sol de primera mañana |
| **500 – 600** | `#f59e0b` | Media mañana |
| **600 – 700** | `#fbbf24` | Sol fuerte premayoría |
| **700 – 800** | `#fde047` | Mediodía típico tropical |
| **800 – 900** | `#fef08a` | Mediodía despejado intenso |
| **900 – 1000** | `#fef9c3` | Cenit solar despejado en Colombia |
| **1000 – 1100** | `#ffedd5` | Radiación extrema de montaña |
| **> 1100** | `#fff7ed` | Picos cenitales extraordinarios por reflexión en nubes (cloud enhancement) |
