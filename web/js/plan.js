/*
  plan.js · Plan de ataque: reparto de brigadas entre incendios (versión 1)
  Qué hace:  1) calcula cuántos recursos pide cada incendio según su nivel (demanda),
             2) decide en qué orden atenderlos y
             3) reparte las brigadas disponibles con el método elegido:
                  "voraz"   · recorre los incendios en orden y da a cada uno sus brigadas más rápidas
                  "cercana" · una brigada por incendio, la más cercana en línea recta (referencia)
                El método "hungaro" llega en la versión 2.
  Qué recibe: listas y diccionarios ya cargados (incendios, brigadas, bases, tiempos y reglas).
             No lee archivos ni toca la página: así se puede probar por separado.
  Cómo se prueba: abrir la consola del navegador en una página que cargue este archivo y
             escribir probarPlan(). Debe responder "Todas las pruebas del plan pasaron".
*/

// ---------------------------------------------------------------------------
// 1. Demanda: qué pide cada incendio
// ---------------------------------------------------------------------------

// Devuelve lo que pide un incendio según la tabla de respuesta: {brigadas, motobomba, apoyo_aereo}.
function demandaDe(incendio, reglas) {
  return reglas.tabla_respuesta[incendio.nivel];
}

// ---------------------------------------------------------------------------
// 2. Tiempos y distancias
// ---------------------------------------------------------------------------

// Minutos que tarda una base en llegar por camino a un incendio. Si no hay camino, Infinity.
function minutosDesde(tiempos, incendioId, baseId) {
  var deEseIncendio = tiempos[incendioId] || {};
  var minutos = deEseIncendio[baseId];
  return minutos === undefined ? Infinity : minutos;
}

// Minutos de la base que llega más rápido a un incendio.
function llegadaMasRapida(tiempos, incendioId) {
  var mejor = Infinity;
  Object.keys(tiempos[incendioId] || {}).forEach(function (baseId) {
    mejor = Math.min(mejor, tiempos[incendioId][baseId]);
  });
  return mejor;
}

// Distancia en línea recta entre dos lugares, en kilómetros (fórmula del haversine).
function distanciaEnLineaRecta(lat1, lon1, lat2, lon2) {
  var aRadianes = Math.PI / 180;
  var dLat = (lat2 - lat1) * aRadianes;
  var dLon = (lon2 - lon1) * aRadianes;
  var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
          Math.cos(lat1 * aRadianes) * Math.cos(lat2 * aRadianes) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  return 6371 * 2 * Math.asin(Math.sqrt(a));     // 6371 km es el radio de la Tierra
}

// ---------------------------------------------------------------------------
// 3. Orden de atención
// ---------------------------------------------------------------------------

// Ordena los incendios: primero el nivel más grave; a igual nivel, el que se alcanza más rápido.
function ordenDeAtencion(incendios, tiempos, reglas) {
  var copia = incendios.slice();          // se ordena una copia para no cambiar la lista original
  copia.sort(function (a, b) {
    var diferencia = reglas.niveles.indexOf(b.nivel) - reglas.niveles.indexOf(a.nivel);
    if (diferencia !== 0) { return diferencia; }
    return llegadaMasRapida(tiempos, a.id) - llegadaMasRapida(tiempos, b.id);
  });
  return copia;
}

// ---------------------------------------------------------------------------
// 4. Reparto
// ---------------------------------------------------------------------------

// Saca de la lista de libres la brigada que llega más rápido a un incendio y la devuelve.
// Si ninguna puede llegar, devuelve null.
function tomarLaMasRapida(libres, tiempos, incendioId) {
  var mejor = -1;
  libres.forEach(function (brigada, posicion) {
    var minutos = minutosDesde(tiempos, incendioId, brigada.base);
    if (minutos < Infinity && (mejor === -1 || minutos < minutosDesde(tiempos, incendioId, libres[mejor].base))) {
      mejor = posicion;
    }
  });
  return mejor === -1 ? null : libres.splice(mejor, 1)[0];
}

// Arma el renglón de una asignación: qué brigada va a qué incendio y cuánto tarda.
function nuevaAsignacion(brigada, incendio, tiempos) {
  return { brigada: brigada.id, base: brigada.base, tipo: brigada.tipo, incendio: incendio.id,
           minutos: minutosDesde(tiempos, incendio.id, brigada.base) };
}

// Método voraz: en el orden de atención, cada incendio toma las brigadas libres más rápidas.
// Devuelve cuántas brigadas le faltaron a cada incendio: {idDelIncendio: faltantes}.
function repartirVoraz(enOrden, libres, tiempos, reglas, asignaciones) {
  var faltantes = {};
  enOrden.forEach(function (incendio) {
    var pedidas = demandaDe(incendio, reglas).brigadas;
    var dadas = 0;
    while (dadas < pedidas) {
      var brigada = tomarLaMasRapida(libres, tiempos, incendio.id);
      if (brigada === null) { break; }
      asignaciones.push(nuevaAsignacion(brigada, incendio, tiempos));
      dadas += 1;
    }
    faltantes[incendio.id] = pedidas - dadas;
  });
  return faltantes;
}

// Saca de la lista de libres la brigada cuya base queda más cerca en línea recta de un incendio.
function tomarLaMasCercana(libres, bases, incendio) {
  var mejor = -1;
  var mejorKm = Infinity;
  libres.forEach(function (brigada, posicion) {
    var base = bases[brigada.base];
    var km = distanciaEnLineaRecta(base.lat, base.lon, incendio.lat, incendio.lon);
    if (km < mejorKm) { mejor = posicion; mejorKm = km; }
  });
  return mejor === -1 ? null : libres.splice(mejor, 1)[0];
}

// Método de referencia: UNA brigada por incendio, en el orden en que se detectaron, eligiendo
// la base más cercana en línea recta (sin mirar los caminos ni el nivel).
function repartirMasCercana(incendios, libres, bases, tiempos, reglas, asignaciones) {
  var faltantes = {};
  var porDeteccion = incendios.slice().sort(function (a, b) { return a.inicio < b.inicio ? -1 : 1; });
  porDeteccion.forEach(function (incendio) {
    var pedidas = demandaDe(incendio, reglas).brigadas;
    var brigada = tomarLaMasCercana(libres, bases, incendio);
    if (brigada !== null) { asignaciones.push(nuevaAsignacion(brigada, incendio, tiempos)); }
    faltantes[incendio.id] = pedidas - (brigada === null ? 0 : 1);
  });
  return faltantes;
}

// Reparte las unidades con motobomba: en el orden de atención, cada incendio que la pide
// recibe la unidad libre que llega más rápido. Devuelve los incendios que se quedaron sin ella.
function repartirMotobombas(enOrden, libres, tiempos, reglas, asignaciones) {
  var sinMotobomba = [];
  enOrden.forEach(function (incendio) {
    if (!demandaDe(incendio, reglas).motobomba) { return; }
    var unidad = tomarLaMasRapida(libres, tiempos, incendio.id);
    if (unidad === null) { sinMotobomba.push(incendio.id); return; }
    asignaciones.push(nuevaAsignacion(unidad, incendio, tiempos));
  });
  return sinMotobomba;
}

// ---------------------------------------------------------------------------
// 5. Plan completo
// ---------------------------------------------------------------------------

// Genera el plan de ataque con el método indicado ("voraz" o "cercana").
//   incendios: [{id, nivel, inicio, lat, lon}]      brigadas: [{id, base, tipo}] (solo las disponibles)
//   bases: {idDeBase: {lat, lon}}                   tiempos: {idDeIncendio: {idDeBase: minutos}}
//   reglas: lo que trae datos/reglas.json (niveles, tabla_respuesta, peso_nivel)
function generarPlan(incendios, brigadas, bases, tiempos, reglas, metodo) {
  var terrestres = brigadas.filter(function (b) { return b.tipo === "terrestre"; });
  var motobombas = brigadas.filter(function (b) { return b.tipo === "motobomba"; });
  var enOrden = ordenDeAtencion(incendios, tiempos, reglas);
  var asignaciones = [];
  var faltantes;
  if (metodo === "voraz") {
    faltantes = repartirVoraz(enOrden, terrestres, tiempos, reglas, asignaciones);
  } else if (metodo === "cercana") {
    faltantes = repartirMasCercana(incendios, terrestres, bases, tiempos, reglas, asignaciones);
  } else {
    throw new Error('El método "' + metodo + '" todavía no existe. Usa "voraz" o "cercana".');
  }
  var sinMotobomba = repartirMotobombas(enOrden, motobombas, tiempos, reglas, asignaciones);
  return {
    metodo: metodo,
    orden: enOrden.map(function (incendio) { return incendio.id; }),
    asignaciones: asignaciones,
    // Lo que no se pudo cubrir: brigadas que faltaron y unidades con motobomba que faltaron.
    brigadas_faltantes: faltantes,
    sin_motobomba: sinMotobomba,
    // La herramienta solo RECOMIENDA pedir apoyo aéreo; no lo asigna ni lo solicita.
    recomendar_apoyo_aereo: enOrden.filter(function (incendio) {
      return demandaDe(incendio, reglas).apoyo_aereo;
    }).map(function (incendio) { return incendio.id; })
  };
}

// ---------------------------------------------------------------------------
// 6. Prueba con un caso pequeño calculado a mano
// ---------------------------------------------------------------------------

// El mismo caso está en pruebas/probar_plan.py. Si se cambia aquí, hay que cambiarlo allá.
function casoDePrueba() {
  return {
    reglas: {
      niveles: ["bajo", "medio", "alto", "critico"],
      tabla_respuesta: {
        bajo: { brigadas: 1, motobomba: false, apoyo_aereo: false },
        medio: { brigadas: 2, motobomba: false, apoyo_aereo: false },
        alto: { brigadas: 3, motobomba: true, apoyo_aereo: false },
        critico: { brigadas: 4, motobomba: true, apoyo_aereo: true }
      }
    },
    bases: { B1: { lat: 20.0, lon: -103.0 }, B2: { lat: 20.0, lon: -103.5 } },
    brigadas: [
      { id: "BR1", base: "B1", tipo: "terrestre" }, { id: "BR2", base: "B1", tipo: "terrestre" },
      { id: "BR3", base: "B2", tipo: "terrestre" }, { id: "BR4", base: "B2", tipo: "terrestre" }
    ],
    // I3 se detectó primero; I1 y I2 son de nivel medio (piden 2 brigadas) e I3 es bajo (pide 1).
    incendios: [
      { id: "I1", nivel: "medio", inicio: "2025-04-15T12:00", lat: 20.0, lon: -103.2 },
      { id: "I2", nivel: "medio", inicio: "2025-04-15T13:00", lat: 20.0, lon: -103.3 },
      { id: "I3", nivel: "bajo", inicio: "2025-04-15T11:00", lat: 20.0, lon: -103.1 }
    ],
    // Desde B2, el camino a I2 es muy lento (40 min) aunque en línea recta quede cerca.
    tiempos: { I1: { B1: 10, B2: 12 }, I2: { B1: 11, B2: 40 }, I3: { B1: 5, B2: 6 } }
  };
}

// Convierte las asignaciones en textos como "BR1>I1:10" para compararlas fácil.
function resumenDeAsignaciones(plan) {
  return plan.asignaciones.map(function (a) { return a.brigada + ">" + a.incendio + ":" + a.minutos; }).join(" ");
}

// Revisa que una condición se cumpla; si no, avisa cuál falló.
function comprobar(condicion, mensaje) {
  if (!condicion) { throw new Error("Falló la prueba: " + mensaje); }
}

// Corre el caso de prueba con los dos métodos y compara contra el resultado calculado a mano.
function probarPlan() {
  var c = casoDePrueba();
  // Orden de atención: los dos medios primero (I1 se alcanza en 10 min, I2 en 11) y luego el bajo.
  comprobar(ordenDeAtencion(c.incendios, c.tiempos, c.reglas).map(function (i) { return i.id; }).join(",") === "I1,I2,I3",
            "orden de atención");
  // Voraz: I1 toma las dos brigadas de B1 (10 min); a I2 le quedan las de B2 (40 min); I3 se queda sin brigada.
  var voraz = generarPlan(c.incendios, c.brigadas, c.bases, c.tiempos, c.reglas, "voraz");
  comprobar(resumenDeAsignaciones(voraz) === "BR1>I1:10 BR2>I1:10 BR3>I2:40 BR4>I2:40", "reparto voraz");
  comprobar(voraz.brigadas_faltantes.I3 === 1 && voraz.brigadas_faltantes.I1 === 0, "faltantes del voraz");
  // Más cercana: por orden de detección (I3, I1, I2), una brigada cada uno, por línea recta:
  // I3 y I1 quedan más cerca de B1; I2 queda más cerca de B2, aunque por camino tarde 40 min.
  var cercana = generarPlan(c.incendios, c.brigadas, c.bases, c.tiempos, c.reglas, "cercana");
  comprobar(resumenDeAsignaciones(cercana) === "BR1>I3:5 BR2>I1:10 BR3>I2:40", "reparto de la más cercana");
  comprobar(cercana.brigadas_faltantes.I1 === 1 && cercana.brigadas_faltantes.I2 === 1 &&
            cercana.brigadas_faltantes.I3 === 0, "faltantes de la más cercana");
  return "Todas las pruebas del plan pasaron";
}
