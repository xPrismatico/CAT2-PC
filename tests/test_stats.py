"""Tests unitarios para las funciones numéricas de app/stats.py."""

import numpy as np

from app.stats import (
    category_stats,
    price_zscores,
    price_zscores_pure_python,
    run_benchmark,
)


def test_category_stats_correctness() -> None:
    """Verifica que category_stats calcule correctamente la media, min, max y std."""
    prices = np.array([10.0, 20.0, 30.0, 100.0, 200.0], dtype=np.float64)
    type_ids = np.array([1, 1, 1, 2, 2], dtype=np.int64)

    unique_types, stats = category_stats(prices, type_ids)

    assert len(unique_types) == 2
    assert list(unique_types) == [1, 2]

    # Categoría 1: [10, 20, 30]
    # -> count=3, min=10, max=30, mean=20, std=sqrt(((100+0+100)/3))=8.1649...
    assert stats[0, 0] == 3.0
    assert stats[0, 1] == 10.0
    assert stats[0, 2] == 30.0
    assert stats[0, 3] == 20.0
    assert np.isclose(stats[0, 4], np.std([10.0, 20.0, 30.0]))

    # Categoría 2: [100, 200]
    # -> count=2, min=100, max=200, mean=150, std=50
    assert stats[1, 0] == 2.0
    assert stats[1, 1] == 100.0
    assert stats[1, 2] == 200.0
    assert stats[1, 3] == 150.0
    assert np.isclose(stats[1, 4], 50.0)


def test_price_zscores_numba_vs_python_puro() -> None:
    """Verifica que los z-scores de Numba coincidan con los de Python puro."""
    np.random.seed(42)
    prices = np.random.uniform(10.0, 100.0, size=50)
    type_ids = np.random.choice([10, 20, 30], size=50)

    z_numba = price_zscores(prices, type_ids)
    z_python = price_zscores_pure_python(prices, type_ids)

    assert np.allclose(z_numba, z_python, atol=1e-8)


def test_price_zscores_single_item_zero_std() -> None:
    """Verifica que si la desviación estándar es 0, el z-score retorne 0 en vez de NaN."""
    prices = np.array([50.0], dtype=np.float64)
    type_ids = np.array([1], dtype=np.int64)

    zscores = price_zscores(prices, type_ids)
    assert zscores[0] == 0.0


def test_run_benchmark_metrics() -> None:
    """Verifica la ejecución del benchmark y la presencia de métricas clave."""
    prices = np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float64)
    type_ids = np.array([1, 1, 2, 2], dtype=np.int64)

    metrics = run_benchmark(prices, type_ids)

    assert "time_numba_sec" in metrics
    assert "time_python_sec" in metrics
    assert "speedup" in metrics
    assert metrics["time_numba_sec"] >= 0
    assert metrics["time_python_sec"] >= 0
