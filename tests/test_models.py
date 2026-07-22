"""Tests unitarios para los modelos ProductType y Product."""

import pytest

from gamescout.models import Product, ProductType


def test_product_type_name_no_vacio() -> None:
    """ProductType.name no debe aceptar strings vacíos."""
    with pytest.raises(ValueError):
        ProductType(name="   ")


def test_product_type_valido() -> None:
    """ProductType se crea correctamente con un nombre válido."""
    product_type = ProductType(name="RPG")
    assert product_type.name == "RPG"


def test_product_id_invalido() -> None:
    """Product.product_id debe ser mayor o igual a 1."""
    with pytest.raises(ValueError):
        Product(product_id=0, title="Juego", price_eur=10.0)


def test_product_price_negativo_invalido() -> None:
    """Product.price_eur no puede ser negativo."""
    with pytest.raises(ValueError):
        Product(product_id=1, title="Juego", price_eur=-5.0)


def test_product_title_vacio_invalido() -> None:
    """Product.title no puede estar vacío."""
    with pytest.raises(ValueError):
        Product(product_id=1, title="   ", price_eur=10.0)


def test_product_valido() -> None:
    """Product se crea correctamente con datos válidos."""
    product = Product(product_id=1, title="Zelda", price_eur=59.99)
    assert product.product_id == 1
    assert product.title == "Zelda"
    assert product.price_eur == 59.99
