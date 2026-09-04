# Atlas preliminar de accesibilidad educativa en Zumbahua

Esta carpeta contiene el atlas reproducible y las piezas gráficas derivadas.

- `atlas-zumbahua-2026.pdf`: documento principal de ocho páginas, calidad de impresión.
- `atlas-zumbahua-2026-web.pdf`: copia optimizada para compartir y descargar.
- `figures/`: páginas individuales en PNG para presentaciones y portafolio.
- `social/`: tarjetas verticales 1080 × 1350 para redes sociales.
- `data/`: coordenadas educativas reconstruidas y métricas derivadas pequeñas.

## Alcance

Los mapas de tiempo representan accesibilidad **potencial** por la red caminable de OpenStreetMap, con velocidad ajustada por pendiente SRTM. Todavía no son resultados finales de cobertura poblacional: falta incorporar los sectores y la población por edad del Censo 2022, auditar la red y completar la validación de coordenadas.

## Reproducir

```bash
python scripts/build_atlas.py
```

La primera ejecución descarga la geometría de la parroquia, la red caminable, lugares educativos de OpenStreetMap y dos teselas SRTM. Estos archivos se guardan en `data/raw/atlas_cache/` y no se versionan.
