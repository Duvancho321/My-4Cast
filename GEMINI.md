# Directrices y Contexto del Proyecto My-4Cast

## 1. Entorno de Trabajo
- **Directorio de Código**: `/home/dnieves/Documentos/My-4Cast` (producción y desarrollo operan en este mismo path).
- **Almacén Base de Datos y Productos**: `/mnt/datos/dnieves/WN3` (datos crudos protegidos `raw/`, procesados `processed/`, figuras `figures/`, animaciones `animations/`, staging `staging/`).
- **Política de Archivos de Salida**: Todas las figuras (`.png`, `.pdf`) y videos (`.mp4`) se guardan estrictamente en `/mnt/datos/dnieves/WN3/figures/` y `/mnt/datos/dnieves/WN3/animations/`. Prohibido dejarlos en el `home` o rastrearlos en Git.
- **Vault de Documentación**: `vault/` (gestión de conocimiento persistente con Obsidian).

## 2. Roles y Estilos Mandatorios
- **python-style activo**:
  - Código minimalista, orden de decisión PE (parar en el peldaño más corto que funcione).
  - Prohibido agregar funciones auxiliares innecesarias (`PS-01`) o variables temporales intermedias (`PS-02`).
  - Prohibido `import paquete as alias`; siempre imports específicos (`from xarray import open_dataset`), ordenados por longitud de menor a mayor (pirámide).
  - Chunks delimitados por `#%%` con alineación vertical estricta del `=`.
  - Header de script obligatorio: UNAL (`dnieves@unal.edu.co`, "Universidad Nacional de Colombia").
- **real-sci-write activo**:
  - Redacción técnica/científica sobria, rigurosa y directa. Cero tics o adjetivos vacíos de IA.
  - Toda afirmación respaldada por evidencia numérica o física explícita.
- **loop-operator activo**:
  - Supervisión de ejecuciones continuas y tareas batch. Detención ante fallos repetidos o estancamiento.

## 3. Política de Seguridad y Permisos
- Auto-aprobación activa para lecturas, inspecciones, scripts de documentación `.md`, `.canvas`, `.base` y trabajo local en `My-4Cast` y `WN3`.
- Bloqueo estricto (`force_ask`) para cualquier operación destructiva o sobre rutas de sistema / protegidas en `.protected_paths`.
