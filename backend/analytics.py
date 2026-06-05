from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


COLUMN_ALIASES = {
    "transaction_id": ["transaction_id", "id_transaccion", "id de transaccion", "transaccion", "ticket", "invoice"],
    "datetime": ["datetime", "fecha_hora", "fecha y hora", "fecha", "date", "timestamp"],
    "customer_id": ["customer_id", "id_cliente", "id de cliente", "cliente", "customer"],
    "product_id": ["product_id", "id_producto", "id de producto", "producto", "product"],
    "category": ["category", "categoria", "categoría", "categoria_producto", "categoria del producto"],
    "quantity": ["quantity", "cantidad", "cantidad_comprada", "unidades"],
    "store": ["store", "tienda", "punto_venta", "punto de venta", "sucursal"],
}


@dataclass
class DatasetSource:
    name: str
    dataframe: pd.DataFrame


def load_sample_dataset() -> DatasetSource:
    sample_path = Path(__file__).resolve().parents[1] / "data" / "datos_ejemplo_supermercado.csv"
    return DatasetSource(name="datos_ejemplo_supermercado.csv", dataframe=pd.read_csv(sample_path))


def load_uploaded_dataset(filename: str, content: bytes) -> DatasetSource:
    text = content.decode("utf-8-sig")
    return DatasetSource(name=filename, dataframe=pd.read_csv(StringIO(text)))


def analyze_dataset(source: DatasetSource) -> dict[str, Any]:
    df = normalize_dataframe(source.dataframe)
    if df.empty:
        raise ValueError("El archivo no contiene registros validos para analizar.")

    customer_features = build_customer_features(df)
    clustered = kmeans(customer_features, k=min(3, len(customer_features)))
    recommendations = build_recommendations(df)

    return {
        "source": {
            "name": source.name,
            "rows": int(len(df)),
            "date_min": df["datetime"].min().strftime("%Y-%m-%d"),
            "date_max": df["datetime"].max().strftime("%Y-%m-%d"),
        },
        "kpis": {
            "total_units": int(df["quantity"].sum()),
            "total_transactions": int(df["transaction_id"].nunique()),
            "total_customers": int(df["customer_id"].nunique()),
            "total_products": int(df["product_id"].nunique()),
        },
        "executive": {
            "top_products": records(df.groupby("product_id")["quantity"].sum().sort_values(ascending=False).head(10)),
            "top_customers": records(df.groupby("customer_id")["transaction_id"].nunique().sort_values(ascending=False).head(10)),
            "daily_peaks": records(df.groupby(df["datetime"].dt.strftime("%Y-%m-%d"))["transaction_id"].nunique()),
            "category_volume": records(df.groupby("category")["quantity"].sum().sort_values(ascending=False)),
        },
        "visuals": {
            "daily_time_series": records(df.groupby(df["datetime"].dt.strftime("%Y-%m-%d"))["quantity"].sum()),
            "weekly_time_series": records(df.groupby(df["datetime"].dt.strftime("%Y-S%U"))["quantity"].sum()),
            "boxplot_by_category": build_boxplot(df),
            "correlation_heatmap": build_correlation(customer_features),
        },
        "advanced": {
            "customer_segments": clustered,
            "recommendations": recommendations,
            "cluster_descriptions": describe_clusters(clustered),
        },
        "insights": build_insights(df, clustered),
    }


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    normalized_lookup = {clean_column(col): col for col in df.columns}
    rename_map = {}
    missing = []

    for target, aliases in COLUMN_ALIASES.items():
        original = next((normalized_lookup.get(clean_column(alias)) for alias in aliases if clean_column(alias) in normalized_lookup), None)
        if original:
            rename_map[original] = target
        else:
            missing.append(target)

    if missing:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(missing)}")

    clean = df.rename(columns=rename_map)[list(COLUMN_ALIASES.keys())].copy()
    clean["datetime"] = pd.to_datetime(clean["datetime"], errors="coerce")
    clean["quantity"] = pd.to_numeric(clean["quantity"], errors="coerce")
    clean = clean.dropna(subset=["transaction_id", "datetime", "customer_id", "product_id", "category", "quantity", "store"])
    clean["transaction_id"] = clean["transaction_id"].astype(str)
    clean["customer_id"] = clean["customer_id"].astype(str)
    clean["product_id"] = clean["product_id"].astype(str)
    clean["category"] = clean["category"].astype(str)
    clean["store"] = clean["store"].astype(str)
    return clean


def clean_column(value: str) -> str:
    return (
        str(value)
        .lower()
        .replace("_", " ")
        .replace("-", " ")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
        .strip()
    )


def records(series: pd.Series) -> list[dict[str, Any]]:
    return [{"label": str(index), "value": float(value) if value % 1 else int(value)} for index, value in series.items()]


def build_customer_features(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("customer_id")
        .agg(
            frequency=("transaction_id", "nunique"),
            distinct_products=("product_id", "nunique"),
            total_volume=("quantity", "sum"),
            category_diversity=("category", "nunique"),
        )
        .reset_index()
    )


def kmeans(features: pd.DataFrame, k: int) -> list[dict[str, Any]]:
    if features.empty:
        return []

    numeric_cols = ["frequency", "distinct_products", "total_volume", "category_diversity"]
    x = features[numeric_cols].astype(float).to_numpy()
    min_values = x.min(axis=0)
    ranges = np.where(x.max(axis=0) - min_values == 0, 1, x.max(axis=0) - min_values)
    x_norm = (x - min_values) / ranges
    centroids = x_norm[:k].copy()
    labels = np.zeros(len(x_norm), dtype=int)

    for _ in range(30):
        distances = np.linalg.norm(x_norm[:, None, :] - centroids[None, :, :], axis=2)
        labels = distances.argmin(axis=1)
        for cluster in range(k):
            members = x_norm[labels == cluster]
            if len(members):
                centroids[cluster] = members.mean(axis=0)

    result = features.copy()
    result["cluster"] = labels + 1
    return result.to_dict(orient="records")


def build_boxplot(df: pd.DataFrame) -> list[dict[str, Any]]:
    grouped = df.groupby(["category", "customer_id"])["quantity"].sum().reset_index()
    output = []
    for category, group in grouped.groupby("category"):
        values = group["quantity"].to_numpy()
        output.append(
            {
                "label": category,
                "min": float(np.min(values)),
                "q1": float(np.quantile(values, 0.25)),
                "median": float(np.quantile(values, 0.5)),
                "q3": float(np.quantile(values, 0.75)),
                "max": float(np.max(values)),
            }
        )
    return output


def build_correlation(features: pd.DataFrame) -> list[dict[str, Any]]:
    labels = {
        "frequency": "Frecuencia",
        "distinct_products": "Productos distintos",
        "total_volume": "Volumen total",
        "category_diversity": "Diversidad categorias",
    }
    corr = features[list(labels.keys())].corr(numeric_only=True).fillna(0)
    return [
        {"row": labels[row], "column": labels[col], "value": round(float(corr.loc[row, col]), 3)}
        for row in corr.index
        for col in corr.columns
    ]


def build_recommendations(df: pd.DataFrame) -> dict[str, Any]:
    baskets = df.groupby("transaction_id")["product_id"].apply(lambda values: sorted(set(values))).tolist()
    cooccurrence: dict[str, dict[str, int]] = {}
    for basket in baskets:
        for product in basket:
            cooccurrence.setdefault(product, {})
            for other in basket:
                if product != other:
                    cooccurrence[product][other] = cooccurrence[product].get(other, 0) + 1

    customer_recommendations = {}
    for customer_id, group in df.groupby("customer_id"):
        bought = set(group["product_id"])
        scores: dict[str, int] = {}
        for product in bought:
            for other, score in cooccurrence.get(product, {}).items():
                if other not in bought:
                    scores[other] = scores.get(other, 0) + score
        customer_recommendations[customer_id] = top_scores(scores)

    product_recommendations = {product: top_scores(scores) for product, scores in cooccurrence.items()}
    return {
        "customers": customer_recommendations,
        "products": product_recommendations,
    }


def top_scores(scores: dict[str, int]) -> list[dict[str, Any]]:
    return [{"label": label, "score": score} for label, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:5]]


def describe_clusters(clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not clusters:
        return []
    df = pd.DataFrame(clusters)
    descriptions = []
    for cluster, group in df.groupby("cluster"):
        descriptions.append(
            {
                "cluster": int(cluster),
                "customers": int(len(group)),
                "avg_frequency": round(float(group["frequency"].mean()), 2),
                "avg_volume": round(float(group["total_volume"].mean()), 2),
                "avg_distinct_products": round(float(group["distinct_products"].mean()), 2),
                "interpretation": interpret_cluster(group),
            }
        )
    return descriptions


def interpret_cluster(group: pd.DataFrame) -> str:
    avg_volume = group["total_volume"].mean()
    avg_diversity = group["category_diversity"].mean()
    if avg_volume >= group["total_volume"].quantile(0.66) and avg_diversity >= 2:
        return "Clientes de alto valor operativo por volumen y variedad."
    if avg_diversity >= 2:
        return "Clientes diversos, buenos candidatos para venta cruzada."
    return "Clientes de compra puntual o baja diversidad."


def build_insights(df: pd.DataFrame, clusters: list[dict[str, Any]]) -> list[str]:
    top_product = df.groupby("product_id")["quantity"].sum().sort_values(ascending=False).index[0]
    top_category = df.groupby("category")["quantity"].sum().sort_values(ascending=False).index[0]
    peak_day = df.groupby(df["datetime"].dt.strftime("%Y-%m-%d"))["transaction_id"].nunique().sort_values(ascending=False).index[0]
    cluster_count = len(set(item["cluster"] for item in clusters))
    return [
        f"El producto con mayor volumen de unidades es {top_product}.",
        f"La categoria con mayor peso relativo es {top_category}, usando volumen como proxy de importancia.",
        f"El dia pico de compra es {peak_day}, medido por numero de transacciones.",
        f"K-Means separo los clientes en {cluster_count} grupos segun frecuencia, volumen y diversidad.",
        "El recomendador usa co-ocurrencia: productos comprados juntos se proponen como complementarios.",
    ]
