# Protocolo de investigación

## Alcance

Estudio ecológico, transversal y reproducible de accesibilidad potencial. Compara la red educativa de 2017-2018 con la información disponible más reciente y estima condiciones espaciales actuales desde gabinete.

No busca sustituir una encuesta de movilidad ni afirmar tiempos reales de viaje. Los escenarios motorizados se presentarán como simulaciones cuando no existan rutas, horarios y frecuencias verificables.

## Preguntas

1. ¿Cómo cambió la oferta, matrícula y dotación docente desde 2017-2018?
2. ¿Qué proporción de la población en edad escolar puede alcanzar una institución de su nivel dentro de cada umbral de tiempo?
3. ¿Qué sectores presentan simultáneamente baja accesibilidad, alta población objetivo y alta vulnerabilidad?
4. ¿Cómo cambia el resultado al incorporar capacidad institucional, pendiente y velocidades alternativas?
5. ¿Qué escenarios de localización o transporte reducen más la población desatendida?

## Unidades de análisis

- Origen: sector censal, manzana/localidad o centroide poblacional ponderado.
- Destino: institución educativa activa, desagregada por nivel ofertado.
- Red: caminos transitables a pie; escenario vial motorizado separado.
- Población: residentes en edades compatibles con cada nivel.

## Flujo de trabajo

### 1. Inventario educativo

- Descargar los registros históricos y el inventario 2024-2025.
- Filtrar provincia Cotopaxi, cantón Pujilí y parroquia Zumbahua.
- Normalizar código AMIE, nombres y niveles.
- Comparar altas, bajas y cambios de matrícula.
- Reconstruir coordenadas mediante fuentes públicas y revisión manual.

### 2. Demanda

- Descargar Censo 2022 y marco geoestadístico compatible.
- Construir población por edades para Inicial, EGB y Bachillerato.
- Mantener la agregación necesaria para evitar reidentificación.
- Comparar los resultados de sectores con una superficie de población alternativa si está disponible y autorizada.

### 3. Red y fricción

- Guardar una instantánea fechada de OpenStreetMap.
- Incluir vías, senderos y caminos rurales transitables.
- Reparar componentes, intersecciones y geometrías sin modificar el archivo crudo.
- Calcular tiempos peatonales y corregir velocidad por pendiente.
- Modelar transporte motorizado únicamente como escenario hipotético hasta disponer de rutas verificables.

### 4. Indicadores

- Tiempo mínimo a la institución más cercana por nivel.
- Oportunidades acumuladas dentro de cada umbral.
- Porcentaje y número de estudiantes potenciales cubiertos.
- Población desatendida por sector y nivel.
- Indicador de captación flotante balanceada con matrícula o capacidad.
- Desigualdad mediante Gini y comparación de cuantiles territoriales.

### 5. Escenarios

- Situación actual.
- Mejora de caminos o velocidad peatonal.
- Transporte escolar hipotético.
- Reapertura o nueva localización mediante máxima cobertura o p-mediana.

### 6. Validación

- Verificar manualmente cada escuela y conservar la evidencia.
- Informar distancia de ajuste de cada escuela a la red.
- Contrastar una muestra de rutas con servicios alternativos sin copiar datos sujetos a restricciones.
- Ejecutar sensibilidad de velocidades ±20 %, pendiente y umbrales.
- Publicar tabla de exclusiones y errores, no solo resultados favorables.

## Resultados mínimos para publicación

1. Inventario educativo reproducible.
2. Serie 2009-2024 con explicación de discontinuidades.
3. Mapa de demanda y oferta por nivel.
4. Distribución de tiempos de viaje ponderada por población.
5. Mapa de población desatendida.
6. Comparación base-capacidad-pendiente.
7. Escenarios de mejora con población beneficiada.
8. Anexo de calidad, sensibilidad y licencias.

