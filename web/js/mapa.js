/*
  mapa.js · Código de la página "Mapa de incendios" (versión 1)
  Qué hace:  crea el mapa de Jalisco, marca la región piloto, lee un archivo de incendios y
             pinta cada incendio como un círculo del color de su nivel. Al hacer clic en un
             círculo aparece su ficha.
  Qué lee:   datos/incendios_ejemplo.json (incendios INVENTADOS, solo para probar el mapa).
  Qué usa:   Leaflet y js/comun.js (colores, nombres de nivel y carga de JSON).
  Cómo se prueba: abrir el sitio publicado; deben verse 8 círculos de colores sobre Jalisco.
*/

// Archivo que se pinta. En la versión 2 se cambia por los datos reales de cada año.
var ARCHIVO_INCENDIOS = "datos/incendios_ejemplo.json";

// Esquinas de las dos regiones: [latitud, longitud] del suroeste y del noreste.
// Son los mismos números que están en scripts/config.py.
var CAJA_JALISCO = [[18.87, -105.75], [22.80, -101.45]];
var CAJA_PILOTO = [[20.40, -103.90], [20.95, -103.15]];

// Crea el mapa con el fondo de OpenStreetMap y el rectángulo de la región piloto.
function crearMapa() {
  var mapa = L.map("mapa");
  mapa.fitBounds(CAJA_JALISCO);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; colaboradores de OpenStreetMap"
  }).addTo(mapa);
  // interactive: false para que el rectángulo no estorbe al hacer clic en los incendios.
  L.rectangle(CAJA_PILOTO, {
    color: "#1d5c4b", weight: 2, dashArray: "6 6", fillOpacity: 0.05, interactive: false
  }).addTo(mapa);
  return mapa;
}

// Agrega un renglón de texto a la ficha. Si "fuerte" es true, va en negritas.
function agregarRenglon(ficha, texto, fuerte) {
  var renglon = document.createElement(fuerte ? "strong" : "div");
  renglon.textContent = texto;
  ficha.appendChild(renglon);
}

// Arma la ficha que aparece al hacer clic en un incendio.
function crearFicha(incendio) {
  var ficha = document.createElement("div");
  ficha.className = "ficha";
  var titulo = incendio.es_real
    ? "Incendio real · nivel " + NOMBRES_NIVEL[incendio.nivel].toLowerCase()
    : "Probable falsa alarma";
  agregarRenglon(ficha, titulo, true);
  agregarRenglon(ficha, "Probabilidad de ser real: " + Math.round(incendio.prob_real * 100) + " %");
  agregarRenglon(ficha, "Inicio: " + incendio.inicio.replace("T", " "));
  agregarRenglon(ficha, "Puntos de calor: " + incendio.n_puntos + " · Pasadas: " + incendio.n_pasadas);
  // Las razones explican por qué se clasificó así.
  var lista = document.createElement("ul");
  incendio.razones.forEach(function (razon) {
    var elemento = document.createElement("li");
    elemento.textContent = razon;
    lista.appendChild(elemento);
  });
  ficha.appendChild(lista);
  return ficha;
}

// Pinta cada incendio como un círculo del color de su nivel (gris si es falsa alarma).
function pintarIncendios(mapa, incendios) {
  incendios.forEach(function (incendio) {
    var circulo = L.circleMarker([incendio.lat, incendio.lon], {
      radius: 8,
      color: "#333333",                     // borde oscuro para que resalte sobre el mapa
      weight: 1,
      fillColor: colorDeIncendio(incendio),
      fillOpacity: 0.85
    });
    circulo.bindPopup(crearFicha(incendio));
    circulo.addTo(mapa);
  });
}

// Lo que pasa cuando el archivo de incendios cargó bien.
function alCargarIncendios(mapa, datos) {
  pintarIncendios(mapa, datos.incendios);
  var mensaje = "Se muestran " + datos.incendios.length + " incendios.";
  // Si el archivo es de ejemplo, se avisa para que nadie lo confunda con datos reales.
  if (datos.ejemplo) {
    mensaje = "DATOS DE EJEMPLO: estos " + datos.incendios.length +
              " incendios son inventados para probar el mapa. Pronto se reemplazan por los reales.";
  }
  mostrarAviso("estado-datos", mensaje);
}

// Punto de partida de la página.
function iniciarPagina() {
  dibujarMenu();
  // Si Leaflet no se pudo bajar (sin internet), se avisa en vez de dejar el hueco en blanco.
  if (typeof L === "undefined") {
    mostrarAviso("estado-datos", "No se pudo cargar el mapa. Revisa tu conexión a internet y vuelve a abrir la página.");
    return;
  }
  var mapa = crearMapa();
  cargarJSON(ARCHIVO_INCENDIOS,
    function (datos) { alCargarIncendios(mapa, datos); },
    function (mensaje) { mostrarAviso("estado-datos", mensaje); });
}

iniciarPagina();
