"""Aplicación principal de Streamlit para la visualización del catálogo GameScout.

Lee datos de la base de datos SQLite usando SQLModel, aplica filtros interactivos,
muestra visualizaciones en Plotly e integra cálculos numéricos acelerados con Numba.
"""

import time
from typing import Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlmodel import Session, select

from app.stats import category_stats, price_zscores, price_zscores_pure_python
from gamescout.db import get_engine
from gamescout.models import Product, ProductType


@st.cache_data
def load_data() -> pd.DataFrame:
    """Carga el catálogo desde SQLite combinando Product y ProductType.

    Returns:
        DataFrame con las columnas necesarias para el dashboard.
    """
    engine = get_engine()
    with Session(engine) as session:
        statement = select(Product, ProductType).outerjoin(
            ProductType, Product.type_id == ProductType.id
        )
        results = session.exec(statement).all()

        data = []
        for product, ptype in results:
            data.append(
                {
                    "product_id": product.product_id,
                    "title": product.title,
                    "type_name": ptype.name if ptype else "Sin Categoría",
                    "type_id": product.type_id if product.type_id else 0,
                    "price_eur": float(product.price_eur),
                }
            )

        return pd.DataFrame(data) if data else pd.DataFrame()


def prepare_numba_arrays(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Extrae arreglos NumPy estrictos desde el DataFrame para uso en Numba."""
    prices = df["price_eur"].to_numpy(dtype=np.float64)
    type_ids = df["type_id"].to_numpy(dtype=np.int64)
    return prices, type_ids


# ==========================================
# CONFIGURACIÓN DE PÁGINA Y DATOS
# ==========================================
st.set_page_config(page_title="GameScout Dashboard", page_icon="🎮", layout="wide")

st.title("GameScout Analytics Dashboard")
st.markdown("Explora el catálogo de videojuegos, analiza precios y detecta ofertas.")

df_raw = load_data()

if df_raw.empty:
    st.warning("La base de datos está vacía. Ejecuta el scraper primero (`make run`).")
    st.stop()

# ==========================================
# BARRA LATERAL: FILTROS EN CASCADA
# ==========================================
st.sidebar.header("Filtros")
st.sidebar.markdown("Refina tu búsqueda a continuación:")

# 1. Búsqueda por texto (coincidencia parcial, case-insensitive)
search_text = st.sidebar.text_input("Búsqueda por título:", placeholder="Ej. Zelda, Mario...")

# 2. Multiselect de tipos
all_types = sorted(df_raw["type_name"].unique())
selected_types = st.sidebar.multiselect(
    "Categorías (vacío = todas):", options=all_types, default=[]
)

# 3. Slider de precios (Valores reales de la BD)
min_db_price = float(df_raw["price_eur"].min())
max_db_price = float(df_raw["price_eur"].max())
selected_min, selected_max = st.sidebar.slider(
    "Rango de precio (€):",
    min_value=min_db_price,
    max_value=max_db_price,
    value=(min_db_price, max_db_price),
)

# APLICAR FILTROS EN CASCADA
df_filtered = df_raw.copy()

if search_text:
    df_filtered = df_filtered[df_filtered["title"].str.contains(search_text, case=False, na=False)]
if selected_types:
    df_filtered = df_filtered[df_filtered["type_name"].isin(selected_types)]

df_filtered = df_filtered[
    (df_filtered["price_eur"] >= selected_min) & (df_filtered["price_eur"] <= selected_max)
]

# ==========================================
# MÉTRICAS CLAVE (UX/UI)
# ==========================================
if df_filtered.empty:
    st.info("💡 No hay productos que coincidan con los filtros actuales.")
    st.stop()

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Juegos Encontrados", f"{len(df_filtered)}")
kpi2.metric("Precio Promedio", f"{df_filtered['price_eur'].mean():.2f} €")
kpi3.metric("Precio Máximo", f"{df_filtered['price_eur'].max():.2f} €")

st.divider()

# ==========================================
# SECCIÓN 1: VISUALIZACIONES (PLOTLY)
# ==========================================
st.header("📈 Distribución y Tendencias")

col1, col2 = st.columns(2)

with col1:
    # Top 10 más caros (Visualización mejorada)
    top_10 = df_filtered.nlargest(10, "price_eur").sort_values("price_eur", ascending=True)
    fig_top = px.bar(
        top_10,
        x="price_eur",
        y="title",
        orientation="h",
        title="Top 10 Juegos Más Caros",
        text_auto=".2f",
        labels={"price_eur": "Precio (€)", "title": ""},
        color_discrete_sequence=["#1f77b4"],
    )
    fig_top.update_traces(textposition="outside", hovertemplate="<b>%{y}</b><br>%{x:.2f} €")
    fig_top.update_layout(xaxis_title="", yaxis_title="")
    st.plotly_chart(fig_top, use_container_width=True)

with col2:
    # Histograma (UX mejorada con menos "ruido" visual)
    fig_hist = px.histogram(
        df_filtered,
        x="price_eur",
        nbins=20,
        title="Distribución Frecuencial de Precios",
        labels={"price_eur": "Rango de Precio (€)"},
        color_discrete_sequence=["#2ca02c"],
    )
    fig_hist.update_layout(yaxis_title="Cantidad de Juegos")
    st.plotly_chart(fig_hist, use_container_width=True)

# Precio Promedio por Categoría
avg_price_df = (
    df_filtered.groupby("type_name", as_index=False)["price_eur"]
    .mean()
    .rename(columns={"price_eur": "precio_promedio"})
    .sort_values("precio_promedio", ascending=False)
)
fig_avg = px.bar(
    avg_price_df,
    x="type_name",
    y="precio_promedio",
    title="Precio Promedio de Juegos por Categoría",
    text_auto=".2f",
    labels={"type_name": "", "precio_promedio": "Precio Promedio (€)"},
    color="type_name",
)
fig_avg.update_traces(hovertemplate="%{x}<br>Promedio: %{y:.2f} €")
fig_avg.update_layout(showlegend=False)
st.plotly_chart(fig_avg, use_container_width=True)

# Tabla Interactiva Formateada (Streamlit Nativo, mejor UX)
st.subheader("📋 Catálogo Filtrado")
st.dataframe(
    df_filtered[["product_id", "title", "type_name", "price_eur"]],
    column_config={
        "product_id": st.column_config.NumberColumn("ID", format="%d"),
        "title": "Título del Videojuego",
        "type_name": "Categoría",
        "price_eur": st.column_config.NumberColumn("Precio", format="%.2f €"),
    },
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ==========================================
# SECCIÓN 2: CÁLCULOS ACELERADOS CON NUMBA
# ==========================================
st.header("⚡ Análisis Estadístico Avanzado (Numba)")

prices_arr, type_ids_arr = prepare_numba_arrays(df_filtered)

# 1. Tabla resumen por categoría
unique_types, stats_matrix = category_stats(prices_arr, type_ids_arr)
id_to_name = dict(zip(df_filtered["type_id"], df_filtered["type_name"]))

stats_data = [
    {
        "cat_name": id_to_name.get(unique_types[i], str(unique_types[i])),
        "count": int(stats_matrix[i, 0]),
        "min": stats_matrix[i, 1],
        "max": stats_matrix[i, 2],
        "mean": stats_matrix[i, 3],
        "std": stats_matrix[i, 4],
    }
    for i in range(len(unique_types))
]

st.subheader("Resumen Poblacional por Categoría")
st.dataframe(
    pd.DataFrame(stats_data),
    column_config={
        "cat_name": "Categoría",
        "count": st.column_config.NumberColumn("Total Juegos", format="%d"),
        "min": st.column_config.NumberColumn("Mínimo", format="%.2f €"),
        "max": st.column_config.NumberColumn("Máximo", format="%.2f €"),
        "mean": st.column_config.NumberColumn("Promedio", format="%.2f €"),
        "std": st.column_config.NumberColumn("Desv. Estándar", format="%.4f"),
    },
    use_container_width=True,
    hide_index=True,
)

# 2. Outliers / Ofertas (z-scores)
st.subheader("🚨 Detección de Outliers y Ofertas")
st.markdown("Encuentra juegos con precios anormalmente altos o bajos para su categoría.")

z_threshold = st.slider(
    "Umbral de Z-Score (Desviaciones):", min_value=0.0, max_value=5.0, value=2.0, step=0.1
)

z_scores = price_zscores(prices_arr, type_ids_arr)
df_filtered = df_filtered.assign(z_score=z_scores)
outliers = df_filtered[df_filtered["z_score"].abs() > z_threshold]

if outliers.empty:
    st.success(f"No se detectaron outliers fuera del umbral de Z-Score > {z_threshold}.")
else:
    st.dataframe(
        outliers[["title", "type_name", "price_eur", "z_score"]],
        column_config={
            "title": "Título",
            "type_name": "Categoría",
            "price_eur": st.column_config.NumberColumn("Precio", format="%.2f €"),
            "z_score": st.column_config.NumberColumn("Z-Score", format="%.2f"),
        },
        use_container_width=True,
        hide_index=True,
    )

# 3. Benchmark de Rendimiento
st.subheader("⏱️ Benchmark de Aceleración: Python vs Numba")

with st.spinner("Calculando Z-Scores en ambos motores..."):
    # Descartar warm-up (Compilación JIT)
    _ = price_zscores(prices_arr, type_ids_arr)

    # Numba
    t0_numba = time.perf_counter()
    _ = price_zscores(prices_arr, type_ids_arr)
    t_numba = time.perf_counter() - t0_numba

    # Python Puro
    t0_python = time.perf_counter()
    _ = price_zscores_pure_python(prices_arr, type_ids_arr)
    t_python = time.perf_counter() - t0_python

col_b1, col_b2, col_b3 = st.columns(3)
col_b1.metric("Tiempo Python Puro", f"{t_python:.6f} s")
col_b2.metric("Tiempo Numba (@njit)", f"{t_numba:.6f} s")

speedup = t_python / t_numba if t_numba > 0 else 1.0
col_b3.metric("Aceleración Lograda", f"{speedup:.2f}x", delta="JIT Compilation")
