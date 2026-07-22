"""Modelos de datos del proyecto GameScout.

Define las entidades persistentes ``ProductType`` y ``Product`` usando
SQLModel. Ambas tablas están relacionadas mediante una llave foránea
(``Product.type_id`` -> ``ProductType.id``) y la relación es navegable en
ambos sentidos gracias a ``Relationship(back_populates=...)``.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import validates
from sqlmodel import Field, Relationship, SQLModel


class ProductType(SQLModel, table=True):
    """Categoría o tipo de producto (ej. "Action", "RPG", "Nintendo Switch").

    Attributes:
        id: Identificador interno autogenerado por la base de datos.
        name: Nombre único del tipo de producto, tal como aparece en la
            tarjeta del catálogo.
        products: Lista de productos asociados a este tipo. Se completa
            automáticamente a través de la relación con ``Product``.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, nullable=False)

    products: List["Product"] = Relationship(back_populates="type")

    @validates("name")
    def name_no_vacio(self, key: str, value: str) -> str:
        """Valida que el nombre del tipo de producto no esté vacío.

        Args:
            key: Nombre del atributo que está siendo validado ("name").
            value: Valor propuesto para el campo ``name``.

        Returns:
            El valor validado, sin espacios sobrantes en los extremos.

        Raises:
            ValueError: Si el valor está vacío o compuesto solo de espacios.
        """
        if not value or not value.strip():
            raise ValueError("El nombre del ProductType no puede estar vacío.")
        return value.strip()


class Product(SQLModel, table=True):
    """Producto individual extraído del catálogo de videojuegos.

    Attributes:
        id: Identificador interno autogenerado por la base de datos.
        product_id: Identificador del producto tal como aparece en la URL
            del sitio de origen (ej. ``/products/1`` -> ``1``).
        title: Título del producto.
        price_eur: Precio del producto en euros, almacenado como número
            (float), nunca como string con el símbolo "€".
        scraped_at: Marca de tiempo en la que el producto fue extraído.
        type_id: Llave foránea hacia ``ProductType.id``.
        type: Instancia de ``ProductType`` asociada a este producto,
            accesible de forma navegable gracias a la relación.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(index=True, unique=True, nullable=False)
    title: str = Field(nullable=False)
    price_eur: float = Field(nullable=False)
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    type_id: Optional[int] = Field(default=None, foreign_key="producttype.id")

    type: Optional[ProductType] = Relationship(back_populates="products")

    @validates("product_id")
    def product_id_valido(self, key: str, value: int) -> int:
        """Valida que ``product_id`` sea mayor o igual a 1.

        Args:
            key: Nombre del atributo que está siendo validado ("product_id").
            value: Valor propuesto para el campo ``product_id``.

        Returns:
            El valor validado.

        Raises:
            ValueError: Si el valor es menor a 1.
        """
        if value < 1:
            raise ValueError("product_id debe ser mayor o igual a 1.")
        return value

    @validates("price_eur")
    def price_eur_valido(self, key: str, value: float) -> float:
        """Valida que ``price_eur`` sea mayor o igual a 0.

        Args:
            key: Nombre del atributo que está siendo validado ("price_eur").
            value: Valor propuesto para el campo ``price_eur``.

        Returns:
            El valor validado.

        Raises:
            ValueError: Si el valor es negativo.
        """
        if value < 0:
            raise ValueError("price_eur debe ser mayor o igual a 0.")
        return value

    @validates("title")
    def title_no_vacio(self, key: str, value: str) -> str:
        """Valida que el título del producto no esté vacío.

        Args:
            key: Nombre del atributo que está siendo validado ("title").
            value: Valor propuesto para el campo ``title``.

        Returns:
            El valor validado, sin espacios sobrantes en los extremos.

        Raises:
            ValueError: Si el valor está vacío o compuesto solo de espacios.
        """
        if not value or not value.strip():
            raise ValueError("El título del producto no puede estar vacío.")
        return value.strip()
