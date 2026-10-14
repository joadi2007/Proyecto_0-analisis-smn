# Análisis de observaciones meteorológicas del SMN

Trabajo Práctico — Programación 1 (Comisión 2)

## Descripción

Herramienta de línea de comandos que trabaja con las observaciones actuales
del Servicio Meteorológico Nacional (SMN). Según el archivo que reciba por
parámetro:

- **Archivo `.txt` del SMN**: lo lee (detectando si está codificado en
  `utf-8` o `latin-1`), arma un diccionario indexado por ciudad/estación, lo
  convierte a JSON y lo guarda en la carpeta `obs_json/`.
- **Archivo `.json`**: informa la cantidad de ciudades que contiene y cuántas
  están informadas.

El archivo también incluye las funciones de análisis del Proyecto 0 (datos
faltantes por campo, rankings de ciudades más cálidas/frías y con más/menos
viento, horarios reportados y resumen), que por ahora no se invocan desde la
ejecución principal.

## Cómo ejecutarlo

```bash
python analisis_smn.py datos/estado_tiempo.txt
python analisis_smn.py obs_json/estado_tiempo.json
```

- Con un `.txt`: imprime una leyenda antes de cada acción (leer, convertir
  fechas, crear `obs_json/` si no existe, guardar) y si se completó, y al
  final la cantidad de ciudades del archivo y de ciudades informadas.
- Con un `.json`: imprime la cantidad de ciudades y de ciudades informadas.
- Sin argumentos: avisa y muestra cuántos `.txt` hay en `datos/` y cuántos
  `.json` hay en `obs_json/`.
- Con más de un argumento: avisa y termina sin hacer nada más.

## Cómo conseguir el archivo de entrada

1. Ir a la página de descarga de datos del SMN: <https://www.smn.gob.ar/descarga-de-datos>
2. Buscar la sección de **observaciones actuales** y descargar el archivo comprimido (`.rar`).
3. Descomprimirlo (en Mac, si el Finder no lo abre solo, se puede usar una app como The Unarchiver).
4. Copiar el `.txt` que queda adentro a la carpeta `datos/` del repositorio.

El archivo cambia constantemente porque son datos en vivo, así que cada
descarga es una "foto" distinta según el momento.

## Formato del JSON generado

Un objeto indexado por ciudad. Cada ciudad tiene sus datos (temperatura,
sensación térmica, humedad, dirección y velocidad del viento, presión, etc.)
y el campo `fecha_y_hora` en formato ISO 8601 sin segundos, por ejemplo
`"2026-10-01T00:00"`. Los datos que no se pudieron convertir figuran como
`null`. El archivo se guarda en `utf-8` y tiene el mismo nombre que el `.txt`
de origen.

`obs_json/` se genera solo al ejecutar el programa y no está versionado en el
repositorio (ver `.gitignore`).

## Decisiones de diseño

- El viento `"Calma"` se representa con dirección `"Calma"` y velocidad `0`
  (en vez de `None`), para no tener que filtrar casos especiales al calcular
  extremos y rankings.
- Los campos numéricos que no se pueden convertir (por ejemplo
  `"No se calcula"` en la sensación térmica) quedan como `None`.
- Se considera ciudad **informada** a la que tiene temperatura válida.
- Para detectar la codificación del `.txt`, se intenta leerlo en `utf-8` y,
  si falla, se lee en `latin-1`.

## Estructura del repositorio

```
├── README.md
├── analisis_smn.py
├── datos/          (archivos .txt del SMN)
├── obs_json/       (se genera al ejecutar, no versionado)
└── .gitignore
```