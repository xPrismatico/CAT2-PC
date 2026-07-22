# GameScout

**Evaluaciones Aplicadas 2.1 y 2.2 - Programación Científica (2026)**  
**Universidad Católica del Norte, Antofagasta, Chile**  
**Autor:** Samuel Fuentes

Pipeline de datos que extrae el catálogo de videojuegos publicado en
[Oxylabs Scraping Sandbox](https://sandbox.oxylabs.io/products), lo
almacena en una base de datos SQLite local y deja todo listo para
análisis posterior.

## Requisitos

- Conda (Recomiendo Miniconda)
- Google Chrome / Chromium instalado (para Selenium)


## 🚀 Características Principales

* **Scraping Automatizado:** Extracción de datos paginados utilizando **Selenium WebDriver** en modo *headless*, manejando cargas dinámicas y esperas explícitas.
* **Persistencia Relacional:** Modelado de datos robusto con **SQLModel** (Pydantic + SQLAlchemy) garantizando integridad transaccional y validación de tipos.
* **Dashboard Interactivo:** Interfaz web construida con **Streamlit**, implementando filtros en cascada y visualizaciones analíticas de alto nivel con **Plotly**.
* **Aceleración Numérica:** Cálculos estadísticos poblacionales y detección de *outliers* (z-scores) acelerados mediante compilación JIT con **Numba**, incluyendo benchmarks de rendimiento frente a Python puro.



## Uso

```bash
make install   # Crea el entorno conda "gamescout" desde environment.yml
conda activate gamescout
make lint      # flake8
make format    # black
make run       # Ejecuta el pipeline completo (scrape + persist + reporte)
make test      # pytest
```


## Instalación y Ejecución

El proyecto incluye un `Makefile` para facilitar la configuración, ejecución y evaluación. Para revisar la entrega, por favor ejecute los siguientes comandos en orden:

### 1. Preparar el entorno virtual
Crea el entorno con todas las dependencias exactas (`streamlit`, `plotly`, `numba`, `sqlmodel`, etc.) y actívelo:
```bash
make install
conda activate gamescout
```

### 2. Poblar base de datos

Paso obligatorio en la primera ejecución para scrapear el sitio web, construir la base de datos data/processed/gamescout.db y evitar errores de tablas inexistentes:

make run


### 3. Levantar el Dashboard Interactivo
Inicia la interfaz gráfica de Streamlit de forma segura reconociendo el módulo principal:


make dashboard

## Pruebas y Calidad de Código
El código fuente respeta rigurosamente el estándar PEP 8, incluyendo type hints (PEP 484) y docstrings (formato Google) en el 100% de las funciones públicas.

Para validar los estándares de calidad, ejecute:


# Verificación estricta de estilo (0 errores garantizados)
make lint

# Formateo automático de código
make format

# Ejecución de la batería de pruebas unitarias (Modelos, Repositorio y Motor Numba)
make test

---

## 📂 Estructura del Proyecto

El proyecto sigue estándares de estructuración modular para ciencia de datos:

```text
Base_Prueba_1/
├── app/                    # Aplicación de visualización web (Aplicada 2)
│   ├── __init__.py
│   ├── dashboard.py        # UI interactiva en Streamlit
│   └── stats.py            # Motor matemático acelerado con Numba
├── data/
│   └── processed/          # Base de datos SQLite generada (gamescout.db)
├── gamescout/              # Paquete principal del pipeline ETL (Aplicada 1)
│   ├── __init__.py
│   ├── db.py               # Configuración del motor SQLModel
│   ├── main.py             # Punto de entrada del scraper
│   ├── models.py           # Modelos de datos (Product, ProductType)
│   ├── repository.py       # Capa de persistencia (Upserts y Consultas)
│   └── scraper.py          # Lógica de extracción con Selenium
├── tests/                  # Pruebas unitarias automatizadas
│   ├── test_models.py
│   ├── test_repository.py
│   └── test_stats.py
├── environment.yml         # Dependencias y entorno Conda
├── Makefile                # Automatización de comandos principales
└── pyproject.toml / setup.cfg # Configuración de herramientas (Black, Flake8, Pytest)
```