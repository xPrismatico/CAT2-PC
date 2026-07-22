# GameScout

Pipeline de datos que extrae el catálogo de videojuegos publicado en
[Oxylabs Scraping Sandbox](https://sandbox.oxylabs.io/products), lo
almacena en una base de datos SQLite local y deja todo listo para
análisis posterior.
## Requisitos

- Conda
- Google Chrome / Chromium instalado (para Selenium)

## Uso

```bash
make install   # Crea el entorno conda "gamescout" desde environment.yml
conda activate gamescout
make lint      # flake8
make format    # black
make run       # Ejecuta el pipeline completo (scrape + persist + reporte)
make test      # pytest
```
