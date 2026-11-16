# Modelo de decisión (OP2)

> **Versión 2 · 16 de noviembre de 2026.** Agrega a la versión 1 las **reglas de clasificación** (pasos A y B), la **tabla de respuesta** y el **plan de ataque** (bases, rutas, orden de atención y reparto de brigadas). Falta para la versión 3: el algoritmo húngaro, las métricas del plan y el bosque aleatorio.
> Objetivo particular al que responde: **OP2** (diseñar el modelo de clasificación y el de plan de ataque).
> Todos los parámetros están en `scripts/config.py`, cada uno con su fuente o su justificación. Los números de respaldo están en `reportes/analisis_datos.md` (versión 2).

## 1. De puntos de calor a una decisión

```
puntos de calor ──► incendios candidatos ──► variables ──► ¿real o falsa alarma? ──► nivel ──► plan de ataque
   (script 01)          (script 03)          (script 04)        (paso A)            (paso B)   (región piloto)
                                                              └────── script 05 ──────┘   scripts 06 y plan.js
```

El satélite no entrega incendios: entrega **puntos de calor sueltos**. Un incendio grande produce cientos de puntos y una fuente industrial produce puntos todo el año. El modelo hace cuatro cosas, en orden: junta los puntos en incendios candidatos, describe cada candidato con variables, lo clasifica y, en la región piloto, propone cómo repartir las brigadas.

**La herramienta recomienda; no actúa.** No envía alertas ni solicita recursos.

## 2. Agrupamiento: de puntos a incendios candidatos

Dos puntos de calor pertenecen al mismo incendio candidato si están **cerca en distancia y cerca en tiempo**. Si A está cerca de B y B está cerca de C, los tres son el mismo incendio: así un incendio que avanza se sigue como uno solo.

| Parámetro | Valor | Justificación |
| --- | --- | --- |
| `DISTANCIA_MAXIMA_M` | 1,000 m | Un píxel de MODIS mide 1 km: dos detecciones del mismo fuego pueden quedar separadas hasta esa distancia |
| `VENTANA_HORAS` | 48 h | Tres de cada cuatro incendios registrados por CONAFOR duran 1 día o menos; 48 horas dan margen para que el satélite vuelva a pasar |

Se usa **DBSCAN** (scikit-learn). Como solo mide una distancia, el tiempo se convierte a “metros”: 48 horas pesan lo mismo que 1,000 m. Por eso la distancia y el tiempo **se combinan**: dos puntos a 700 m y 34 horas quedan en el límite. Un punto solo también es un candidato (`min_samples = 1`): un incendio pequeño real puede verse una sola vez.

**Resultado:** de 44,662 puntos de calor salen 14,118 incendios candidatos (7,029 en 2024 y 7,089 en 2025). Seis de cada diez son un punto solo.

**Cómo se comprobó:** `pruebas/probar_agrupamiento.py`, con seis puntos hechos a mano.

## 3. Variables de cada incendio candidato

| Variable | Qué significa | Cómo se calcula |
| --- | --- | --- |
| `n_puntos` | Tamaño aparente | Número de puntos de calor |
| `n_pasadas` | Persistencia | Detecciones del mismo satélite con menos de 30 minutos de diferencia cuentan como una pasada (el satélite tarda unos 100 minutos en dar la vuelta) |
| `duracion_horas` | Cuánto duró | De la primera a la última detección |
| `frp_max`, `frp_total` | Intensidad (MW) | Máximo y suma de la potencia radiativa |
| `confianza_media` | Confianza del satélite | Promedio, de 0 a 1 |
| `fraccion_nocturna` | Parte detectada de noche | De 0 a 1 |
| `fuente_fija` | El lugar emite calor casi todo el año | 1 si al menos la mitad de sus puntos son “fuente fija” según FIRMS, o si en su cuadro de 1 km hubo calor en 6 o más meses del año |
| `es_forestal`, `vegetacion` | Terreno forestal o no | Tipo de vegetación del INEGI (Serie VII) en el centro del candidato. No es forestal lo agrícola, los pastizales inducidos y cultivados, lo urbano, el agua y lo que no tiene vegetación |
| `en_area_protegida` | Dentro de un área natural protegida federal | Áreas de CONANP (julio de 2025) |
| `dist_localidad_km`, `poblacion_localidad` | Localidad más cercana | Solo localidades de 100 habitantes o más (INEGI, Censo 2020) |
| `en_piloto` | Está en la región piloto | Caja de La Primavera y el AMG |

Las variables de clima (viento, humedad y temperatura) entran en el Sprint 2.

## 4. Clasificación · paso A: ¿incendio real o falsa alarma?

### Las etiquetas

Para ajustar y comprobar las reglas hace falta saber qué candidatos fueron incendios. Un candidato se etiqueta como **real** si su centro queda a **1 km o menos** del polígono de un incendio registrado por CONAFOR y sus fechas coinciden con un margen de **2 días** (`scripts/04b_etiquetar.py`). Esos dos valores se eligieron con 2024: más lejos o con más días, las coincidencias se reparten como si fueran casualidad.

### Las reglas

Se aplican en este orden; la primera que se cumple decide.

| # | Regla | Resultado | De los candidatos de 2024 que la cumplieron, coincidieron con CONAFOR |
| --- | --- | --- | --- |
| 1 | Es una fuente fija | Falsa alarma | 0 de 154 |
| 2 | Terreno forestal **y** visto en 2 o más pasadas | **Real** | 346 de 965 (36 %) |
| 3 | 15 o más puntos de calor | **Real** | 10 de 21 (48 %) |
| 4a | Terreno forestal, pero una sola pasada | Falsa alarma | 234 de 2,095 (11 %) |
| 4b | Terreno no forestal | Falsa alarma | 100 de 3,794 (3 %) |

La última columna es la `prob_real` que acompaña a cada clasificación.

### Por qué estas reglas y no las de partida

Las reglas iniciales eran “2 o más pasadas → real” y “forestal con 10 MW o más → real”. Con 2024 se vio que:

- **El terreno forestal es lo que más separa**: coincide con CONAFOR el 18.9 % de los candidatos forestales y el 2.8 % de los no forestales.
- **La persistencia separa, pero sobre todo en terreno forestal**: con 2 pasadas, 21 % en forestal contra 4 % fuera.
- **La intensidad sola separa poco**: hasta 100 MW la diferencia es pequeña, y el umbral de 10 MW lo supera el 43 % de los candidatos.

### Qué tan bien funciona

| | Clasificados como reales | Precisión | Sensibilidad | F1 |
| --- | --- | --- | --- | --- |
| Reglas de partida, 2025 | 1,887 | 0.19 | 0.67 | 0.30 |
| **Reglas ajustadas, 2025 (prueba)** | 693 | 0.33 | 0.43 | 0.37 |

Las reglas se ajustaron **solo con 2024**; 2025 se usa únicamente para probar. Los números son bajos y hay que decirlo: de cada tres incendios que la herramienta llama reales, uno coincide con un registro. Parte se debe a las etiquetas: el satélite solo ve cerca de la mitad de los incendios que CONAFOR registra, y hay fuego real que CONAFOR no registró. El bosque aleatorio (Sprint 2) es la comparación pendiente.

## 5. Clasificación · paso B: nivel de severidad

Solo para los incendios que el paso A considera reales.

### Niveles reales

Se definen con la superficie que registró CONAFOR. Los cortes son los cuartiles (redondeados) de los incendios de 2024 que sí detectó el satélite:

| Nivel | Superficie quemada |
| --- | --- |
| Bajo | Menos de 30 ha |
| Medio | De 30 a 100 ha |
| Alto | De 100 a 600 ha |
| Crítico | 600 ha o más |

### Puntaje

Cada condición que se cumple suma puntos.

| Condición | Puntos | Por qué |
| --- | --- | --- |
| 5, 15 o 40 puntos de calor o más | +1, +2 o +3 | A partir de 15 puntos la superficie sube mucho (287 ha de mediana; con 40 o más, 1,019 ha) |
| Intensidad máxima de 30 o 100 MW o más | +1 o +2 | Con más de 100 MW la mediana es 323 ha, contra 60 ha con 10 MW o menos |
| Duración de 24 horas o más | +1 | 355 ha de mediana, contra 61 ha en los de una sola detección |
| Dentro de un área natural protegida | +1 | No predice el tamaño; cuenta por lo que está en riesgo |
| A 4 km o más de la localidad más cercana | +1 | **Hallazgo de 2024:** lejos de las poblaciones los incendios son mucho más grandes (837 ha a más de 8 km contra 38 ha a menos de 2 km): se detectan y se atienden más tarde |

| Puntaje | Nivel |
| --- | --- |
| 0 | Bajo |
| 1 o 2 | Medio |
| 3 o 4 | Alto |
| 5 o más | Crítico |

### Regla de seguridad

Un incendio a **menos de 1 km** de una localidad (de 100 habitantes o más) sube **al menos a nivel alto**, aunque sea pequeño. La regla nunca baja un nivel ni convierte una falsa alarma en incendio. El valor inicial era 2 km, pero a esa distancia está 1 de cada 5 incendios reales y la regla dejaría de ser excepcional; el equipo confirmó 1 km el 13 de noviembre.

### Qué tan bien funciona

| Incendios reales para las reglas y con registro de CONAFOR | 2024 (ajuste) | 2025 (prueba) |
| --- | --- | --- |
| Mismo nivel | 0.43 | 0.49 |
| Mismo nivel o uno de diferencia | 0.84 | 0.93 |
| Críticos clasificados como bajos | 1 de 104 | 2 de 47 |

Acierta el nivel exacto en menos de la mitad de los casos, pero casi nunca falla por más de un nivel y casi nunca llama “bajo” a un incendio crítico, que es el error más peligroso. Ninguna variable del satélite predice bien la superficie: un incendio de cientos de hectáreas puede aparecer como un solo punto de calor.

### Las razones

Cada incendio guarda la lista de razones de su clasificación, por ejemplo: “Terreno forestal (Bosque de encino-pino) y visto en 6 pasadas de satélite”, “15 puntos de calor (+2)”, “Duró 35 horas (+1)”. El mapa las muestra en la ficha y la página “Probar clasificación” las muestra para un incendio inventado.

**Cómo se comprobó:** `pruebas/probar_clasificacion.py`, con 15 incendios inventados de resultado conocido. La página “Probar clasificación” da el mismo resultado en esos 15 casos.

## 6. Tabla de respuesta

Traduce cada nivel en los recursos que se recomiendan.

| Nivel | Brigadas terrestres | Unidad con motobomba | Apoyo aéreo |
| --- | --- | --- | --- |
| Bajo | 1 | No | No |
| Medio | 2 | No | No |
| Alto | 3 | Sí | No |
| Crítico | 4 | Sí | **Se recomienda solicitarlo** |

**Es un supuesto del equipo.** No está validado por un brigadista ni por un especialista en manejo del fuego. La lógica: cada nivel pide una brigada más que el anterior, la motobomba entra desde el nivel alto y en el crítico se recomienda pedir apoyo aéreo. La herramienta no asigna aeronaves ni solicita nada.

## 7. Plan de ataque (solo en la región piloto)

### Bases y brigadas

No se encontró una fuente pública con la ubicación de las bases de brigadas en la región. Se usan **seis bases hipotéticas**, colocadas en el centro de localidades reales de los municipios que participan en el combate de incendios en La Primavera (`datos/referencia/bases.csv`):

| Base | Brigadas terrestres | Unidades con motobomba |
| --- | --- | --- |
| Tala | 2 | 0 |
| El Arenal | 1 | 0 |
| La Venta del Astillero (Zapopan) | 2 | 1 |
| Zapopan | 3 | 1 |
| Tlajomulco de Zúñiga | 2 | 0 |
| Guadalajara | 2 | 1 |
| **Total** | **12** | **3** |

Las ubicaciones y las cantidades son un **supuesto**. En la página del plan, el usuario podrá marcar qué brigadas están disponibles.

### Rutas y tiempos (se calculan antes, en Python)

`scripts/06_rutas_region_piloto.py`:

1. Descarga de OpenStreetMap la red de caminos de la región piloto (194,429 cruces y 459,629 tramos), incluidas las **brechas**, que son el acceso al bosque.
2. A cada tramo le pone una velocidad según su tipo (de 20 km/h en brechas a 90 km/h en autopistas) cuando OpenStreetMap no trae el límite. Son velocidades supuestas, sin tráfico.
3. El **punto de acceso** de cada incendio es el cruce de caminos más cercano a su centro. La ruta llega ahí, no al centro del fuego (decisión D3: bloquear una zona alrededor del fuego hacía inalcanzable el destino).
4. Con el algoritmo de **Dijkstra**, una corrida por base da el camino más rápido a todos los cruces de la red.
5. Guarda el tiempo en minutos y el trazo de cada ruta en `web/datos/rutas_piloto.json`.

**Resultado:** 570 rutas (6 bases por 95 incendios reales de la región piloto en 2024 y 2025). Tiempo mediano de llegada: 41 minutos; mínimo 6 y máximo 113. La mitad de los puntos de acceso queda a unos 700 m o menos del centro del incendio; el más lejano, a 6.8 km.

### Reparto de brigadas (se calcula en el navegador)

`web/js/plan.js` recibe los incendios de un escenario, las brigadas disponibles y los tiempos, y hace tres cosas:

1. **Demanda.** Cada incendio pide lo que dice la tabla de respuesta para su nivel.
2. **Orden de atención.** Primero el nivel más grave; a igual nivel, el que se alcanza más rápido.
3. **Reparto**, con uno de estos métodos (misma entrada, misma salida):

| Método | Cómo reparte | Papel |
| --- | --- | --- |
| **Voraz** | Recorre los incendios en el orden de atención y a cada uno le da sus brigadas libres más rápidas | Referencia B |
| **Más cercana** | Una sola brigada por incendio, en el orden en que se detectaron, la de la base más cercana **en línea recta** | Referencia A (lo más simple que se podría hacer) |
| **Húngaro** | Busca el reparto de menor tiempo total, ponderado por nivel | Propuesta. Llega en la versión 3 |

Las unidades con motobomba se reparten aparte: cada incendio que la pide recibe la unidad libre que llega más rápido, en el orden de atención.

**Salida:** qué brigada va a qué incendio y en cuántos minutos, cuántas brigadas le faltaron a cada incendio, qué incendios se quedaron sin motobomba y en cuáles se recomienda pedir apoyo aéreo.

### Por qué importa comparar métodos

En un caso pequeño hecho a mano (4 brigadas y 3 incendios), el voraz le da al primer incendio las dos brigadas más rápidas y deja al segundo con las que tardan 40 minutos; la “más cercana” manda a un incendio la brigada que está cerca en línea recta pero tarda 40 minutos por camino. Ninguno de los dos ve el problema completo: eso es lo que debe resolver el húngaro.

**Cómo se comprobó:** `pruebas/probar_plan.py` y la función `probarPlan()` de `plan.js` corren ese mismo caso y dan el mismo resultado.

## 8. Limitaciones

**De la clasificación**
- **Etiquetas con ruido.** CONAFOR no registra todo y el satélite no ve todo. La precisión reportada es un mínimo.
- **El agrupamiento puede unir incendios vecinos** o partir uno si el satélite deja de verlo más de 48 horas.
- **La severidad se predice mal con datos de satélite.** El puntaje sirve para ordenar, no para estimar hectáreas.
- **Las áreas protegidas son solo las federales.** Una de ellas cubre buena parte del norte de Jalisco.
- **Los ajustes se hicieron a mano**, probando variantes con 2024.

**Del plan de ataque**
- **Las bases, el número de brigadas y la tabla de respuesta son supuestos del equipo.**
- **Los tiempos son de un vehículo sin tráfico y con velocidades supuestas.** No consideran el estado real de las brechas ni el tramo a pie desde el punto de acceso.
- **El punto de acceso puede quedar lejos del fuego** cuando no hay caminos cerca (hasta 6.8 km).
- **Los caminos vienen de OpenStreetMap**, que en zonas de bosque puede estar incompleto.
- **El plan es una foto de un momento.** No considera que los incendios crecen ni que las brigadas se liberan.
