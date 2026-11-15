/*
  mapa.js · Código de la página "Mapa de incendios" (versión 2)
  Qué hace:  crea el mapa de Jalisco, lee los incendios clasificados de un año y pinta los del
             día elegido, con el color de su nivel. Permite cambiar de año y de día, y apagar
             o prender niveles. Al hacer clic en un incendio aparece su ficha con las razones.
  Qué lee:   datos/incendios_2024.json y datos/incendios_2025.json (los escribe el script 07).
  Qué usa:   Leaflet y js/comun.js (colores, nombres de nivel y carga de JSON).
  Cómo se prueba: abrir el sitio publicado, elegir un día y hacer clic en un círculo.
*/

// Esquinas de las dos regiones: [latitud, longitud] del suroeste y del noreste.
// Son los mismos números que están en scripts/config.py.
var CAJA_JALISCO = [[18.87, -105.75], [22.80, -101.45]];
var CAJA_PILOTO = [[20.40, -103.90], [20.95, -103.15]];

// Lo que la página recuerda mientras está abierta.
var mapa = null;               // el mapa de Leaflet
var capaIncendios = null;      // grupo con los círculos que están pintados
var incendiosDelAnio = [];     // todos los incendios del año que está cargado

// ---------------------------------------------------------------------------
// 1. Mapa
// ---------------------------------------------------------------------------

// Crea el mapa con el fondo de OpenStreetMap y el rectángulo de la región piloto.
function crearMapa() {
  mapa = L.map("mapa");
  mapa.fitBounds(CAJA_JALISCO);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; colaboradores de OpenStreetMap"
  }).addTo(mapa);
  // interactive: false para que el rectángulo no estorbe al hacer clic en los incendios.
  L.rectangle(CAJA_PILOTO, {
    color: "#1d5c4b", weight: 2, dashArray: "6 6", fillOpacity: 0.05, interactive: false
  }).addTo(mapa);
  capaIncendios = L.layerGroup().addTo(mapa);
}

// ---------------------------------------------------------------------------
// 2. Fechas
// ---------------------------------------------------------------------------

// Escribe un día como "15 de mayo de 2025". Recibe el texto "2025-05-15".
function diaEnPalabras(dia) {
  var fecha = new Date(dia + "T12:00:00");
  return fecha.toLocaleDateString("es-MX", { day: "numeric", month: "long", year: "numeric" });
}

// Devuelve el día que está "cuantos" días después (o antes, si es negativo).
function sumarDias(dia, cuantos) {
  var fecha = new Date(dia + "T12:00:00");
  fecha.setDate(fecha.getDate() + cuantos);
  return fecha.toISOString().slice(0, 10);
}

// Busca el día en que empezaron más incendios reales, para abrir el mapa en un día interesante.
function diaConMasIncendios() {
  var cuentas = {};
  var mejorDia = null;
  incendiosDelAnio.forEach(function (incendio) {
    if (!incendio.es_real) { return; }
    var dia = incendio.inicio.slice(0, 10);
    cuentas[dia] = (cuentas[dia] || 0) + 1;
    if (mejorDia === null || cuentas[dia] > cuentas[mejorDia]) {
      mejorDia = dia;
    }
  });
  return mejorDia;
}

// ---------------------------------------------------------------------------
// 3. Qué incendios se muestran
// ---------------------------------------------------------------------------

// Devuelve la lista de niveles que están marcados en las casillas ("bajo", "falsa", ...).
function nivelesMarcados() {
  var marcados = [];
  document.querySelectorAll("#filtros input").forEach(function (casilla) {
    if (casilla.checked) { marcados.push(casilla.value); }
  });
  return marcados;
}

// Devuelve los incendios que estaban activos ese día y cuyo nivel está marcado.
function incendiosVisibles(dia) {
  var niveles = nivelesMarcados();
  return incendiosDelAnio.filter(function (incendio) {
    // Activo ese día: empezó ese día o antes, y terminó ese día o después.
    // Las fechas van como texto "2025-05-15T14:30", así que se pueden comparar como texto.
    var activo = incendio.inicio.slice(0, 10) <= dia && incendio.fin.slice(0, 10) >= dia;
    return activo && niveles.indexOf(nivelParaPintar(incendio)) !== -1;
  });
}

// ---------------------------------------------------------------------------
// 4. Ficha de un incendio
// ---------------------------------------------------------------------------

// Agrega un renglón de texto a la ficha. Si "fuerte" es true, va en negritas.
function agregarRenglon(ficha, texto, fuerte) {
  var renglon = document.createElement(fuerte ? "strong" : "div");
  renglon.textContent = texto;
  ficha.appendChild(renglon);
}

// Dice en palabras si el incendio coincide con un registro de CONAFOR.
function textoConafor(incendio) {
  if (incendio.conafor.coincide) {
    return "Coincide con un incendio registrado por CONAFOR: " + incendio.conafor.superficie_ha + " ha";
  }
  return "Sin registro de CONAFOR que coincida";
}

// Arma la ficha que aparece al hacer clic en un incendio.
function crearFicha(incendio) {
  var ficha = document.createElement("div");
  ficha.className = "ficha";
  var titulo = incendio.es_real
    ? "Incendio real · nivel " + NOMBRES_NIVEL[incendio.nivel].toLowerCase()
    : "Probable falsa alarma";
  agregarRenglon(ficha, titulo, true);
  agregarRenglon(ficha, "Detectado del " + incendio.inicio.replace("T", " ") + " al " + incendio.fin.replace("T", " "));
  agregarRenglon(ficha, incendio.n_puntos + " puntos de calor · " + incendio.n_pasadas +
                        " pasadas · hasta " + incendio.frp_max + " MW");
  // Las razones explican por qué se clasificó así.
  var lista = document.createElement("ul");
  incendio.razones.forEach(function (razon) {
    var elemento = document.createElement("li");
    elemento.textContent = razon;
    lista.appendChild(elemento);
  });
  ficha.appendChild(lista);
  agregarRenglon(ficha, "De los casos parecidos de 2024, el " + Math.round(incendio.prob_real * 100) +
                        " % coincidió con un registro de CONAFOR.");
  agregarRenglon(ficha, textoConafor(incendio));
  agregarRenglon(ficha, "Identificador: " + incendio.id);
  return ficha;
}

// ---------------------------------------------------------------------------
// 5. Pintar
// ---------------------------------------------------------------------------

// Pinta un incendio como círculo. Las falsas alarmas van más chicas para que no tapen a los reales.
function pintarIncendio(incendio) {
  var circulo = L.circleMarker([incendio.lat, incendio.lon], {
    radius: incendio.es_real ? 8 : 5,
    color: "#333333",                     // borde oscuro para que resalte sobre el mapa
    weight: 1,
    fillColor: colorDeIncendio(incendio),
    fillOpacity: 0.85
  });
  circulo.bindPopup(crearFicha(incendio));
  circulo.addTo(capaIncendios);
}

// Borra los círculos y pinta los incendios del día que está elegido.
function pintarDia() {
  var dia = document.getElementById("fecha").value;
  capaIncendios.clearLayers();
  if (!dia) { return; }
  var visibles = incendiosVisibles(dia);
  // Primero las falsas alarmas y encima los reales.
  visibles.filter(function (incendio) { return !incendio.es_real; }).forEach(pintarIncendio);
  var reales = visibles.filter(function (incendio) { return incendio.es_real; });
  reales.forEach(pintarIncendio);
  mostrarAviso("estado-datos", diaEnPalabras(dia) + ": " + reales.length + " incendios reales y " +
               (visibles.length - reales.length) + " probables falsas alarmas a la vista.");
}

// Cambia el día elegido, sin salirse del año cargado, y vuelve a pintar.
function irAlDia(dia) {
  var campo = document.getElementById("fecha");
  if (dia < campo.min) { dia = campo.min; }
  if (dia > campo.max) { dia = campo.max; }
  campo.value = dia;
  pintarDia();
}

// ---------------------------------------------------------------------------
// 6. Cargar un año y conectar los controles
// ---------------------------------------------------------------------------

// Lee el archivo del año elegido y abre el mapa en el día con más incendios reales.
function cargarAnio() {
  var anio = document.getElementById("anio").value;
  mostrarAviso("estado-datos", "Cargando incendios de " + anio + "…");
  cargarJSON("datos/incendios_" + anio + ".json",
    function (datos) {
      incendiosDelAnio = datos.incendios;
      var campo = document.getElementById("fecha");
      campo.min = anio + "-01-01";
      campo.max = anio + "-12-31";
      irAlDia(diaConMasIncendios());
    },
    function (mensaje) {
      incendiosDelAnio = [];
      capaIncendios.clearLayers();
      mostrarAviso("estado-datos", mensaje);
    });
}

// Dice qué hace cada control cuando el usuario lo usa.
function conectarControles() {
  document.getElementById("anio").addEventListener("change", cargarAnio);
  document.getElementById("fecha").addEventListener("change", pintarDia);
  document.getElementById("dia-anterior").addEventListener("click", function () {
    irAlDia(sumarDias(document.getElementById("fecha").value, -1));
  });
  document.getElementById("dia-siguiente").addEventListener("click", function () {
    irAlDia(sumarDias(document.getElementById("fecha").value, 1));
  });
  document.getElementById("dia-mas-activo").addEventListener("click", function () {
    irAlDia(diaConMasIncendios());
  });
  document.querySelectorAll("#filtros input").forEach(function (casilla) {
    casilla.addEventListener("change", pintarDia);
  });
}

// Punto de partida de la página.
function iniciarPagina() {
  dibujarMenu();
  // Si Leaflet no se pudo bajar (sin internet), se avisa en vez de dejar el hueco en blanco.
  if (typeof L === "undefined") {
    mostrarAviso("estado-datos", "No se pudo cargar el mapa. Revisa tu conexión a internet y vuelve a abrir la página.");
    return;
  }
  crearMapa();
  conectarControles();
  cargarAnio();
}

iniciarPagina();
