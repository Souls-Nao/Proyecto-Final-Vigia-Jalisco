# Vigía Jalisco

**Herramienta web de apoyo a la decisión que clasifica los incendios forestales de Jalisco y propone un plan de ataque a las instituciones de protección.**
Seminario de Integración de Desarrollo · Equipo **Brigada Binaria**

- Castañeda Hernández Oswaldo Daniel
- Gutierrez Nava Johan Daniel
- Ruvalcaba Velazquez Omar Alejandro
- Soria Hernández Cuauhtémoc

---

## El problema (resumen)

Cuando hay varios incendios activos al mismo tiempo, los coordinadores reciben alertas satelitales en forma de **puntos de calor sueltos**: un incendio genera muchos puntos y hay falsas alarmas. Con eso deben decidir rápido cuáles son incendios reales, qué tan graves son, cuántos recursos necesita cada uno y en qué orden atenderlos. La detección ya existe (FIRMS, CONABIO, LANOT); lo que no está resuelto es el paso entre la alerta y el plan de ataque. → [Planteamiento completo](docs/01_planteamiento_y_objetivos.md)

## Qué hace la herramienta

1. **Clasifica** cada incendio en todo Jalisco con datos de FIRMS y fuentes públicas (localidades, vegetación, áreas protegidas, clima):
   - ¿Es un incendio **real** o una falsa alarma?
   - ¿Qué **nivel de severidad** tiene: bajo, medio, alto o crítico?
2. **Propone un plan de ataque** en la región piloto (Bosque La Primavera y AMG): recursos según el nivel, orden de atención, qué brigadas enviar y por qué ruta.

## Objetivo general (versión 2, 12 nov 2026)

Desarrollar una herramienta web de apoyo a la decisión que, a partir de los puntos de calor de NASA FIRMS y de información geográfica y meteorológica de fuentes públicas, clasifique los incendios de Jalisco según si son reales y su nivel de severidad, y proponga a las instituciones de protección un plan de ataque (recursos por nivel, orden de atención, asignación de brigadas y ruta de acceso) en la región piloto del Bosque La Primavera y el AMG, para reducir el tiempo de decisión y el tiempo estimado de llegada de los recursos cuando ocurren varios incendios simultáneos durante la temporada de estiaje.

| | Objetivo particular | Fase |
| --- | --- | --- |
| OP1 | Analizar los datos (FIRMS, CONAFOR, fuentes complementarias, red vial, bases) | F1 |
| OP2 | Diseñar los modelos de clasificación y de plan de ataque, con su evaluación | F2–F3 |
| OP3 | Implementar la aplicación web (clasificación estatal, plan en región piloto, simulación) | F2–F3 |
| OP4 | Evaluar contra los registros de CONAFOR y las estrategias de referencia | F4 |


## Estado

**Sprint actual:** Sprint 1 (12 – 19 nov 2026): datos, clasificación por reglas y plan de ataque, el 70 % del proyecto. Entrega final: 26 nov 2026. 


## Estructura del repositorio

```
vigia-jalisco/
├── index.html       Redirige al sitio (GitHub Pages)
├── docs/            Planteamiento, análisis, arquitectura, evaluación
├── entregables/     Documentos entregados al profesor
├── scripts/         Scripts de Python numerados (01 a 08) y config.py
├── pruebas/         Pruebas sencillas con assert
├── datos/           crudos/ (no se sube) · referencia/ · procesados/
├── reportes/        Análisis de datos y evaluación
├── web/             Sitio: páginas, estilos, JavaScript y datos JSON
├── ROADMAP.md · BACKLOG.md · BITACORA.md
```

## Aviso

Proyecto académico. **No sustituye a los sistemas oficiales** de CONAFOR, SEMADET ni Protección Civil, y no emite alertas. Ante un incendio, llama al **911**.
