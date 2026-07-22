"""Scraper de videojuegos para Oxylabs Scraping Sandbox.

Recorre el catálogo paginado de https://sandbox.oxylabs.io/products usando
Selenium en modo headless, extrayendo de cada tarjeta el identificador del
producto, título, tipo/categoría y precio.
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

BASE_URL = "https://sandbox.oxylabs.io/products"
CARD_SELECTOR = "div.product-card"
TITLE_SELECTOR = "h4.title"
TYPE_SELECTOR = "p.category span"
PRICE_SELECTOR = "div.price-wrapper"
DEFAULT_TIMEOUT = 10


@dataclass
class ScrapedProduct:
    """Representa un producto crudo extraído de una tarjeta del catálogo.

    Attributes:
        product_id: Identificador numérico del producto extraído de la URL.
        title: Título del producto.
        type_name: Nombre del tipo/categoría, tal como aparece en la tarjeta.
        price_eur: Precio del producto ya limpio y convertido a float.
    """

    product_id: int
    title: str
    type_name: str
    price_eur: float


def _build_driver(headless: bool = True) -> webdriver.Chrome:
    """Construye una instancia de Chrome WebDriver.

    Args:
        headless: Si es True, el navegador se ejecuta sin interfaz gráfica.

    Returns:
        Instancia configurada de ``webdriver.Chrome``.
    """
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def _extract_product_id(card: WebElement) -> Optional[int]:
    """Extrae el product_id numérico desde el enlace de una tarjeta.

    Args:
        card: Elemento WebElement correspondiente a la tarjeta de producto.

    Returns:
        El identificador numérico del producto, o None si no se pudo extraer.
    """
    link = card.find_element(By.CSS_SELECTOR, "a[href*='/products/']")
    href = link.get_attribute("href") or ""
    match = re.search(r"/products/(\d+)", href)
    return int(match.group(1)) if match else None


def _clean_price(raw_price: str) -> float:
    """Limpia un precio en formato "12,34 €" y lo convierte a float.

    Args:
        raw_price: Texto crudo del precio tal como aparece en la tarjeta.

    Returns:
        El precio convertido a float, usando punto como separador decimal.
    """
    cleaned = raw_price.replace("€", "").strip()
    cleaned = cleaned.replace(",", ".")
    cleaned = re.sub(r"[^0-9.]", "", cleaned)
    return float(cleaned)


def _parse_card(card: WebElement) -> ScrapedProduct:
    """Extrae los datos de una única tarjeta de producto.

    Args:
        card: Elemento WebElement correspondiente a la tarjeta de producto.

    Returns:
        Instancia de ``ScrapedProduct`` con los datos ya limpios.

    Raises:
        ValueError: Si no fue posible extraer el product_id de la tarjeta.
    """
    product_id = _extract_product_id(card)
    if product_id is None:
        raise ValueError("No se pudo extraer product_id de la tarjeta.")

    title = card.find_element(By.CSS_SELECTOR, TITLE_SELECTOR).text.strip()
    type_name = card.find_element(By.CSS_SELECTOR, TYPE_SELECTOR).text.strip()
    raw_price = card.find_element(By.CSS_SELECTOR, PRICE_SELECTOR).text
    price_eur = _clean_price(raw_price)

    return ScrapedProduct(
        product_id=product_id,
        title=title,
        type_name=type_name,
        price_eur=price_eur,
    )


def scrape_page(driver: webdriver.Chrome) -> List[ScrapedProduct]:
    """Extrae todos los productos de la página actualmente cargada.

    Espera explícitamente a que la grilla de productos esté presente antes
    de leerla, y omite (con advertencia) cualquier tarjeta que falle al
    ser procesada, sin detener el resto del scraping.

    Args:
        driver: Instancia activa de Selenium WebDriver.

    Returns:
        Lista de productos extraídos correctamente en la página actual.
    """
    wait = WebDriverWait(driver, DEFAULT_TIMEOUT)
    wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, CARD_SELECTOR)))

    cards = driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)
    products: List[ScrapedProduct] = []

    for index, card in enumerate(cards):
        try:
            products.append(_parse_card(card))
        except (NoSuchElementException, ValueError) as exc:
            logger.warning("No se pudo procesar la tarjeta #%d: %s", index, exc)
            continue

    return products


def scrape_catalog(num_pages: int = 5, headless: bool = True) -> List[ScrapedProduct]:
    """Recorre varias páginas del catálogo y devuelve todos los productos.

    Args:
        num_pages: Cantidad de páginas a recorrer, comenzando desde la 1.
        headless: Si es True, ejecuta el navegador en modo headless.

    Returns:
        Lista consolidada de productos extraídos de todas las páginas.
    """
    driver = _build_driver(headless=headless)
    all_products: List[ScrapedProduct] = []

    try:
        for page in range(1, num_pages + 1):
            url = BASE_URL if page == 1 else f"{BASE_URL}?page={page}"
            logger.info("Scrapeando página %d: %s", page, url)
            driver.get(url)
            try:
                page_products = scrape_page(driver)
            except TimeoutException:
                logger.warning("Timeout esperando la grilla en la página %d.", page)
                continue
            all_products.extend(page_products)
    finally:
        driver.quit()

    return all_products
