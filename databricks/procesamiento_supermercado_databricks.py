# Databricks notebook source
# MAGIC %md
# MAGIC # Procesamiento analitico de transacciones de supermercado
# MAGIC
# MAGIC Este script esta pensado para ejecutarse en Databricks con PySpark.
# MAGIC Lee un CSV de transacciones, limpia los datos, calcula indicadores,
# MAGIC segmenta clientes con K-Means y genera reglas de asociacion para recomendaciones.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
from pyspark.ml import Pipeline
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.fpm import FPGrowth

# COMMAND ----------

dbutils.widgets.text("input_path", "/FileStore/supermercado/datos_ejemplo_supermercado.csv")
dbutils.widgets.text("output_path", "/FileStore/supermercado/resultados")

input_path = dbutils.widgets.get("input_path")
output_path = dbutils.widgets.get("output_path")

# COMMAND ----------

raw_df = (
    spark.read.option("header", True)
    .option("inferSchema", True)
    .csv(input_path)
)

required_columns = [
    "transaction_id",
    "datetime",
    "customer_id",
    "product_id",
    "category",
    "quantity",
    "store",
]

missing_columns = [column for column in required_columns if column not in raw_df.columns]
if missing_columns:
    raise ValueError(f"Faltan columnas requeridas: {missing_columns}")

df = (
    raw_df.select(*required_columns)
    .withColumn("datetime", F.to_timestamp("datetime"))
    .withColumn("quantity", F.col("quantity").cast(DoubleType()))
    .dropna(subset=required_columns)
    .withColumn("date", F.to_date("datetime"))
    .withColumn("week", F.date_format("datetime", "yyyy-'S'ww"))
)

# COMMAND ----------

summary_df = spark.createDataFrame(
    [
        (
            float(df.agg(F.sum("quantity")).first()[0]),
            df.select("transaction_id").distinct().count(),
            df.select("customer_id").distinct().count(),
            df.select("product_id").distinct().count(),
        )
    ],
    ["total_units", "total_transactions", "total_customers", "total_products"],
)

top_products_df = (
    df.groupBy("product_id")
    .agg(F.sum("quantity").alias("units"))
    .orderBy(F.desc("units"))
    .limit(10)
)

top_customers_df = (
    df.groupBy("customer_id")
    .agg(F.countDistinct("transaction_id").alias("transactions"))
    .orderBy(F.desc("transactions"))
    .limit(10)
)

daily_peaks_df = (
    df.groupBy("date")
    .agg(F.countDistinct("transaction_id").alias("transactions"))
    .orderBy("date")
)

weekly_series_df = (
    df.groupBy("week")
    .agg(F.sum("quantity").alias("units"))
    .orderBy("week")
)

category_volume_df = (
    df.groupBy("category")
    .agg(F.sum("quantity").alias("units"))
    .orderBy(F.desc("units"))
)

# COMMAND ----------

customer_features_df = (
    df.groupBy("customer_id")
    .agg(
        F.countDistinct("transaction_id").alias("frequency"),
        F.countDistinct("product_id").alias("distinct_products"),
        F.sum("quantity").alias("total_volume"),
        F.countDistinct("category").alias("category_diversity"),
    )
)

assembler = VectorAssembler(
    inputCols=["frequency", "distinct_products", "total_volume", "category_diversity"],
    outputCol="raw_features",
)
scaler = StandardScaler(inputCol="raw_features", outputCol="features", withStd=True, withMean=True)
kmeans = KMeans(k=3, seed=42, featuresCol="features", predictionCol="cluster")
pipeline = Pipeline(stages=[assembler, scaler, kmeans])

cluster_model = pipeline.fit(customer_features_df)
clustered_customers_df = cluster_model.transform(customer_features_df)

evaluator = ClusteringEvaluator(featuresCol="features", predictionCol="cluster")
silhouette = evaluator.evaluate(clustered_customers_df)

cluster_summary_df = (
    clustered_customers_df.groupBy("cluster")
    .agg(
        F.count("*").alias("customers"),
        F.avg("frequency").alias("avg_frequency"),
        F.avg("distinct_products").alias("avg_distinct_products"),
        F.avg("total_volume").alias("avg_total_volume"),
        F.avg("category_diversity").alias("avg_category_diversity"),
    )
    .orderBy("cluster")
)

# COMMAND ----------

baskets_df = (
    df.groupBy("transaction_id")
    .agg(F.collect_set("product_id").alias("items"))
    .where(F.size("items") >= 2)
)

fpgrowth = FPGrowth(itemsCol="items", minSupport=0.02, minConfidence=0.1)
recommendation_model = fpgrowth.fit(baskets_df)

frequent_itemsets_df = recommendation_model.freqItemsets
association_rules_df = recommendation_model.associationRules

# COMMAND ----------

summary_df.write.mode("overwrite").json(f"{output_path}/summary")
top_products_df.write.mode("overwrite").json(f"{output_path}/top_products")
top_customers_df.write.mode("overwrite").json(f"{output_path}/top_customers")
daily_peaks_df.write.mode("overwrite").json(f"{output_path}/daily_peaks")
weekly_series_df.write.mode("overwrite").json(f"{output_path}/weekly_series")
category_volume_df.write.mode("overwrite").json(f"{output_path}/category_volume")
customer_features_df.write.mode("overwrite").json(f"{output_path}/customer_features")
clustered_customers_df.drop("raw_features", "features").write.mode("overwrite").json(f"{output_path}/customer_segments")
cluster_summary_df.write.mode("overwrite").json(f"{output_path}/cluster_summary")
frequent_itemsets_df.write.mode("overwrite").json(f"{output_path}/frequent_itemsets")
association_rules_df.write.mode("overwrite").json(f"{output_path}/association_rules")

print(f"Procesamiento completado. Silhouette K-Means: {silhouette}")
print(f"Resultados guardados en: {output_path}")
