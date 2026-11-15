# Análisis de los datos (OP1)

> **Versión 2 · 15 de noviembre de 2026.** Además de qué trae cada fuente (versión 1), responde las dos preguntas de OP1: **qué variables distinguen un incendio real de una falsa alarma** y **cuáles se relacionan con su severidad**. Con eso se ajustaron las reglas de clasificación.
> Todos los números salen de correr los scripts 01 a 05 el 13 de noviembre de 2026; para repetirlos basta correrlos en orden. **Las reglas se ajustaron solo con 2024; 2025 se usa únicamente para probar.**
> Objetivo particular al que responde: **OP1** (identificar las variables que distinguen un incendio real de una falsa alarma y las que se relacionan con su severidad).

## 1. Resumen

| Fuente | Qué aporta | Estado | ¿Se activó el plan B? |
| --- | --- | --- | --- |
| F1 · NASA FIRMS | 44,662 puntos de calor en Jalisco (2024 y 2025) | Descargada y recortada | No |
| F2 · CONAFOR | 1,869 incendios forestales registrados en Jalisco (2024 y 2025), con polígono, fechas y superficie | Descargada y limpia | No |
| INEGI · límite estatal | Polígono oficial de Jalisco | Descargado | No |
| F3 · INEGI · localidades | 10,332 localidades de Jalisco con su población | Descargada | No |
| F4 · Uso de suelo y vegetación | Tipo de vegetación de cada lugar (INEGI, Serie VII) | Descargada del geoportal de CONABIO | No (cambió el sitio de descarga) |
| F5 · Áreas naturales protegidas | Áreas protegidas **federales** (CONANP, julio de 2025) | Descargada del geoportal de CONABIO | **Sí: solo federales** |
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

- **Cortes de severidad.** Los cuartiles de todos los registros de 2024 son 3.1, 14.7 y 60.9 ha. Al final no se usaron: los incendios que detecta el satélite son mucho más grandes, así que los niveles se definieron con los cuartiles de esos (sección 7).
- **Cruce con los puntos de calor.** Como hay polígono, la distancia se puede medir al borde del área quemada y no solo a un punto. Como hay fecha de inicio y de liquidación, la tolerancia de días se puede aplicar alrededor de ese intervalo.
- **Región piloto.** Hay unos 200 incendios registrados por año en la región piloto. Es más de lo que suponíamos (problema P16), así que habrá días reales con varios incendios simultáneos para los escenarios.
- **Qué es una “falsa alarma”.** CONAFOR solo registra incendios en terreno forestal: sus polígonos excluyen la superficie no forestal. Una quema agrícola no aparece en sus registros, lo que es coherente con tratarla como falsa alarma.

## 4. Fuentes complementarias

| Fuente | Qué se encontró | Qué falta |
| --- | --- | --- |
| **INEGI · límite de Jalisco** | El servicio del Marco Geoestadístico (versión de diciembre de 2025) entrega el polígono del estado. Ya se usa en el script 01 y queda en `datos/referencia/jalisco.geojson`. | Nada |
| **F3 · INEGI · localidades** | El mismo servicio entrega las localidades por municipio, con nombre, latitud, longitud, ámbito (urbano o rural) y población total del Censo 2020. Se pidieron los 125 municipios: 10,332 localidades con habitantes (285 urbanas y 10,047 rurales). La mitad tiene 14 habitantes o menos, por eso solo se usan las de 100 o más (2,091). | Nada |
| **F4 · Uso de suelo y vegetación** | “Uso del suelo y vegetación, escala 1:250 000, Serie VII” del INEGI. El servidor de mapas de IDEFOR dejó de responder el 12 y 13 de noviembre, así que la misma capa se bajó del geoportal de CONABIO (317 MB, todo el país). En Jalisco tiene 100 tipos de vegetación. Se considera **no forestal** lo agrícola, los pastizales inducidos y cultivados, las zonas urbanas, el agua y los terrenos sin vegetación; lo demás es forestal. | Nada |
| **F5 · Áreas naturales protegidas** | Áreas naturales protegidas federales de CONANP (julio de 2025), también desde el geoportal de CONABIO. En Jalisco y su borde hay 24, entre ellas La Primavera, Sierra de Manantlán y Sierra de Quila. **No incluye las estatales ni las municipales** (por ejemplo, Cerro Viejo o la Barranca del Río Santiago). | Agregar las estatales si IDEFOR vuelve |
| **F6 · Clima histórico** | Open-Meteo respondió una consulta de prueba de un día de 2025 con temperatura máxima, humedad mínima y viento máximo, sin clave. El uso gratuito es no comercial y tiene un límite diario de consultas. | Calcular cuántas consultas se necesitan y decidir si alcanza |
| **F8 · Bases de brigadas** | En IDEFOR solo hay brigadas y campamentos de la Megalópolis (centro del país). | Buscar en fuentes de SEMADET y del OPD Bosque La Primavera; si no hay, bases hipotéticas declaradas como supuesto |

## 5. De puntos de calor a incendios candidatos, y su cruce con CONAFOR

El script 03 agrupó los 44,662 puntos de calor en **14,118 incendios candidatos** (7,029 en 2024 y 7,089 en 2025). El script 04b cruza cada candidato con los registros de CONAFOR: es “real” si su centro queda cerca del polígono de un incendio registrado y sus fechas coinciden.

### Cómo se eligió la tolerancia (con 2024)

El punto de partida era 3 km y 3 días. Los datos de 2024 muestran que es demasiado.

**Distancia.** Parejas candidato-registro cuyas fechas se traslapan:

| Distancia del candidato al polígono | Parejas | Parejas por km² |
| --- | --- | --- |
| Dentro del polígono | 382 | — |
| Hasta 250 m | 152 | — |
| De 250 a 500 m | 37 | — |
| De 500 m a 1 km | 48 | 20 |
| De 1 a 2 km | 81 | 9 |
| De 2 a 3 km | 67 | 4 |
| De 3 a 6 km | 280 | 3 |

Casi todas las coincidencias están dentro del polígono o a unos cientos de metros. Más allá de 1 km, las parejas por km² se aplanan: se parecen a lo que daría la casualidad en plena temporada. **Tolerancia elegida: 1 km.**

**Días.** Parejas a 1 km o menos: 619 se traslapan en fecha. Con 1 y 2 días de separación hay 33 y 29 (antes) y 36 y 26 (después); de 3 días en adelante se estabiliza entre 14 y 21 por día, que es el nivel de casualidad. **Tolerancia elegida: 2 días.**

### Resultado del cruce

| | 2024 | 2025 |
| --- | --- | --- |
| Incendios candidatos | 7,029 | 7,089 |
| Candidatos que coinciden con CONAFOR | 690 (9.8 %) | 542 (7.6 %) |
| Registros de CONAFOR con al menos un candidato | 463 de 950 (49 %) | 418 de 919 (45 %) |

Dos lecturas que hay que tener presentes en todo el proyecto:

- **El satélite solo ve cerca de la mitad de los incendios que CONAFOR registra.** La mayoría de los incendios registrados son pequeños y duran menos de un día, y pueden ocurrir entre dos pasadas.
- **Nueve de cada diez candidatos no coinciden con ningún registro.** Ahí hay quemas agrícolas y fuentes fijas, pero también incendios que nadie documentó. Por eso “no coincide con CONAFOR” no significa “falsa alarma” con certeza.

## 6. Qué distingue a un incendio real de una falsa alarma (2024)

Para cada variable, qué parte de los candidatos de 2024 coincide con CONAFOR. El promedio general es 9.8 %.

| Variable | Valor | Candidatos | Coinciden con CONAFOR |
| --- | --- | --- | --- |
| **Pasadas de satélite** | 1 | 5,530 | 5.6 % |
| | 2 | 891 | 13.7 % |
| | 3 | 252 | 31.0 % |
| | 4 o 5 | 179 | 38.0 % |
| | 6 o más | 177 | 63.3 % |
| **Puntos de calor** | 1 | 4,120 | 5.3 % |
| | 5 a 14 | 584 | 25.7 % |
| | 15 a 39 | 106 | 60.4 % |
| | 40 o más | 69 | 84.1 % |
| **Terreno** | No forestal | 3,961 | 2.8 % |
| | Forestal | 3,068 | 18.9 % |
| **Fuente fija** | Sí | 154 | 0.0 % |
| **Área natural protegida** | Dentro | 355 | 22.3 % |
| **Intensidad máxima (FRP)** | Hasta 5 MW | 2,251 | 5.4 % |
| | De 10 a 20 MW | 1,461 | 10.1 % |
| | De 50 a 100 MW | 382 | 17.3 % |
| | Más de 100 MW | 199 | 37.2 % |

Lo que más separa es la **combinación de terreno y persistencia**:

| | 1 pasada | 2 pasadas | 3 o más |
| --- | --- | --- | --- |
| No forestal | 2.2 % | 3.7 % | 13.3 % |
| Forestal | 11.1 % | 21.3 % | 52.0 % |

**Conclusiones:**

1. **Terreno forestal** es la variable más útil: multiplica por siete la probabilidad de coincidir.
2. **La persistencia** (pasadas) y **el tamaño** (puntos) suben la probabilidad de forma constante.
3. **Fuente fija** funciona perfecto en 2024: ninguna de las 154 coincide.
4. **La intensidad sola separa poco**: hasta los 100 MW la diferencia es pequeña. Por eso salió de la regla del paso A.
5. **La confianza del satélite no ayuda**: los candidatos de confianza alta coinciden igual que los de confianza media (alrededor de 10 %).

## 7. Qué se relaciona con la severidad (2024)

Se mide con la superficie que registró CONAFOR en los 690 candidatos de 2024 que coinciden.

**Los incendios que ve el satélite son más grandes que el incendio típico.** La mediana de todos los registros de 2024 es 14.7 ha; la de los que detectó el satélite, 97.4 ha. Sus cuartiles son 31.5, 97.4 y 606.3 ha. Con ellos, redondeados, se definen los niveles reales:

| Nivel real | Superficie | Candidatos de 2024 |
| --- | --- | --- |
| Bajo | Menos de 30 ha | 168 |
| Medio | De 30 a 100 ha | 180 |
| Alto | De 100 a 600 ha | 166 |
| Crítico | 600 ha o más | 176 |

Superficie mediana según cada variable:

| Variable | Valor | Superficie mediana (ha) |
| --- | --- | --- |
| **Puntos de calor** | 1 | 72 |
| | 5 a 14 | 84 |
| | 15 a 39 | 287 |
| | 40 o más | 1,019 |
| **Duración** | Una sola detección | 61 |
| | Más de 24 horas | 355 |
| **Intensidad máxima** | Hasta 10 MW | 60 |
| | Más de 100 MW | 323 |
| **Distancia a la localidad más cercana** | Menos de 2 km | 38 |
| | De 4 a 6 km | 131 |
| | Más de 8 km | 837 |

**Conclusiones:**

1. **Ninguna variable predice bien la superficie.** La relación más fuerte es moderada (correlación de rangos de 0.29 a 0.36). Un incendio de cientos de hectáreas puede aparecer como un solo punto de calor.
2. **El tamaño solo dice algo cuando es grande**: de 1 a 14 puntos la superficie casi no cambia; de 15 en adelante sube mucho.
3. **Hallazgo no previsto: la lejanía.** Los incendios lejos de las poblaciones son mucho más grandes (837 ha a más de 8 km contra 38 ha a menos de 2 km). Es razonable: se detectan y se atienden más tarde. Se agregó como condición del puntaje.
4. **Estar en un área protegida no se relaciona con el tamaño** (correlación de −0.03). Se conserva en el puntaje porque indica lo que está en riesgo, no porque prediga superficie.

## 8. Reglas ajustadas y primer resultado

### Paso A · ¿real o falsa alarma?

| Regla | Punto de partida | Ajustada con 2024 |
| --- | --- | --- |
| 1 | Fuente fija → falsa alarma | Igual |
| 2 | 2 o más pasadas → real | **Forestal y** 2 o más pasadas → real |
| 3 | Forestal y FRP de 10 MW o más → real | 15 o más puntos de calor → real |
| 4 | Lo demás → falsa alarma | Igual |

| | Clasificados como reales | Precisión | Sensibilidad | F1 |
| --- | --- | --- | --- | --- |
| Punto de partida, 2024 | 2,230 | 0.21 | 0.68 | 0.32 |
| **Ajustada, 2024 (ajuste)** | 986 | 0.36 | 0.52 | 0.42 |
| Punto de partida, 2025 | 1,887 | 0.19 | 0.67 | 0.30 |
| **Ajustada, 2025 (prueba)** | 693 | 0.33 | 0.43 | 0.37 |

*Precisión:* de los que la regla llama reales, cuántos coinciden con CONAFOR. *Sensibilidad:* de los que coinciden con CONAFOR, cuántos encuentra la regla.

**Cómo leer estos números con honestidad:** son bajos. De cada tres incendios que la herramienta llama reales, uno coincide con un registro; y encuentra cerca de la mitad de los que sí están registrados. La regla ajustada es mejor que la de partida (F1 de 0.37 contra 0.30 en el año de prueba), pero pierde sensibilidad. Parte de la baja precisión es ruido de las etiquetas: fuego persistente en terreno forestal que CONAFOR no registró cuenta aquí como error. El bosque aleatorio del Sprint 2 es la comparación que falta.

### Paso B · nivel de severidad

Puntaje: puntos de calor (5, 15 o 40: +1, +2, +3), intensidad (30 o 100 MW: +1, +2), duración de 24 horas o más (+1), área natural protegida (+1) y, **nuevo**, a 4 km o más de la localidad más cercana (+1). Niveles: 0 bajo, 1 o 2 medio, 3 o 4 alto, 5 o más crítico (el punto de partida era 0-1, 2-3, 4-5 y 6 o más).

| Incendios reales para la regla y con registro de CONAFOR | 2024 (ajuste) | 2025 (prueba) |
| --- | --- | --- |
| Cuántos | 356 | 231 |
| Mismo nivel | 0.43 | 0.49 |
| Mismo nivel o uno de diferencia | 0.84 | 0.93 |
| Críticos clasificados como bajos | 1 de 104 | 2 de 47 |

Acierta el nivel exacto en menos de la mitad de los casos, pero casi nunca se equivoca por más de un nivel y casi nunca llama “bajo” a un incendio crítico, que es el error más peligroso. Adivinar siempre el nivel más común acertaría el 26 %.

### Regla de seguridad

El valor inicial era 2 km. A esa distancia de una localidad (de 100 habitantes o más) está el 20 % de los incendios reales de 2024: la regla dejaría de ser excepcional. A menos de 1 km está el 5 %. **Se usa 1 km**; es una decisión de criterio que el equipo confirmó el 13 de noviembre. Con 1 km, la regla subió de nivel a 21 incendios en 2024 y a 17 en 2025.

### Lo que queda clasificado

| | 2024 | 2025 |
| --- | --- | --- |
| Clasificados como reales | 986 | 693 |
| Bajo / medio / alto / crítico | 130 / 483 / 264 / 109 | 98 / 328 / 168 / 99 |
| Reales en la región piloto | 53 | 42 |

## 9. Limitaciones y pendientes

1. **CONAFOR no registra todo.** Un punto de calor sin registro no es necesariamente una falsa alarma; puede ser un incendio que no se documentó. Las etiquetas tienen ruido y así se declarará en la evaluación.
2. **Las cifras del planteamiento no coinciden exactamente con estos datos.** El planteamiento cita 912 incendios y 88,536 ha en Jalisco en 2025, y 49 incendios y 1,936 ha en La Primavera. Los polígonos dan 919 incendios y 88,822 ha en Jalisco, y 56 incendios y 1,608 ha con la etiqueta “La Primavera”. Las diferencias pueden venir de cortes de fecha distintos o de cómo se delimita La Primavera. **Hay que citar la fuente exacta de cada cifra antes del informe final.**
3. **Las horas de FIRMS están en tiempo universal.** Se agrega la hora local (6 horas menos) porque CONAFOR registra fechas locales. Un punto detectado a la 1:00 UTC pertenece al día anterior en Jalisco.
4. **Un polígono de 1,869 queda con un cruce** después de simplificarlo y redondear coordenadas. El script 04b lo repara al cargarlo.
5. **Las etiquetas tienen ruido en los dos sentidos:** el satélite no ve la mitad de los incendios registrados, y hay fuego real que CONAFOR no registró. La precisión que se reporta es un mínimo.
6. **Si un candidato coincide con varios registros, se queda con el más cercano.** Un incendio muy grande que CONAFOR partió en varios registros queda con la superficie de uno solo.
7. **Las áreas protegidas son solo las federales.** Una de ellas (C.A.D.N.R. 043) cubre buena parte del norte de Jalisco, así que ahí casi todo incendio suma un punto.
8. **El ajuste se hizo a mano**, probando variantes con 2024. No es una búsqueda exhaustiva; el bosque aleatorio del Sprint 2 dirá cuánto se puede mejorar.
9. **Faltan las variables de clima** (Sprint 2).

## 10. Fuentes

- NASA FIRMS, archivos anuales por país: <https://firms.modaps.eosdis.nasa.gov/country/>
- CONAFOR, IDEFOR, Concentrado Nacional de Polígonos de Incendios Forestales 2024 y 2025: <https://idefor.cnf.gob.mx/>
- INEGI, Marco Geoestadístico (servicio de consulta del catálogo): <https://www.inegi.org.mx/servicios/catalogounico.html>
- INEGI, Uso del suelo y vegetación, escala 1:250 000, Serie VII, distribuido por el geoportal de CONABIO: <http://geoportal.conabio.gob.mx/>
- CONANP, Áreas Naturales Protegidas Federales de México, julio de 2025, distribuido por el geoportal de CONABIO: <http://geoportal.conabio.gob.mx/>
- Open-Meteo, datos históricos: <https://open-meteo.com/>
