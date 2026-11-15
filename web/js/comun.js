/*
  comun.js · Funciones que comparten todas las páginas de Vigía Jalisco (versión 1)
  Qué hace:  1) dibuja el menú, 2) carga archivos JSON de web/datos/ y 3) guarda los colores
             y nombres de los niveles de severidad.
  Lo usan:   las páginas de web/ con <script src="js/comun.js"></script>
  Cómo se prueba: abrir web/acerca.html; el menú debe aparecer con "Acerca de" resaltado.
*/

// ---------------------------------------------------------------------------
// 1. Menú
// ---------------------------------------------------------------------------

// Lista de páginas del sitio, en el orden en que salen en el menú.
// "lista" dice si la página ya existe. Cuando se suba una página nueva, se cambia a true.
var PAGINAS = [
  { archivo: "index.html", nombre: "Mapa de incendios", lista: true },
  { archivo: "plan.html", nombre: "Plan de ataque", lista: false },
  { archivo: "probar.html", nombre: "Probar clasificación", lista: false },
  { archivo: "resultados.html", nombre: "Resultados", lista: false },
  { archivo: "acerca.html", nombre: "Acerca de", lista: true }
];

// Devuelve el nombre del archivo que se está viendo, por ejemplo "acerca.html".
function paginaActual() {
  var partes = window.location.pathname.split("/");
  var archivo = partes[partes.length - 1];
  // Si la dirección termina en "/", el navegador está mostrando index.html.
  return archivo === "" ? "index.html" : archivo;
}

// Llena el elemento <nav id="menu"> con los enlaces a las páginas.
function dibujarMenu() {
  var menu = document.getElementById("menu");
  var actual = paginaActual();
  PAGINAS.forEach(function (pagina) {
    var elemento;
    if (pagina.lista) {
      elemento = document.createElement("a");
      elemento.href = pagina.archivo;
      // La página en la que estamos se resalta.
      if (pagina.archivo === actual) {
        elemento.className = "menu-actual";
      }
    } else {
      // Las páginas que todavía no existen se ven apagadas y no se pueden abrir.
      elemento = document.createElement("span");
      elemento.className = "menu-pendiente";
      elemento.title = "Página en construcción";
    }
    elemento.textContent = pagina.nombre;
    menu.appendChild(elemento);
  });
}

// ---------------------------------------------------------------------------
// 2. Carga de datos
// ---------------------------------------------------------------------------

// Lee un archivo JSON (por ejemplo "datos/incendios_2025.json").
// Si todo sale bien llama a alTerminar(datos); si no, llama a alFallar(mensaje)
// con un mensaje claro, para que la página no se quede en blanco.
function cargarJSON(ruta, alTerminar, alFallar) {
  fetch(ruta)
    .then(function (respuesta) {
      if (!respuesta.ok) {
        throw new Error("no encontrado");
      }
      return respuesta.json();
    })
    .then(alTerminar)
    .catch(function () {
      alFallar("No se pudieron cargar los datos (" + ruta + "). " +
               "Puede que el archivo todavía no esté publicado o que no haya conexión a internet.");
    });
}

// Escribe un mensaje de aviso dentro del elemento con ese id.
function mostrarAviso(idElemento, mensaje) {
  var elemento = document.getElementById(idElemento);
  elemento.textContent = mensaje;
  elemento.className = "aviso";
}

// ---------------------------------------------------------------------------
// 3. Niveles de severidad
// ---------------------------------------------------------------------------

// Un color por nivel. Son los mismos que están en css/estilos.css.
// "falsa" es para los incendios clasificados como probable falsa alarma.
var COLORES_NIVEL = {
  bajo: "#4caf50",
  medio: "#f2c200",
  alto: "#f57c00",
  critico: "#c62828",
  falsa: "#9e9e9e"
};

// Cómo se escribe cada nivel en pantalla (en los datos van sin acento).
var NOMBRES_NIVEL = {
  bajo: "Bajo",
  medio: "Medio",
  alto: "Alto",
  critico: "Crítico",
  falsa: "Probable falsa alarma"
};

// Devuelve el nivel con el que se pinta un incendio: su nivel si es real, "falsa" si no.
function nivelParaPintar(incendio) {
  return incendio.es_real ? incendio.nivel : "falsa";
}

// Devuelve el color con el que se pinta un incendio.
function colorDeIncendio(incendio) {
  return COLORES_NIVEL[nivelParaPintar(incendio)];
}
