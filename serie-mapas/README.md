# Serie de mapas: accesibilidad educativa en Zumbahua

Esta carpeta contiene la serie cartográfica reproducible y sus piezas gráficas derivadas.

- `serie-mapas-zumbahua-2026.pdf`: documento principal de cinco páginas, calidad de impresión.
- `serie-mapas-zumbahua-2026-web.pdf`: copia optimizada para compartir y descargar.
- `figures/`: páginas individuales en PNG para presentaciones y portafolio.
- `social/`: cuatro tarjetas verticales 1080 × 1350 para redes sociales.
- `data/`: coordenadas educativas reconstruidas y métricas derivadas pequeñas.

## Alcance

Los mapas de tiempo representan accesibilidad **potencial** por la red caminable de OpenStreetMap, con velocidad ajustada por pendiente SRTM. Todavía no son resultados finales de cobertura poblacional: falta incorporar los sectores y la población por edad del Censo 2022, auditar la red y completar la validación de coordenadas.

## Reproducir

```bash
python scripts/build_map_series.py
```

La primera ejecución descarga la geometría de la parroquia, la red caminable, lugares educativos de OpenStreetMap y dos teselas SRTM. Estos archivos se guardan en `data/raw/map_series_cache/` y no se versionan.
