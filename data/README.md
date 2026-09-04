# Datos

## Reglas

- `raw/`: descargas originales inmutables; no se versionan.
- `interim/`: datos limpiados o cruzados; no se versionan.
- `processed/`: insumos analíticos finales; se publican solo si su licencia y tamaño lo permiten.
- `manual/`: tablas pequeñas revisadas manualmente, con fuente y nivel de confianza.

Cada archivo generado debe tener un registro con fuente, fecha de descarga, licencia, hash SHA-256, sistema de coordenadas y transformaciones aplicadas.

No se publicarán coordenadas de hogares, información personal ni microdatos que permitan reidentificación. La demanda se agregará a sectores censales o a una cuadrícula compatible con las reglas del INEC.

