"""Módulo de funciones numéricas aceleradas mediante Numba para GameScout.

Proporciona cálculos estadísticos descriptivos por categoría y z-scores
utilizando compilación JIT con Numba y bucles explícitos sobre arreglos de NumPy.
"""

import time
from typing import Dict, Tuple

import numba
import numpy as np


@numba.njit
def category_stats(prices: np.ndarray, type_ids: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Calcula estadísticas descriptivas por categoría recorriendo arreglos a mano.

    No utiliza pandas.groupby ni vectorización de alto nivel, permitiendo la
    óptima aceleración mediante Numba @njit.

    Args:
        prices: Arreglo 1D de NumPy de tipo float64 con los precios.
        type_ids: Arreglo 1D de NumPy de tipo int64 con los IDs de categoría.

    Returns:
        Una tupla compuesta por:
        - unique_types: Arreglo 1D (int64) con los IDs de categorías presentes.
        - stats_matrix: Arreglo 2D (float64) de forma (N, 5), donde las columnas
          representan: [count, min_price, max_price, mean_price, std_price].
    """
    unique_types = np.unique(type_ids)
    num_categories = len(unique_types)
    stats_matrix = np.zeros((num_categories, 5), dtype=np.float64)

    for i in range(num_categories):
        cat_id = unique_types[i]

        # Primer pase: acumulación de datos básicos
        count = 0
        min_val = 1e18
        max_val = -1e18
        sum_val = 0.0

        for j in range(len(prices)):
            if type_ids[j] == cat_id:
                val = prices[j]
                count += 1
                sum_val += val
                if val < min_val:
                    min_val = val
                if val > max_val:
                    max_val = val

        if count > 0:
            mean_val = sum_val / count

            # Segundo pase: cálculo de desviación estándar (poblacional, ddof=0)
            sum_sq_diff = 0.0
            for j in range(len(prices)):
                if type_ids[j] == cat_id:
                    diff = prices[j] - mean_val
                    sum_sq_diff += diff * diff

            std_val = np.sqrt(sum_sq_diff / count)

            stats_matrix[i, 0] = float(count)
            stats_matrix[i, 1] = min_val
            stats_matrix[i, 2] = max_val
            stats_matrix[i, 3] = mean_val
            stats_matrix[i, 4] = std_val

    return unique_types, stats_matrix


@numba.njit
def price_zscores(prices: np.ndarray, type_ids: np.ndarray) -> np.ndarray:
    """Calcula el z-score de cada producto respecto a su propia categoría.

    Args:
        prices: Arreglo 1D (float64) con los precios de cada producto.
        type_ids: Arreglo 1D (int64) con la categoría correspondiente.

    Returns:
        Arreglo 1D (float64) con los z-scores calculados por categoría.
    """
    n = len(prices)
    zscores = np.zeros(n, dtype=np.float64)
    unique_types, stats = category_stats(prices, type_ids)

    for j in range(n):
        cat_id = type_ids[j]
        cat_idx = -1

        for i in range(len(unique_types)):
            if unique_types[i] == cat_id:
                cat_idx = i
                break

        if cat_idx != -1:
            mean_val = stats[cat_idx, 3]
            std_val = stats[cat_idx, 4]

            if std_val > 1e-12:
                zscores[j] = (prices[j] - mean_val) / std_val
            else:
                zscores[j] = 0.0

    return zscores


def price_zscores_pure_python(prices: np.ndarray, type_ids: np.ndarray) -> np.ndarray:
    """Versión en Python puro (sin @njit) para cálculo de z-scores por categoría.

    Esta función sirve exclusivamente como referencia de comparación para
    medir la aceleración de Numba en el benchmark.

    Args:
        prices: Arreglo 1D (float64) con los precios de cada producto.
        type_ids: Arreglo 1D (int64) con la categoría correspondiente.

    Returns:
        Arreglo 1D (float64) con los z-scores calculados por categoría.
    """
    n = len(prices)
    zscores = np.zeros(n, dtype=np.float64)

    # Identificar categorías únicas en Python puro
    unique_types_list = []
    for tid in type_ids:
        if tid not in unique_types_list:
            unique_types_list.append(tid)

    # Calcular estadísticas por categoría
    stats_map = {}
    for cat_id in unique_types_list:
        cat_prices = [prices[k] for k in range(n) if type_ids[k] == cat_id]
        if cat_prices:
            count = len(cat_prices)
            mean_val = sum(cat_prices) / count
            var_val = sum((x - mean_val) ** 2 for x in cat_prices) / count
            std_val = var_val**0.5
            stats_map[cat_id] = (mean_val, std_val)

    # Asignar z-scores
    for j in range(n):
        cat_id = type_ids[j]
        if cat_id in stats_map:
            mean_val, std_val = stats_map[cat_id]
            if std_val > 1e-12:
                zscores[j] = (prices[j] - mean_val) / std_val
            else:
                zscores[j] = 0.0

    return zscores


def run_benchmark(prices: np.ndarray, type_ids: np.ndarray) -> Dict[str, float]:
    """Ejecuta una comparación de tiempo entre Python puro y Numba.

    Descarta la primera llamada (warm-up) de Numba para ignorar el tiempo de
    compilación JIT y medir únicamente el tiempo de ejecución.

    Args:
        prices: Arreglo 1D de precios.
        type_ids: Arreglo 1D de tipos/categorías.

    Returns:
        Diccionario con las mediciones en segundos y el factor de aceleración.
    """
    # 1. Warm-up (compilación JIT)
    _ = price_zscores(prices, type_ids)

    # 2. Medición Numba (ya compilado)
    t0_numba = time.perf_counter()
    _ = price_zscores(prices, type_ids)
    t_numba = time.perf_counter() - t0_numba

    # 3. Medición Python puro
    t0_python = time.perf_counter()
    _ = price_zscores_pure_python(prices, type_ids)
    t_python = time.perf_counter() - t0_python

    speedup = t_python / t_numba if t_numba > 0 else 1.0

    return {
        "time_numba_sec": t_numba,
        "time_python_sec": t_python,
        "speedup": speedup,
    }
