# Modelo de decisión (OP2)

> **Versión 1 · 14 de noviembre de 2026.** Cubre la primera mitad del modelo: **cómo se agrupan los puntos de calor en incendios candidatos** y **qué variables se calculan de cada uno**. La versión 2 agrega las reglas de clasificación (pasos A y B), la tabla de respuesta y el plan de ataque.
> Objetivo particular al que responde: **OP2** (diseñar el modelo de clasificación y el de plan de ataque).
> Todos los números salen de correr los scripts 01 a 04 el 12 de noviembre de 2026. Los parámetros están en `scripts/config.py`, cada uno con su fuente o su justificación.

## 1. De puntos de calor a una decisión

```
puntos de calor ──► incendios candidatos ──► variables ──► ¿real o falsa alarma? ──► nivel ──► plan de ataque
   (script 01)          (script 03)          (script 04)        (paso A)            (paso B)   (región piloto)
                                                              └──────── versión 2 de este documento ────────┘
```

El satélite no entrega incendios: entrega **puntos de calor sueltos**. Un incendio grande produce cientos de puntos y una fuente industrial produce puntos todo el año. Antes de clasificar hay que decidir qué puntos forman un mismo incendio y describir cada incendio con números que se puedan comparar.

## 2. Agrupamiento: de puntos a incendios candidatos

### La regla

Dos puntos de calor pertenecen al mismo incendio candidato si están **cerca en distancia y cerca en tiempo**. Si A está cerca de B y B está cerca de C, los tres son el mismo incendio aunque A y C queden lejos: así un incendio que avanza se sigue como uno solo.

| Parámetro | Valor inicial | Justificación |
| --- | --- | --- |
| `DISTANCIA_MAXIMA_M` | 1,000 m | Un píxel de MODIS mide 1 km: dos detecciones del mismo fuego pueden quedar separadas hasta esa distancia |
| `VENTANA_HORAS` | 48 h | Tres de cada cuatro incendios registrados por CONAFOR duran 1 día o menos; 48 horas dan margen para que el satélite vuelva a pasar sobre un incendio que sigue activo |

Los dos valores son **iniciales** y se calibran en OP1 comparando los candidatos con los registros de CONAFOR.

### Cómo se calcula

Se usa **DBSCAN** (de scikit-learn), un algoritmo que junta puntos que están a menos de cierta distancia entre sí. Como DBSCAN solo sabe medir una distancia, el tiempo se convierte a “metros”: con los valores de arriba, 48 horas pesan lo mismo que 1,000 metros. Las posiciones se usan en metros (EPSG:32613).

Consecuencia que hay que saber explicar: la distancia y el tiempo **se combinan**. Dos puntos a 1,000 m se juntan solo si son casi simultáneos; dos puntos en el mismo lugar se juntan si los separan hasta 48 horas; dos puntos a 700 m y 34 horas ya quedan en el límite.

Se usa `min_samples = 1`: **un punto solo también es un candidato**. No se descarta, porque un incendio pequeño real puede verse una sola vez.

### Problemas que resuelve

| Problema | Cómo lo resuelve el agrupamiento |
| --- | --- |
| Un incendio produce muchos puntos | Se cuentan como un solo candidato |
| Agrupar solo por distancia fusionaba incendios de días distintos en el mismo lugar (P10) | El tiempo entra en la regla: el mismo lugar un mes después es otro candidato |
| Descartar puntos de baja confianza borraba incendios pequeños (P11) | No se descarta nada al agrupar; la confianza queda como variable |

### Cómo se comprobó

`pruebas/probar_agrupamiento.py` arma seis puntos a mano y comprueba que: dos puntos cercanos son un incendio; dos incendios lejanos el mismo día no se mezclan; un incendio que dura tres días sigue siendo uno; y el mismo lugar un mes después es otro incendio.

### Resultado con los datos reales

De 44,662 puntos de calor salen **14,118 incendios candidatos** (7,029 en 2024 y 7,089 en 2025).

| Puntos de calor del candidato | Candidatos |
| --- | --- |
| 1 | 8,573 |
| 2 a 4 | 4,130 |
| 5 a 14 | 1,100 |
| 15 a 39 | 194 |
| 40 o más | 121 |

Seis de cada diez candidatos son un punto solo. El más grande tiene 799 puntos y duró siete días (abril de 2025, en la costa). En la región piloto hay 1,033 candidatos en 2024 y 1,183 en 2025.

CONAFOR registró 1,869 incendios en esos dos años. Que haya muchos más candidatos que incendios registrados es lo esperado: entre los candidatos hay quemas agrícolas, fuentes fijas e incendios que nadie documentó. Separarlos es justamente el trabajo del paso A.

## 3. Variables de cada incendio candidato

Cada candidato se describe con estas variables (`datos/procesados/incendios_variables.csv`).

### Calculadas con los puntos de calor

| Variable | Qué significa | Cómo se calcula |
| --- | --- | --- |
| `n_puntos` | Tamaño aparente | Número de puntos de calor del candidato |
| `n_pasadas` | Persistencia: cuántas veces lo vio un satélite | Detecciones del mismo satélite con menos de 30 minutos de diferencia cuentan como una pasada |
| `duracion_horas` | Cuánto duró | Horas entre la primera y la última detección |
| `frp_max` | Intensidad del punto más fuerte (MW) | Máximo de la potencia radiativa de sus puntos |
| `frp_total` | Intensidad acumulada (MW) | Suma de la potencia radiativa de sus puntos |
| `confianza_media` | Qué tan seguro está el satélite | Promedio de la confianza (de 0 a 1) |
| `fraccion_nocturna` | Parte de las detecciones hechas de noche | De 0 (todo de día) a 1 (todo de noche) |
| `fuente_fija` | El lugar emite calor casi todo el año (industria, ladrilleras) | 1 si al menos la mitad de sus puntos son de tipo “fuente fija” según FIRMS, **o** si en su cuadro de 1 km hubo puntos de calor en 6 o más meses distintos del año |

¿Por qué 30 minutos para una pasada? Cada satélite tarda cerca de 100 minutos en dar una vuelta a la Tierra, así que no puede ver dos veces el mismo lugar en media hora.

¿Por qué 6 meses para una fuente fija? El 88 % de los puntos de calor cae de marzo a junio. Un lugar con calor en seis meses o más no sigue la temporada de incendios.

### Calculadas con fuentes externas

| Variable | Qué significa | Fuente | Estado |
| --- | --- | --- | --- |
| `dist_localidad_km`, `poblacion_localidad`, `nombre_localidad` | La localidad más cercana con al menos 100 habitantes | INEGI, localidades con población del Censo 2020 | ✅ Calculada |
| `en_piloto` | El centro del candidato cae en la región piloto | Caja de la región piloto | ✅ Calculada |
| `es_forestal` | Vegetación forestal o terreno agrícola o urbano | Uso de suelo y vegetación (INEGI, Serie VII), publicado en IDEFOR | ⏳ Pendiente |
| `en_area_protegida` | Dentro de un área natural protegida | Áreas naturales protegidas publicadas en IDEFOR | ⏳ Pendiente |
| `viento_kmh`, `humedad_pct`, `temperatura_c` | Clima del día | Open-Meteo | ⏳ Sprint 2 |

**Por qué faltan dos variables:** el servidor de mapas de IDEFOR (CONAFOR) dejó de responder la noche del 12 de noviembre, justo al preparar esta entrega. Los incendios de CONAFOR ya estaban descargados, pero las capas de vegetación y de áreas protegidas no. Se agregan en cuanto el servidor vuelva; si no vuelve, se aplica el plan B (cobertura de OpenStreetMap para la vegetación y solo áreas protegidas federales).

¿Por qué solo localidades de 100 habitantes o más? Jalisco tiene 10,332 localidades con habitantes y la mitad tiene 14 o menos (ranchos). Sin un mínimo, casi cualquier candidato quedaría “cerca de una localidad”. El valor es inicial.

### Primeros números

| Dato | Candidatos | % de 14,118 |
| --- | --- | --- |
| Vistos en una sola pasada | 11,397 | 80.7 % |
| Vistos en 2 o más pasadas | 2,721 | 19.3 % |
| Con duración mayor a 24 horas | 710 | 5.0 % |
| Con `frp_max` de 10 MW o más | 6,114 | 43.3 % |
| Con `frp_max` de 30 MW o más | 2,093 | 14.8 % |
| Con `frp_max` de 100 MW o más | 412 | 2.9 % |
| Marcados como fuente fija | 312 | 2.2 % |
| A menos de 2 km de una localidad de 100 habitantes o más | 5,148 | 36.5 % |

De las 312 fuentes fijas, 200 están en la región piloto. Los dos lugares que más se repiten están al sur del Área Metropolitana de Guadalajara (cerca de Las Pintas) y en el sur del estado (cerca de El Rincón). Falta confirmar qué hay en cada lugar; que emitan calor casi todo el año apunta a una instalación y no a un incendio forestal.

## 4. Observaciones para las reglas (se deciden en la versión 2)

1. **La persistencia separa bastante.** Solo uno de cada cinco candidatos se ve en dos o más pasadas. Es una cifra cercana en orden de magnitud a los 1,869 incendios registrados, lo que apoya usar `n_pasadas >= 2` como señal de incendio real. Falta comprobarlo contra CONAFOR.
2. **El umbral de 10 MW es poco exigente.** Lo supera el 43 % de los candidatos. La regla “forestal y `frp_max >= 10`” puede dejar pasar demasiadas falsas alarmas; conviene probar un valor más alto.
3. **La regla de seguridad a 2 km afectaría a muchos.** El 36.5 % de los candidatos está a menos de 2 km de una localidad de 100 habitantes o más. Si todos subieran a nivel alto, el nivel dejaría de distinguir. Hay que revisar la distancia o el tamaño mínimo de la localidad.
4. **`fuente_fija` ya funciona con dos señales** (la etiqueta de FIRMS y la repetición por meses) y coinciden en 176 candidatos.

## 5. Limitaciones

- **El agrupamiento puede unir incendios vecinos** que arden a menos de 1 km el mismo día, y **puede partir un incendio** si el satélite deja de verlo más de 48 horas (por nubes o humo).
- **El centro del candidato es el promedio de sus puntos.** En incendios muy extensos, ese centro puede quedar lejos de donde está el fuego activo.
- **La distancia a la localidad se mide al punto que el INEGI da como ubicación de la localidad**, no al borde de la zona habitada. En ciudades grandes la distancia real al borde es menor.
- **Faltan `es_forestal` y `en_area_protegida`**, por la caída del servidor de IDEFOR.
- **Los valores de los parámetros son iniciales.** No se han calibrado contra CONAFOR.
