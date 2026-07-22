"""Tests unitarios para ProductRepository sobre una base de datos temporal."""

from pathlib import Path
from typing import Iterator

import pytest
from sqlalchemy.engine import Engine

from gamescout.db import create_db_and_tables, get_engine
from gamescout.repository import ProductRepository
from gamescout.scraper import ScrapedProduct


@pytest.fixture()
def engine(tmp_path: Path) -> Iterator[Engine]:
    """Crea un motor SQLite temporal con las tablas ya creadas.

    Args:
        tmp_path: Directorio temporal provisto por pytest.

    Yields:
        Motor de base de datos listo para usarse en los tests.
    """
    db_path = tmp_path / "test_gamescout.db"
    test_engine = get_engine(db_path)
    create_db_and_tables(test_engine)
    yield test_engine


def test_get_or_create_type_no_duplica(engine: Engine) -> None:
    """Llamar dos veces con el mismo nombre no debe duplicar el tipo."""
    repository = ProductRepository(engine)
    first = repository.get_or_create_type("Action")
    second = repository.get_or_create_type("Action")
    assert first.id == second.id


def test_upsert_products_no_duplica(engine: Engine) -> None:
    """upsert_products no debe insertar dos veces el mismo product_id."""
    repository = ProductRepository(engine)
    items = [ScrapedProduct(product_id=1, title="Juego A", type_name="RPG", price_eur=20.0)]

    repository.upsert_products(items)
    repository.upsert_products(items)

    products = repository.get_products_by_type("RPG")
    assert len(products) == 1


def test_get_top_n(engine: Engine) -> None:
    """get_top_n retorna los productos más caros ordenados descendentemente."""
    repository = ProductRepository(engine)
    items = [
        ScrapedProduct(product_id=1, title="Barato", type_name="Action", price_eur=10.0),
        ScrapedProduct(product_id=2, title="Caro", type_name="Action", price_eur=50.0),
        ScrapedProduct(product_id=3, title="Medio", type_name="RPG", price_eur=30.0),
    ]
    repository.upsert_products(items)

    top_2 = repository.get_top_n(2)
    assert [p.title for p in top_2] == ["Caro", "Medio"]
    assert top_2[0].type.name == "Action"


def test_get_products_by_type_inexistente(engine: Engine) -> None:
    """get_products_by_type retorna lista vacía si el tipo no existe."""
    repository = ProductRepository(engine)
    assert repository.get_products_by_type("Inexistente") == []
