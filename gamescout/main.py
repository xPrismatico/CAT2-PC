"""Punto de entrada del pipeline GameScout.

Ejecuta el flujo completo: crea la base de datos si no existe, scrapea el
catálogo, persiste los productos y muestra un pequeño reporte por consola.
Se invoca mediante ``make run``.
"""

import logging

from gamescout.db import create_db_and_tables, get_engine
from gamescout.repository import ProductRepository
from gamescout.scraper import scrape_catalog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run(num_pages: int = 5) -> None:
    """Ejecuta el pipeline completo de GameScout.

    Args:
        num_pages: Cantidad de páginas del catálogo a recorrer.

    Returns:
        None.
    """
    engine = get_engine()
    create_db_and_tables(engine)

    logger.info("Iniciando scraping de %d páginas...", num_pages)
    scraped_products = scrape_catalog(num_pages=num_pages, headless=True)
    logger.info("Se extrajeron %d productos.", len(scraped_products))

    repository = ProductRepository(engine)
    repository.upsert_products(scraped_products)
    logger.info("Productos persistidos en la base de datos.")

    top_products = repository.get_top_n(5)
    logger.info("Top 5 productos más caros:")
    for product in top_products:
        type_name = product.type.name if product.type else "sin tipo"
        logger.info("  - %s (%s): %.2f €", product.title, type_name, product.price_eur)

    if top_products and top_products[0].type is not None:
        sample_type = top_products[0].type.name
        products_of_type = repository.get_products_by_type(sample_type)
        logger.info("Productos de tipo '%s': %d encontrados.", sample_type, len(products_of_type))
        for product in products_of_type[:5]:
            logger.info("  - %s: %.2f €", product.title, product.price_eur)


if __name__ == "__main__":
    run()
