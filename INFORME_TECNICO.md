# Informe tecnico: Analisis y Modelado Analitico de Transacciones de Supermercado

## 1. Descripcion de los datos

El proyecto analiza un dataset de transacciones de supermercado. Cada registro representa un producto comprado dentro de una transaccion.

Variables del dataset:

- `transaction_id`: identificador de la transaccion.
- `datetime`: fecha y hora de la compra.
- `customer_id`: identificador del cliente.
- `product_id`: identificador del producto.
- `category`: categoria del producto.
- `quantity`: cantidad comprada.
- `store`: tienda o punto de venta.

El dataset no tiene precios ni montos pagados. Por eso el analisis usa metricas relativas: volumen de unidades, frecuencia de transacciones, diversidad de productos y diversidad de categorias.

## 2. Arquitectura de la solucion

La solucion se construyo como una aplicacion web con backend:

- **Frontend:** dashboard visual en HTML, CSS y JavaScript.
- **Backend:** API desarrollada con Python y FastAPI.
- **Procesamiento local:** modulo `backend/analytics.py`, encargado de limpiar datos, calcular metricas, aplicar K-Means y generar recomendaciones.
- **Procesamiento Databricks:** script `databricks/procesamiento_supermercado_databricks.py`, preparado para ejecutarse con PySpark en Databricks.
- **Datos:** archivo `data/datos_ejemplo_supermercado.csv`.

Esta arquitectura permite cargar nuevos CSV desde la interfaz. FastAPI recibe el archivo, lo procesa en Python y devuelve los resultados al dashboard.

## 3. Metodologia de analisis

El proceso implementado es:

1. Lectura del CSV desde FastAPI.
2. Normalizacion de columnas.
3. Conversion de fechas y cantidades.
4. Eliminacion de registros invalidos.
5. Calculo de indicadores descriptivos.
6. Generacion de estructuras para visualizaciones.
7. Segmentacion de clientes con K-Means.
8. Generacion de recomendaciones por co-ocurrencia de productos.

Indicadores calculados:

- Total de unidades vendidas.
- Numero de transacciones.
- Numero de clientes.
- Numero de productos.
- Top 10 productos.
- Top 10 clientes.
- Dias pico de compra.
- Categorias con mayor volumen relativo.

## 4. Visualizaciones analiticas

El dashboard incluye:

- Serie de tiempo diaria y semanal para detectar tendencias.
- Graficos de barras para productos, clientes y categorias.
- Boxplot por categoria para detectar dispersion y comportamientos atipicos.
- Heatmap de correlacion entre frecuencia, volumen, productos distintos y diversidad de categorias.
- Grafico de dispersion para visualizar clusters de clientes.

## 5. Principales hallazgos visuales

El sistema permite identificar productos con mayor rotacion, clientes con mas frecuencia de compra y dias de mayor actividad. Como no existen precios, las categorias de mayor importancia se infieren por volumen relativo de unidades.

La serie de tiempo ayuda a reconocer picos de demanda. El boxplot permite detectar categorias con mayor variabilidad de consumo. El heatmap permite observar si los clientes que compran con mayor frecuencia tambien compran mayor volumen o mas variedad de productos.

## 6. Segmentacion de clientes

Se implemento K-Means usando estas variables:

- Frecuencia de compra.
- Numero de productos distintos.
- Volumen total.
- Diversidad de categorias.

Antes de aplicar K-Means, las variables se normalizan para evitar que el volumen total domine el calculo de distancia.

El modelo genera grupos interpretables:

- Clientes de compra puntual o baja diversidad.
- Clientes frecuentes con volumen medio o alto.
- Clientes diversos, utiles para estrategias de venta cruzada.

El dashboard muestra los clusters en un grafico donde el eje X representa volumen total, el eje Y productos distintos, el color representa el cluster y el tamano del punto representa la frecuencia.

## 7. Recomendador de productos

Se desarrollo un recomendador basado en co-ocurrencia de productos dentro de una misma transaccion.

Funcionamiento:

- Para un cliente, el sistema revisa productos que ya compro y recomienda productos que suelen aparecer junto a ellos.
- Para un producto, recomienda otros productos que aparecen frecuentemente en la misma transaccion.

Este enfoque es adecuado porque el dataset no incluye precios, calificaciones ni pagos.

## 8. Procesamiento en Databricks

El archivo `databricks/procesamiento_supermercado_databricks.py` contiene el procesamiento con PySpark:

- Lectura del CSV.
- Limpieza de datos.
- Calculo de indicadores.
- Segmentacion con `pyspark.ml.clustering.KMeans`.
- Reglas de asociacion con `pyspark.ml.fpm.FPGrowth`.
- Escritura de resultados en JSON.

El script usa widgets de Databricks:

- `input_path`: ruta del CSV.
- `output_path`: ruta donde se guardan los resultados.

## 9. Incorporacion de nuevos datos

El dashboard permite cargar un CSV nuevo mediante el boton **Cargar CSV**. Cuando se carga un archivo, FastAPI lo recibe y recalcula:

- Indicadores.
- Visualizaciones.
- Segmentacion K-Means.
- Recomendaciones.

Esto cumple el requisito de generar nuevos resultados al incorporar nuevas fuentes de informacion.

## 10. Conclusiones y aplicaciones empresariales

La solucion demuestra que se puede generar valor desde datos transaccionales incluso sin precios. El volumen, frecuencia y diversidad permiten analizar comportamiento de compra, detectar productos relevantes y segmentar clientes.

Aplicaciones empresariales:

- Planificacion de inventario por productos de alta rotacion.
- Promociones basadas en productos comprados juntos.
- Programas de fidelizacion para clientes frecuentes.
- Planeacion de personal en dias pico.
- Estrategias diferenciadas por segmento de cliente.
- Analisis de categorias con alta variabilidad de consumo.

Como mejora futura se recomienda incorporar precios, costos, promociones y datos demograficos para calcular rentabilidad real y construir modelos predictivos.
