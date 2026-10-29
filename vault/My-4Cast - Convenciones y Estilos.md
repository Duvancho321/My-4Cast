---
title: Convenciones y Estilos Operativos
tags: [my-4cast, estilo, python, ciencia]
status: active
created: 2026-10-28
---

# 📐 My-4Cast — Convenciones y Estilos Operativos

Este documento consolida las tres reglas de oro metodológicas del proyecto para garantizar persistencia y uniformidad en el código y la documentación.

---

## 1. Código Python: `python-style` (v2.5.0)

### Escalera de Solución (PE)
1. ¿Hace falta? Si es especulativo, se omite.
2. Reusar librerías instaladas y lo nativo de `xarray` / `pandas` / `numpy`.
3. Nunca añadir funciones auxiliares nuevas (`PS-01`) ni variables temporales intermedias (`PS-02`).
4. Bug = Causa raíz: corregir en la función compartida, nunca parches en los llamadores (`PE-03`).

### Formato y Reglas de Oro
- **Header Obligatorio (UNAL)**:
  ```python
  """
  <Descripción breve del script>

  __author__: "Duvan Nieves"
  __copyright__: "Universidad Nacional de Colombia"
  __version__: "0.0.1"
  __maintaner__: "Duvan Nieves Ruiz"
  __email__: "dnieves@unal.edu.co"
  __status__: "Developer"
  __changues__:
      - [YYYY-MM-DD][Duvan]: Descripción máx 50 chars.
  """
  ```
- **Imports**: Solo imports específicos (`from xarray import open_dataset`), ordenados de menor a mayor longitud de línea (lado derecho de pirámide). Prohibido `import xarray as xr`.
- **Alineación por Chunk**: Delimitados por `#%%`. El signo `=` de todas las asignaciones debe estar perfectamente alineado verticalmente.
- **Comentarios**: Cero comentarios obvios o narrativos. Solo documentar el *por qué*, supuestos físicos, unidades o fuentes.

---

## 2. Redacción Científica: `real-sci-write`

- **Orden de Prioridad**: Fidelidad > Arquitectura > Consistencia > Claridad > Naturalidad.
- **Fidelidad Numérica**: Ninguna afirmación debe ser más fuerte que la evidencia que la respalda.
- **Anti-patrones**: Eliminar lenguaje inflado de IA, metáforas decorativas ("tapiz", "piedra angular"), y narrativas innecesarias.

---

## 3. Operación de Bucles: `loop-operator`

- **Checkpoints**: Monitorear y registrar el avance de ejecuciones continuas (descargas, entrenamientos).
- **Parada de Emergencia**: Escalar y detener ante 2 checkpoints consecutivos con el mismo error o estancamiento de avance.
