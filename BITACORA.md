# Bitácora de avance

> Una entrada por semana (y extra cuando se tome una decisión importante). Sirve para mostrar el **proceso**, no solo el resultado, que es lo que pide el profesor.
> Plantilla al final.

---

## S0 · 12 – 18 oct 2026 · Fase F0 (Definición)

**Hecho**
- Actividad 03 completada en las Partes 4 a 6 y en el resultado final, conservando las Partes 1 a 3 como primeras versiones.
- Análisis crítico de la propuesta técnica generada con Gemini (`docs/02_…`).
- Arquitectura revisada, plan de evaluación, roadmap y backlog con criterios de aceptación.
- Estructura del repositorio preparada.

**Decisiones**
- El problema se redacta desde la situación de los coordinadores, no desde los algoritmos. Motivo: observación del profesor en la Actividad 03.
- Objetivo general centrado en una herramienta de apoyo a la decisión; la comparación de algoritmos pasa a ser un medio (OP2/OP4).
- Región piloto: Bosque La Primavera y su entorno en el AMG.
- Drones, propagación física y el LLM supervisor quedan fuera del núcleo (ver `docs/02`, sección 6).
- Arquitectura de pipeline + cron + web estática en lugar de un sistema multiagente orientado a eventos.

**Pendiente / bloqueos**
- Revisión cruzada con otro equipo (Parte 7). Los campos están marcados en rojo en el documento.
- Instalar Git y crear el repositorio en GitHub.
- Añadir referencias formales a las cifras del planteamiento.

**Próxima semana (S1):** F1-0, F1-1, F1-2, F1-3 y F1-4.

---

## S1 a S3 · 19 oct – 8 nov 2026

**Hecho**
- Sin avance técnico registrado: no se creó código ni se subió el repositorio a GitHub.
- La revisión cruzada (Parte 7 de la Actividad 03) no quedó registrada en el documento.

**Consecuencia**
- El plan de 8 semanas se comprime a 4 (ver S4).

---

## S4 · 9 – 15 nov 2026 · Replanificación y enfoque v2

**Decisiones (12 nov)**
- **Nuevo enfoque:** la herramienta **clasifica** los incendios con datos de fuentes externas y, con esa clasificación, **propone un plan de ataque** a las instituciones de protección.
- Clasificación en dos pasos: incendio real o falsa alarma, y nivel de severidad (bajo, medio, alto, crítico). Motivo: cada paso se puede validar contra los registros de CONAFOR.
- El plan de ataque incluye recursos según el nivel, orden de atención, asignación de brigadas (varias por incendio) y ruta al punto de acceso. Motivo: un incendio grave necesita más de una brigada; la versión 1 asignaba una sola.
- Cobertura mixta: clasificación en todo Jalisco; plan de ataque con rutas solo en la región piloto. Motivo: hay muchos más incendios para validar a escala estatal, sin el costo de calcular rutas en todo el estado.
- Fuentes nuevas: localidades, uso de suelo y vegetación, áreas protegidas y clima.
- Documentos actualizados: `docs/01` (versión 2, conserva la 1), `docs/03`, `docs/04`, `ROADMAP.md`, `BACKLOG.md`, `README.md` y `CLAUDE.md`.

**Pendiente / bloqueos**
- Instalar Python y completar el login de GitHub para crear el repositorio.
- **Confirmar antes del 15 nov qué campos traen los registros de CONAFOR** (coordenadas y superficie). Sin eso no hay etiquetas para entrenar ni validar.
- Informar al profesor del ajuste de enfoque.

**Próxima semana (S5):** F1-3 a F1-7 y F2-1 a F2-4.

### Jueves 12 nov · Revisión de fuentes de datos y primera entrega diaria

**Hecho**
- Se revisó en línea qué trae cada fuente de datos (tareas F1-3 y F1-4 del backlog, OP1). Solo se consultaron encabezados y muestras pequeñas; todavía no se descarga nada completo.
- Primera entrega diaria repartida por integrante: redirección de la raíz (`index.html`), `requirements.txt`, `.gitignore`, `scripts/config.py` v1 y `web/index.html` + `web/css/estilos.css` v1 (mapa de Jalisco con la región piloto y el menú).
- Entorno: Python 3.12.10 ya estaba instalado en la computadora de desarrollo. Se instalaron las librerías de `requirements.txt` con pip y se comprobó que funcionan (conversión de coordenadas a EPSG:32613, DBSCAN, bosque aleatorio, algoritmo húngaro y Dijkstra con datos de juguete).

**Qué trae cada fuente (comprobado el 12 nov 2026)**

| Fuente | Resultado | Plan B |
| --- | --- | --- |
| F2 · CONAFOR | **Disponible y mejor de lo esperado.** El “Concentrado Nacional de Polígonos de Incendios Forestales” está publicado en IDEFOR (idefor.cnf.gob.mx) para 2024 y 2025. Cada registro trae el **polígono quemado** (EPSG:4326), fecha de inicio (`FECHAINIC`), fecha de liquidación (`FECHALIQ`), superficie (`AREA_HA`), municipio, causa, tipo de vegetación (`TIPVEG`), área natural protegida (`ANP`) y tipo de impacto. Jalisco: **950 registros en 2024 y 919 en 2025**. | **No se activa.** Ya no hace falta emparejar por municipio ni usar el área quemada MODIS. |
| F1 · NASA FIRMS | **Disponible sin clave.** Existen los archivos anuales de México 2024 y 2025 para VIIRS S-NPP (unos 26 y 22 MB) y MODIS (unos 6 y 5 MB). Columnas: latitud, longitud, fecha, hora, satélite, confianza, FRP, día/noche y `type` (tipo de fuente). La confianza de VIIRS viene como letra (l, n, h) y la de MODIS como número de 0 a 100: hay que normalizarla. | No se necesita. La `MAP_KEY` solo haría falta para el modo en vivo (opcional). |
| F6 · Clima (Open-Meteo) | El servicio de histórico respondió a una consulta de prueba (temperatura, humedad mínima y viento de un día de 2025) sin clave. Uso no comercial gratuito con límite diario de consultas. | Pendiente de decidir cuántas consultas se harán (una por celda y día). |
| F5 · Áreas protegidas | IDEFOR publica una capa de áreas naturales protegidas 2024. Falta revisar su contenido y si incluye las estatales. | Solo federales. |
| F3 y F4 · INEGI (localidades y vegetación) | Pendiente de revisar (viernes 13). | — |
| F8 · Bases de brigadas | En IDEFOR solo hay capas de brigadas y campamentos de la Megalópolis (centro del país), no de Jalisco. | Probable: bases hipotéticas documentadas como supuesto. |

**Decisiones**
- Las etiquetas de la clasificación saldrán de los polígonos de CONAFOR en IDEFOR. Motivo: traen ubicación, fechas y superficie, que es justo lo que piden los pasos A y B.
- FIRMS se descargará de los archivos anuales por país, sin clave. Motivo: es más simple y no depende de la `MAP_KEY`.
- Sensores: VIIRS S-NPP y MODIS. Los archivos anuales por país de NOAA-20 y NOAA-21 no existen.
- Cada integrante sube sus archivos desde la página de GitHub, arrastrándolos (*Add file → Upload files*), en lugar de usar comandos de Git. Motivo: nadie tiene que instalar ni aprender Git para subir su parte. Johan mantiene la copia local con `git pull`.

- **Nuevo calendario:** el jueves 19 de noviembre el proyecto se presenta como sprint, con el 70 % terminado, y el jueves 26 de noviembre es la entrega final. Las cinco fases se reorganizan en dos sprints (`BACKLOG.md` y `ROADMAP.md`, versión 3). Sprint 1: datos, clasificación por reglas y plan de ataque (73 de 105 puntos). Sprint 2: evaluación, bosque aleatorio, clima y cierre (32 puntos). Motivo: para el 70 % conviene mostrar las dos funciones de la herramienta funcionando de punta a punta; la evaluación se hace después sobre algo que ya existe.
- **Repositorio y tablero:** se creó el repositorio público `Souls-Nao/vigia-jalisco` y un tablero de GitHub Projects con la misma estructura que el del proyecto de Huffman (columnas Backlog, Por hacer, En progreso, En revision y Terminado; campos Sprint, Puntos y OP). Cada tarea del backlog es una tarjeta: 43 en total.
- Los puntos de cada tarea son una estimación del equipo (1, 2, 3 o 5); sirven para medir el 70 %, no son una medida exacta.

**Observaciones para no olvidar**
- Las cifras del planteamiento (912 incendios en Jalisco y 9,996 en el país en 2025) **no coinciden exactamente** con la capa de polígonos de 2025 (919 en Jalisco y 7,002 en el país). Puede deberse a que son productos distintos o a cortes de fecha distintos. Hay que aclararlo al poner las referencias formales.
- Con `FECHAINIC` y `FECHALIQ` se puede ajustar la tolerancia de días del cruce con CONAFOR usando la duración real de cada incendio (se decide en OP1).

**Pendiente / bloqueos**
- Activar GitHub Pages e invitar a los colaboradores al repositorio.

---

### Viernes 13 a domingo 15 nov · Datos reales, clasificación por reglas y mapa (Sprint 1)

**Hecho**
- Scripts 01 a 05 y 07 corridos con datos reales: 44,662 puntos de calor → 14,118 incendios candidatos → variables → etiquetas → clasificación por reglas → archivos del sitio.
- Sitio: menú compartido, página “Acerca de” y mapa con selector de año y día, filtro por nivel y ficha con las razones de cada clasificación.
- Documentos: `reportes/analisis_datos.md` versión 2 (entregable de OP1) y `docs/05_modelo_de_decision.md` versión 1.
- Pruebas con `assert`: agrupamiento (7 comprobaciones) y clasificación (15 casos).

**Decisiones (qué y por qué)**
- **Tolerancia del cruce con CONAFOR: 1 km y 2 días** (el valor inicial era 3 km y 3 días). Motivo: con 2024, casi todas las coincidencias están dentro del polígono o a menos de 1 km; más lejos, y a 3 días o más, las coincidencias se reparten como si fueran casualidad.
- **Niveles reales: menos de 30 ha, 30 a 100, 100 a 600 y 600 o más.** Motivo: son los cuartiles (redondeados) de la superficie de los incendios de 2024 que sí detecta el satélite. Los cuartiles de todos los registros (3, 15 y 61 ha) no servían: los incendios que ve el satélite son mucho más grandes.
- **Regla del paso A ajustada con 2024:** fuente fija → falsa alarma; terreno forestal y 2 o más pasadas → real; 15 o más puntos de calor → real; lo demás → falsa alarma. Motivo: la regla de partida (2 pasadas, o forestal con 10 MW) llamaba reales a 2,230 candidatos con precisión de 0.21; la intensidad sola separa poco.
- **Puntaje del paso B:** se agrega “a 4 km o más de la localidad más cercana: +1” y los niveles pasan a 0, 1-2, 3-4 y 5 o más. Motivo: en 2024 los incendios lejos de poblaciones fueron mucho más grandes (837 ha a más de 8 km contra 38 ha a menos de 2 km); con el cambio, los críticos clasificados como bajos bajaron de 67 a 15.
- **Regla de seguridad a 1 km** (el valor inicial era 2 km). Motivo: a menos de 2 km está el 20 % de los incendios reales; a menos de 1 km, el 5 %. **Confirmada por el equipo el 13 de noviembre.**
- **Vegetación y áreas protegidas se descargan del geoportal de CONABIO**, no de IDEFOR. Motivo: el servidor de mapas de IDEFOR dejó de responder el 12 y 13 de noviembre. La capa de vegetación es la misma (INEGI, Serie VII). Las áreas protegidas son **solo las federales** (plan B previsto).
- **Dos scripts nuevos fuera de la lista original:** `02b_fuentes_complementarias.py` (descargas de localidades, vegetación y áreas protegidas) y `04b_etiquetar.py` (cruce con CONAFOR). Motivo: dejarlos dentro de los scripts 04 y 05 los hacía demasiado largos para explicarlos.
- **La IA ya no hace ningún cambio en GitHub**: solo deja archivos en las carpetas diarias y el equipo los sube.

**Métricas / evidencia**
- Cruce: 690 candidatos de 2024 y 542 de 2025 coinciden con CONAFOR. El satélite ve cerca de la mitad de los incendios registrados (463 de 950 y 418 de 919).
- Paso A, 2025 (año de prueba): precisión 0.33, sensibilidad 0.43 y F1 0.37. La regla de partida daba F1 0.30.
- Paso B, 2025: mismo nivel en 0.49 de los casos; mismo nivel o uno de diferencia en 0.93; 2 de 47 críticos clasificados como bajos.
- Quedan clasificados como reales 986 incendios en 2024 y 693 en 2025; en la región piloto, 53 y 42.

**Pendiente / bloqueos**
- **Los números de la clasificación son bajos** y hay que saber explicarlo: parte es ruido de las etiquetas (CONAFOR no registra todo y el satélite no ve todo). El bosque aleatorio del Sprint 2 es la comparación que falta.
- Confirmar en equipo los niveles reales (30, 100 y 600 ha).
- Áreas protegidas estatales, si IDEFOR vuelve.
- Activar GitHub Pages e invitar a los colaboradores.
- Referencias formales de las cifras del planteamiento.

**Próximos días (Sprint 1):** lunes 16, página “Probar”, bases y rutas de la región piloto, y `plan.js` con voraz y más cercana; martes 17, húngaro y página “Plan de ataque”; miércoles 18, revisión completa y presentación.

---

<!-- PLANTILLA
## S# · fechas · Fase F#

**Hecho** (con enlace a PR/issue)
-

**Decisiones** (qué y por qué)
-

**Métricas / evidencia**
-

**Pendiente / bloqueos**
-

**Próxima semana:**
-->
