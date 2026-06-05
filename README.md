# Analisis y Modelado Analitico de Transacciones de Supermercado

## Damy Villegas - A00398942

Proyecto funcional construido con:

- **Backend:** Python + FastAPI.
- **Procesamiento analitico:** Python y script PySpark para Databricks.
- **Frontend:** Dashboard web en HTML, CSS y JavaScript.
- **Datos:** CSV de transacciones de supermercado.

## Como ejecutar el programa


Se van a utilizar los siguientes comandos en la terminal:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Despues abrir en el navegador:

`http://127.0.0.1:8000`

El dashboard se cargara desde FastAPI.

## Que CSV se debe cargar

Se puede usar el archivo incluido:

`data\datos_ejemplo_supermercado.csv`

Tambien si se presiona **Procesar datos de ejemplo** en el dashboard. Ese boton va a procesar el mismo CSV de ejemplo desde el backend.

Si se quiere cargar otro archivo, debe ser un CSV con estas columnas:

- `transaction_id`
- `datetime`
- `customer_id`
- `product_id`
- `category`
- `quantity`
- `store`

La aplicacion tambien reconoce nombres equivalentes en espanol como `id_transaccion`, `fecha`, `id_cliente`, `id_producto`, `categoria`, `cantidad` y `tienda`.

## Estructura del proyecto

```text
FINALDATOS/
  backend/
    main.py
    analytics.py
  databricks/
    procesamiento_supermercado_databricks.py
  data/
    datos_ejemplo_supermercado.csv
  frontend/
    index.html
    styles.css
    app.js
  requirements.txt
  README.md
  INFORME_TECNICO.md
  EXPLICACION_PROYECTO.md
```

## Que hace cada parte

- `backend/main.py`: crea la API con FastAPI y expone los endpoints.
- `backend/analytics.py`: realiza limpieza, metricas, visualizaciones base, K-Means y recomendaciones.
- `frontend/`: muestra el dashboard visual y consume la API.
- `databricks/procesamiento_supermercado_databricks.py`: script PySpark para ejecutar el procesamiento en Databricks.
- `data/datos_ejemplo_supermercado.csv`: dataset de prueba.

## Endpoints principales

- `GET /`: abre el dashboard.
- `GET /api/health`: verifica que la API funciona.
- `GET /api/sample`: procesa el CSV de ejemplo.
- `POST /api/upload`: recibe un CSV y recalcula todo el analisis.


