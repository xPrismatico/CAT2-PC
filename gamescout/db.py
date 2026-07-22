"""Utilidades de conexión y creación del esquema de base de datos.

Centraliza la creación del motor de SQLAlchemy/SQLModel usado por el resto
del proyecto (scraper, repositorio, tests) para evitar conexiones sueltas
definidas de forma dispersa.
"""

from pathlib import Path

from sqlmodel import SQLModel, create_engine
from sqlalchemy.engine import Engine

# Importar los modelos aquí asegura que sus tablas queden registradas en
# SQLModel.metadata antes de llamar a create_db_and_tables().
from gamescout.models import Product, ProductType  # noqa: F401

DEFAULT_DB_PATH = Path("data/processed/gamescout.db")


def get_engine(db_path: Path = DEFAULT_DB_PATH) -> Engine:
    """Crea (o reutiliza la configuración de) el motor de base de datos SQLite.

    Args:
        db_path: Ruta al archivo SQLite que se usará como base de datos.
            Por defecto apunta a ``data/processed/gamescout.db``.

    Returns:
        Instancia de ``Engine`` de SQLAlchemy configurada para SQLite.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_url = f"sqlite:///{db_path}"
    return create_engine(sqlite_url, echo=False)


def create_db_and_tables(engine: Engine) -> None:
    """Crea todas las tablas definidas en SQLModel.metadata (y sus relaciones).

    Args:
        engine: Motor de base de datos sobre el que se crearán las tablas.

    Returns:
        None.
    """
    SQLModel.metadata.create_all(engine)
