# Análisis de los datos (OP1)

> **Versión 1 · 13 de noviembre de 2026.** Describe **qué trae cada fuente de datos** y los primeros conteos de Jalisco. Todavía no hay incendios agrupados ni clasificados: eso llega en la versión 2.
> Todos los números de este documento salen de correr `scripts/01_descargar_firms.py` y `scripts/02_preparar_conafor.py` el 12 de noviembre de 2026. Para repetirlos, basta correr esos dos scripts.
> Objetivo particular al que responde: **OP1** (identificar las variables que distinguen un incendio real de una falsa alarma y las que se relacionan con su severidad).

## 1. Resumen

| Fuente | Qué aporta | Estado | ¿Se activó el plan B? |
| --- | --- | --- | --- |
| F1 · NASA FIRMS | 44,662 puntos de calor en Jalisco (2024 y 2025) | Descargada y recortada | No |
| F2 · CONAFOR | 1,869 incendios forestales registrados en Jalisco (2024 y 2025), con polígono, fechas y superficie | Descargada y limpia | No |
| INEGI · límite estatal | Polígono oficial de Jalisco | Descargado | No |
| F3 · INEGI · localidades | Ubicación y población de cada localidad | Fuente confirmada; falta descargar | No |
| F4 · Uso de suelo y vegetación | Forestal o agrícola; tipo de vegetación | Fuente localizada; falta revisar su contenido | Por decidir |
| F5 · Áreas naturales protegidas | Dentro o fuera de un área protegida | Fuente localizada; falta revisar su contenido | Por decidir |
| F6 · Clima histórico | Viento, humedad y temperatura del día | Servicio probado con una consulta | Por decidir |
| F8 · Bases de brigadas | Origen de los recursos | No se encontró una fuente pública para Jalisco | Probable: bases hipotéticas |

**Lo más importante:** el riesgo mayor del proyecto era que CONAFOR no publicara coordenadas o superficie. Sí las publica, para los dos años, y sin datos faltantes. Con eso se pueden validar los dos pasos de la clasificación.

## 2. F1 · Puntos de calor de NASA FIRMS

**De dónde sale:** archivos anuales por país que FIRMS publica sin pedir clave. Se usan dos sensores:

| Sensor | Satélite | Tamaño del píxel | Cómo da la confianza |
| --- | --- | --- | --- |
| VIIRS | Suomi NPP | 375 m | Letra: `l` (baja), `n` (nominal), `h` (alta) |
| MODIS | Terra y Aqua | 1 km | Número de 0 a 100 |

Los archivos anuales por país de los satélites NOAA-20 y NOAA-21 no existen, así que no se usan.

**Qué trae cada punto:** latitud, longitud, fecha, hora (en tiempo universal), satélite, confianza, FRP (potencia radiativa del fuego, en megawatts), si la detección fue de día o de noche y el tipo de fuente (`type`).

**Qué hace el script 01:** descarga los cuatro archivos de México, deja solo los puntos dentro del polígono de Jalisco, pasa la confianza a una sola escala de 0 a 1, agrega la hora local de Jalisco y las coordenadas en metros (EPSG:32613), y guarda `datos/procesados/puntos_calor_jalisco.csv`.

### Conteos en Jalisco

| Año | VIIRS | MODIS | Total |
| --- | --- | --- | --- |
| 2024 | 18,536 | 4,745 | 23,281 |
| 2025 | 16,885 | 4,496 | 21,381 |
| **Total** | 35,421 | 9,241 | **44,662** |

**Por mes (los dos años juntos):**

| Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Dic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1,322 | 1,794 | 5,709 | 9,710 | 18,177 | 5,549 | 415 | 105 | 89 | 268 | 471 | 1,053 |

De marzo a junio se concentra el 88 % de los puntos, lo que coincide con la temporada de estiaje.

**Otros datos:**

- De día: 29,690 puntos. De noche: 14,972.
- Tipo de fuente: 43,741 puntos son de tipo 0 (vegetación), 910 de tipo 2 (fuente fija en tierra, como industria) y 11 de tipo 3 (sobre agua). No hay puntos de tipo 1 (volcán).
- FRP: la mitad de los puntos tiene 6.9 MW o menos; tres de cada cuatro, 14.7 MW o menos; el máximo es 2,186.5 MW.
- En la región piloto (La Primavera y AMG): 2,237 puntos en 2024 y 2,488 en 2025.

### Observaciones para el diseño

- La columna `type` ya marca las fuentes fijas. Puede ser la base de la variable `fuente_fija`, en lugar de calcularla desde cero.
- La confianza no se usa como filtro (problema P11): se guarda como variable.
- La equivalencia de la confianza de VIIRS a números (baja 0.15, nominal 0.55, alta 0.90) usa el punto medio de los rangos que MODIS define para esas mismas clases. Es un valor inicial.

## 3. F2 · Incendios registrados por CONAFOR

**De dónde sale:** “Concentrado Nacional de Polígonos de Incendios Forestales” 2024 y 2025, publicado por la Gerencia de Manejo del Fuego de CONAFOR en IDEFOR (Infraestructura de Datos Espaciales Forestales).

**Qué trae cada registro:**

| Campo de CONAFOR | Nombre en nuestro archivo | Significado |
| --- | --- | --- |
| (geometría) | polígono, `lat`, `lon`, `x`, `y` | Área quemada y su centro |
| `CLAVEINC` | `id_conafor` | Clave del incendio (año, estado y número) |
| `MUNICIPIO` | `municipio` | Municipio |
| `FECHAINIC` | `fecha_inicio` | Fecha en que empezó |
| `FECHALIQ` | `fecha_fin` | Fecha de liquidación (apagado) |
| `AREA_HA` | `superficie_ha` | Superficie quemada, en hectáreas |
| `CAUSA` | `causa` | Causa probable |
| `TIPVEG` | `vegetacion` | Tipo de vegetación quemada |
| `TIPOINC` | `tipo_incendio` | Superficial, de copa, subterráneo o mixto |
| `TIPIMPAC` | `impacto` | Impacto mínimo, moderado o severo |
| `ANP` | `area_protegida` | Área natural protegida, o “ninguna” |
| `POLIGONO` | `metodo_poligono` | Cómo se trazó el polígono |

**Qué hace el script 02:** descarga los registros de Jalisco, repara polígonos con errores de dibujo, calcula el centro y la duración de cada incendio y guarda una tabla (`incendios_conafor_jalisco.csv`) y los polígonos simplificados (`incendios_conafor_jalisco.geojson`).

### Conteos en Jalisco

| | 2024 | 2025 |
| --- | --- | --- |
| Incendios registrados | 950 | 919 |
| Superficie total (ha) | 112,487 | 88,822 |
| Superficie mediana (ha) | 14.7 | 9.6 |
| Una cuarta parte quemó menos de (ha) | 3.1 | 1.3 |
| Una cuarta parte quemó más de (ha) | 60.9 | 53.4 |
| Incendio más grande (ha) | 4,503.2 | 5,444.9 |
| Incendios en la región piloto | 190 | 205 |
| Incendios en La Primavera | 51 | 56 |
| Superficie en La Primavera (ha) | 1,143 | 1,608 |

- **Datos faltantes:** ninguno en las columnas que usamos. No hay claves repetidas, ni fechas fuera de su año, ni duraciones negativas.
- **Por mes (los dos años):** enero 59, febrero 129, marzo 399, abril 471, mayo 530, junio 232, julio 2, octubre 4, noviembre 13, diciembre 30.
- **Duración:** la mayoría se liquida el mismo día (mediana de 0 días); tres de cada cuatro duran 1 día o menos. El más largo duró 34 días (2024).
- **Tamaño:** la distribución es muy desigual. En 2024, el 10 % más grande quemó más de 230 ha y el 1 % más grande, más de 1,832 ha.
- **Impacto:** mínimo 1,446, moderado 254, severo 169.
- **Áreas protegidas:** 411 incendios ocurrieron en un área natural protegida; 107 de ellos en La Primavera.
- **Vegetación más frecuente:** bosque de encino (613), selva baja caducifolia (455), bosque de pino (380).
- **Causa:** desconocida 1,344, intencional 369, actividades agrícolas 141.
- **Cómo se trazó el polígono:** 1,848 con imágenes de satélite Sentinel y 21 con coordenadas tomadas en campo.

### Observaciones para el diseño

- **Cortes de severidad.** Los cuartiles de 2024 (3.1, 14.7 y 60.9 ha) son un punto de partida natural para los cuatro niveles, como propone el modelo. Se decide en la versión 2 de este reporte.
- **Cruce con los puntos de calor.** Como hay polígono, la distancia se puede medir al borde del área quemada y no solo a un punto. Como hay fecha de inicio y de liquidación, la tolerancia de días se puede aplicar alrededor de ese intervalo.
- **Región piloto.** Hay unos 200 incendios registrados por año en la región piloto. Es más de lo que suponíamos (problema P16), así que habrá días reales con varios incendios simultáneos para los escenarios.
- **Qué es una “falsa alarma”.** CONAFOR solo registra incendios en terreno forestal: sus polígonos excluyen la superficie no forestal. Una quema agrícola no aparece en sus registros, lo que es coherente con tratarla como falsa alarma.

## 4. Fuentes complementarias (revisión inicial)

| Fuente | Qué se encontró | Qué falta |
| --- | --- | --- |
| **INEGI · límite de Jalisco** | El servicio del Marco Geoestadístico (versión de diciembre de 2025) entrega el polígono del estado. Ya se usa en el script 01 y queda en `datos/referencia/jalisco.geojson`. | Nada |
| **F3 · INEGI · localidades** | El mismo servicio entrega las localidades por municipio, con nombre, latitud, longitud, ámbito (urbano o rural) y población total del Censo 2020. Hay que pedirlo municipio por municipio (125 en Jalisco). | Descargar y unir (script 04) |
| **F4 · Uso de suelo y vegetación** | IDEFOR publica el “Conjunto de datos vectoriales de uso del suelo y vegetación, escala 1:250 000, Serie VII” (INEGI) y un “Continuo de uso de suelo y vegetación de Jalisco”. | Revisar campos, tamaño y cuál conviene |
| **F5 · Áreas naturales protegidas** | IDEFOR publica las áreas naturales protegidas federales (2024) y una capa de áreas protegidas de Jalisco. | Confirmar si la capa de Jalisco incluye las estatales |
| **F6 · Clima histórico** | Open-Meteo respondió una consulta de prueba de un día de 2025 con temperatura máxima, humedad mínima y viento máximo, sin clave. El uso gratuito es no comercial y tiene un límite diario de consultas. | Calcular cuántas consultas se necesitan y decidir si alcanza |
| **F8 · Bases de brigadas** | En IDEFOR solo hay brigadas y campamentos de la Megalópolis (centro del país). | Buscar en fuentes de SEMADET y del OPD Bosque La Primavera; si no hay, bases hipotéticas declaradas como supuesto |

## 5. Limitaciones y pendientes

1. **CONAFOR no registra todo.** Un punto de calor sin registro no es necesariamente una falsa alarma; puede ser un incendio que no se documentó. Las etiquetas tienen ruido y así se declarará en la evaluación.
2. **Las cifras del planteamiento no coinciden exactamente con estos datos.** El planteamiento cita 912 incendios y 88,536 ha en Jalisco en 2025, y 49 incendios y 1,936 ha en La Primavera. Los polígonos dan 919 incendios y 88,822 ha en Jalisco, y 56 incendios y 1,608 ha con la etiqueta “La Primavera”. Las diferencias pueden venir de cortes de fecha distintos o de cómo se delimita La Primavera. **Hay que citar la fuente exacta de cada cifra antes del informe final.**
3. **Las horas de FIRMS están en tiempo universal.** Se agrega la hora local (6 horas menos) porque CONAFOR registra fechas locales. Un punto detectado a la 1:00 UTC pertenece al día anterior en Jalisco.
4. **Un polígono de 1,869 queda con un cruce** después de simplificarlo y redondear coordenadas. No afecta las distancias, pero el script que los lea debe repararlo al cargar.
5. **Falta todo lo que depende del agrupamiento:** cuántos incendios candidatos hay, cuántos coinciden con CONAFOR y qué variables los distinguen. Es el contenido de la versión 2.

## 6. Fuentes

- NASA FIRMS, archivos anuales por país: <https://firms.modaps.eosdis.nasa.gov/country/>
- CONAFOR, IDEFOR, Concentrado Nacional de Polígonos de Incendios Forestales 2024 y 2025: <https://idefor.cnf.gob.mx/>
- INEGI, Marco Geoestadístico (servicio de consulta del catálogo): <https://www.inegi.org.mx/servicios/catalogounico.html>
- Open-Meteo, datos históricos: <https://open-meteo.com/>
