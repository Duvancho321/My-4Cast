---
title: My-4Cast - Paletas y Rangos
date: 2026-10-29
tags: [my-4cast, cartografia, paletas, diseno, estandares]
status: active
---

# 🎨 Catálogo de Paletas y Rangos Físicos — My-4Cast

Este documento mantiene el registro persistente de las escalas cromáticas, niveles de corte y justificaciones físicas para cada variable pronosticada en **My-4Cast**.

## 1. Precipitación Horaria (`total_precipitation_1hr`)

- **Módulo de Código**: `src/paletas.py` (`CMAP_PPT`, `NORM_PPT`, `NIVELES_PPT`)
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

## 2. Variables Futuras por Estandarizar
- [ ] **Temperatura a 2m (`2m_temperature`)**: Gradiente térmico continuo centrado en el trópico ($10^\circ\text{C}$ a $38^\circ\text{C}$).
- [ ] **Viento Superficial (`10m_wind_speed` + barbas / streamlines)**: Escala Beaufort o cian a violeta.
- [ ] **Radiación Solar y Nubosidad**: Paleta solar / albedo.
