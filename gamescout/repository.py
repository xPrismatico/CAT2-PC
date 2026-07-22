"""Capa de persistencia del proyecto GameScout.

Define ``ProductRepository``, encargado de insertar y consultar productos y
tipos de producto evitando duplicados y manteniendo la relación entre
ambas entidades a través de ``type_id``.
"""

from typing import List, Sequence

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from gamescout.models import Product, ProductType
from gamescout.scraper import ScrapedProduct


class ProductRepository:
    """Repositorio de acceso a datos para productos y tipos de producto.

    Attributes:
        engine: Motor de base de datos usado para abrir sesiones.
    """

    def __init__(self, engine: Engine) -> None:
        """Inicializa el repositorio con un motor de base de datos ya creado.

        Args:
            engine: Instancia de ``Engine`` obtenida vía ``get_engine()``.

        Returns:
            None.
        """
        self.engine = engine

    def get_or_create_type(self, name: str) -> ProductType:
        """Busca un ProductType por nombre, creándolo si no existe.

        Args:
            name: Nombre del tipo de producto a buscar o crear.

        Returns:
            La instancia (existente o recién creada) de ``ProductType``.
        """
        with Session(self.engine) as session:
            statement = select(ProductType).where(ProductType.name == name)
            existing = session.exec(statement).first()
            if existing is not None:
                return existing

            product_type = ProductType(name=name)
            session.add(product_type)
            session.commit()
            session.refresh(product_type)
            return product_type

    def upsert_products(self, scraped_products: Sequence[ScrapedProduct]) -> None:
        """Inserta productos nuevos y omite los que ya existen por product_id.

        Cada producto queda enlazado a su ``ProductType`` correspondiente,
        creando el tipo si aún no existe.

        Args:
            scraped_products: Secuencia de productos crudos extraídos por
                el scraper.

        Returns:
            None.
        """
        with Session(self.engine) as session:
            for item in scraped_products:
                type_statement = select(ProductType).where(ProductType.name == item.type_name)
                product_type = session.exec(type_statement).first()
                if product_type is None:
                    product_type = ProductType(name=item.type_name)
                    session.add(product_type)
                    session.flush()  # asigna product_type.id sin cerrar la transacción

                statement = select(Product).where(Product.product_id == item.product_id)
                existing = session.exec(statement).first()
                if existing is not None:
                    continue

                product = Product(
                    product_id=item.product_id,
                    title=item.title,
                    price_eur=item.price_eur,
                    type_id=product_type.id,
                )
                session.add(product)

            session.commit()

    def get_top_n(self, n: int) -> List[Product]:
        """Obtiene los N productos más caros, con su tipo ya cargado.

        Args:
            n: Cantidad de productos a retornar.

        Returns:
            Lista de los ``n`` productos con mayor ``price_eur``, ordenados
            de mayor a menor precio. El nombre del tipo es accesible vía
            ``product.type.name``.
        """
        with Session(self.engine) as session:
            statement = select(Product).order_by(Product.price_eur.desc()).limit(n)
            products = session.exec(statement).all()
            for product in products:
                _ = product.type.name if product.type else None
            return list(products)

    def get_products_by_type(self, type_name: str) -> List[Product]:
        """Obtiene todos los productos que pertenecen a un tipo dado.

        Args:
            type_name: Nombre del ``ProductType`` a filtrar.

        Returns:
            Lista de productos asociados a ese tipo. Lista vacía si el tipo
            no existe o no tiene productos asociados.
        """
        with Session(self.engine) as session:
            statement = select(ProductType).where(ProductType.name == type_name)
            product_type = session.exec(statement).first()
            if product_type is None:
                return []
            return list(product_type.products)
