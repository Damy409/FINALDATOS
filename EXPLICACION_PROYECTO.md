# Explicacion del proyecto

## Que se construyo

Se construyo una solucion completa para analizar transacciones de supermercado usando Python, FastAPI y Databricks.

- El usuario abre un dashboard web.
- El dashboard consume una API en FastAPI.
- FastAPI procesa los datos con Python.
- El script de Databricks permite ejecutar el procesamiento analitico en un entorno Spark.

## Como funciona

1. El usuario entra a `http://127.0.0.1:8000`.
2. FastAPI entrega el dashboard.
3. El usuario procesa el CSV de ejemplo o carga un nuevo CSV.
4. FastAPI recibe los datos.
5. Python limpia y analiza el dataset.
6. El backend devuelve metricas, datos para graficas, clusters y recomendaciones.
7. El frontend pinta los resultados visualmente.

## Que se hizo en el backend

En `backend/main.py` se creo la API con FastAPI.

Endpoints:

- `/`: dashboard.
- `/api/health`: prueba de estado.
- `/api/sample`: procesa los datos de ejemplo.
- `/api/upload`: recibe un CSV nuevo.

En `backend/analytics.py` se implemento:

- Normalizacion de columnas.
- Validacion de datos.
- Calculo de indicadores.
- Top productos y clientes.
- Series de tiempo.
- Boxplot.
- Heatmap de correlacion.
- K-Means.
- Recomendador.

## Que se hizo en Databricks

En `databricks/procesamiento_supermercado_databricks.py` se creo un script PySpark para ejecutar el procesamiento en Databricks.

Ese script calcula indicadores, segmenta clientes con K-Means de Spark ML y genera reglas de asociacion con FPGrowth.

## Que se hizo en el frontend

En `frontend/index.html`, `frontend/styles.css` y `frontend/app.js` se creo un dashboard visual.

El frontend no hace el procesamiento principal. Su trabajo es:

- Enviar archivos CSV al backend.
- Recibir los resultados.
- Mostrar graficas, indicadores e interpretaciones.
- Permitir seleccionar clientes y productos para recomendaciones.

## Propuesta arquitectonica 

La propuesta arquitectónica de la solución está compuesta por cuatro capas principales: datos, procesamiento distribuido, backend y visualización. En la capa de datos se almacenan los archivos CSV con las transacciones del supermercado. Posteriormente, estos datos son procesados mediante Databricks y PySpark, donde se realizan tareas de limpieza, transformación, análisis, segmentación de clientes mediante K-Means y generación de recomendaciones. Los resultados obtenidos son expuestos a través de un backend desarrollado con FastAPI, el cual proporciona los servicios necesarios para consultar la información procesada. Finalmente, la capa de visualización, implementada mediante un dashboard web en HTML, CSS y JavaScript, permite presentar métricas, indicadores, gráficas y recomendaciones de manera interactiva para apoyar la toma de decisiones.


