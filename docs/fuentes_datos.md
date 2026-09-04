# Fuentes de datos

| Componente | Fuente prioritaria | Resolución o periodo | Estado | Limitación principal |
|---|---|---|---|---|
| Matrícula y docentes | Ministerio de Educación, registro histórico | 2009-2010 a 2024-2025 Inicio | Verificada | Revisar cambios metodológicos, especialmente 2022-2023 |
| Oferta por nivel | Ministerio de Educación, tipologías | 2024-2025, corte febrero 2025 | Verificada | No contiene coordenadas en la descarga revisada |
| Educación intercultural bilingüe | SEIBE | Diciembre 2022 | Complementaria | Menor actualidad |
| Población escolar | INEC, Censo 2022 | Sector y manzana/localidad | Pendiente de descarga | Reglas de anonimización y agregación |
| Límites | INEC / IGM | Censo 2022 / WFS | Pendiente | Comprobar compatibilidad de códigos y fechas |
| Caminos y senderos | OpenStreetMap | Instantánea fechada | Pendiente | Cobertura rural desigual; requiere auditoría |
| Cartografía oficial | IGM | 1:25.000 y otras escalas | Pendiente | Seleccionar capas y licencias aplicables |
| Elevación | Copernicus DEM GLO-30 | 30 m | Opcional | Modelo de superficie; requiere registro |

## Enlaces

- MINEDUC, datos abiertos: https://educacion.gob.ec/datos-abiertos-minedec/
- MINEDUC, base de datos: https://educacion.gob.ec/base-de-datos/
- Registro histórico: https://www.datosabiertos.gob.ec/dataset/registro-de-matricula-mineduc
- SEIBE: https://www.datosabiertos.gob.ec/dataset/instituciones-educativas-del-sistema-de-educacion-intercultural-bilingue
- Censo 2022, resultados: https://www.censoecuador.gob.ec/resultados-censo/
- Censo 2022, datos: https://www.censoecuador.gob.ec/data-censo-ecuador/
- Guía de la base Censo 2022: https://www.censoecuador.gob.ec/wp-content/uploads/2024/12/GUIA_BASE_CPV_2022.pdf
- Geoportal IGM: https://www.geoportaligm.gob.ec/geoportal-igm/
- OpenStreetMap: https://www.openstreetmap.org/
- Extracto Ecuador de Geofabrik: https://download.geofabrik.de/south-america/ecuador.html
- OSMnx: https://osmnx.readthedocs.io/en/stable/
- Copernicus DEM: https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM

## Reconstrucción de coordenadas escolares

La base 2024-2025 revisada contiene 19 instituciones de Zumbahua, pero no coordenadas. Se seguirá este orden:

1. Coincidencia por código AMIE en un geoportal oficial, si está disponible.
2. Coincidencia por nombre y dirección en OpenStreetMap.
3. Geocodificación de dirección pública con Nominatim, respetando su política de uso.
4. Revisión visual contra ortofoto o imagen permitida; no se redistribuirán imágenes con licencia restrictiva.
5. Registro de fuente, fecha, evidencia y confianza alta, media o baja.

Ninguna coordenada se considerará validada solo por similitud de nombre.

