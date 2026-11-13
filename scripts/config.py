# config.py
# Guarda en un solo lugar las regiones, las carpetas y las fuentes de datos que usan todos los scripts.
# Lee:     nada.
# Escribe: nada. Si se corre solo, muestra la configuración y crea las carpetas de datos que falten.
# Uso:     python scripts/config.py      (los demás scripts lo usan con "import config")
#
# Regla del proyecto: cada número lleva un comentario con su FUENTE o su JUSTIFICACIÓN.

import sys
from pathlib import Path

# Para que los acentos de los mensajes se vean bien en cualquier terminal de Windows
# (PowerShell, Git Bash o la de VS Code). Como todos los scripts importan config, basta ponerlo aquí.
sys.stdout.reconfigure(encoding="utf-8")

# ----------------------------------------------------------------------------
# 1. Años de trabajo
# ----------------------------------------------------------------------------
# Decisión D9: los modelos se entrenan con 2024 y se prueban con 2025. Nunca se mezclan.
ANIO_ENTRENAMIENTO = 2024
ANIO_PRUEBA = 2025
ANIOS = [ANIO_ENTRENAMIENTO, ANIO_PRUEBA]

# ----------------------------------------------------------------------------
# 2. Sistemas de coordenadas
# ----------------------------------------------------------------------------
# EPSG:4326 = latitud y longitud en grados. Así llegan FIRMS y CONAFOR y así se manda a la web.
CRS_GRADOS = "EPSG:4326"
# EPSG:32613 = UTM zona 13 norte, en metros. Se usa para medir distancias en Jalisco,
# porque casi todo el estado cae en esa zona (longitudes de -108 a -102).
CRS_METROS = "EPSG:32613"

# ----------------------------------------------------------------------------
# 3. Regiones (en grados, orden: oeste, sur, este, norte)
# ----------------------------------------------------------------------------
# Caja que encierra a Jalisco. Sirve solo para un primer recorte rápido de los puntos de calor;
# el recorte fino se hará después con el polígono estatal del INEGI.
# Fuente: coordenadas extremas de Jalisco según INEGI (norte 22°45'01", sur 18°55'33",
# este 101°30'38", oeste 105°41'43"), con un margen de unos 5 km por lado.
# https://www.inegi.org.mx/contenidos/app/areasgeograficas/resumen/resumen_14.pdf
JALISCO_OESTE = -105.75
JALISCO_SUR = 18.87
JALISCO_ESTE = -101.45
JALISCO_NORTE = 22.80

# Región piloto: Bosque La Primavera y Área Metropolitana de Guadalajara.
# Solo aquí se calculan rutas y plan de ataque (decisión D5).
# Fuente: definida por el equipo en CONTEXTO_COMPLETO.md, sección 10.
PILOTO_OESTE = -103.90
PILOTO_SUR = 20.40
PILOTO_ESTE = -103.15
PILOTO_NORTE = 20.95

# ----------------------------------------------------------------------------
# 4. Carpetas y archivos del proyecto
# ----------------------------------------------------------------------------
# La carpeta del proyecto es la que contiene a "scripts/". Así los scripts funcionan
# sin importar desde dónde se corran.
CARPETA_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_CRUDOS = CARPETA_PROYECTO / "datos" / "crudos"          # descargas grandes; NO se sube
CARPETA_REFERENCIA = CARPETA_PROYECTO / "datos" / "referencia"  # archivos pequeños (bases, cortes)
CARPETA_PROCESADOS = CARPETA_PROYECTO / "datos" / "procesados"  # CSV intermedios
CARPETA_WEB_DATOS = CARPETA_PROYECTO / "web" / "datos"          # JSON que lee el sitio
CARPETA_REPORTES = CARPETA_PROYECTO / "reportes"

CARPETAS_DE_DATOS = [CARPETA_CRUDOS, CARPETA_REFERENCIA, CARPETA_PROCESADOS, CARPETA_WEB_DATOS]

# Archivos que producen los primeros scripts (el número dice qué script lo escribe).
ARCHIVO_PUNTOS_CALOR = CARPETA_PROCESADOS / "puntos_calor_jalisco.csv"        # script 01
ARCHIVO_CONAFOR = CARPETA_PROCESADOS / "incendios_conafor_jalisco.csv"        # script 02
ARCHIVO_CANDIDATOS = CARPETA_PROCESADOS / "incendios_candidatos.csv"          # script 03
ARCHIVO_VARIABLES = CARPETA_PROCESADOS / "incendios_variables.csv"            # script 04

# ----------------------------------------------------------------------------
# 5. Fuente F1 · Puntos de calor de NASA FIRMS
# ----------------------------------------------------------------------------
# FIRMS publica un archivo por país, por año y por sensor. No piden clave.
# Fuente: https://firms.modaps.eosdis.nasa.gov/country/  (comprobado el 12 nov 2026:
# existen los archivos de México 2024 y 2025 para los dos sensores de abajo).
FIRMS_URL = "https://firms.modaps.eosdis.nasa.gov/data/country/{sensor}/{anio}/{sensor}_{anio}_Mexico.csv"
# viirs-snpp = sensor VIIRS del satélite Suomi NPP (píxel de 375 m).
# modis      = sensor MODIS de los satélites Terra y Aqua (píxel de 1 km).
FIRMS_SENSORES = ["viirs-snpp", "modis"]

# ----------------------------------------------------------------------------
# 6. Fuente F2 · Registros de incendios de CONAFOR
# ----------------------------------------------------------------------------
# "Concentrado Nacional de Polígonos de Incendios Forestales", publicado por CONAFOR en IDEFOR.
# Cada registro trae el polígono quemado, fecha de inicio, fecha de liquidación y hectáreas.
# Fuente: https://idefor.cnf.gob.mx  (comprobado el 12 nov 2026: Jalisco tiene 950 registros
# en 2024 y 919 en 2025).
CONAFOR_SERVICIO = "https://idefor.cnf.gob.mx/geoserver/ows"
CONAFOR_CAPAS = {
    2024: "geonode:_2024_incendios_forestales",
    2025: "geonode:poligonos_aq_2025",
}
# Así viene escrito el estado en la columna ESTADO de esas capas.
CONAFOR_ESTADO = "Jalisco"


def crear_carpetas():
    """Crea las carpetas de datos que todavía no existan."""
    for carpeta in CARPETAS_DE_DATOS:
        carpeta.mkdir(parents=True, exist_ok=True)


def revisar_regiones():
    """Comprueba que las cajas tengan sentido y que la región piloto esté dentro de Jalisco."""
    assert JALISCO_OESTE < JALISCO_ESTE and JALISCO_SUR < JALISCO_NORTE, "La caja de Jalisco está al revés."
    assert PILOTO_OESTE < PILOTO_ESTE and PILOTO_SUR < PILOTO_NORTE, "La caja de la región piloto está al revés."
    assert JALISCO_OESTE < PILOTO_OESTE and PILOTO_ESTE < JALISCO_ESTE, "La región piloto se sale de Jalisco (este-oeste)."
    assert JALISCO_SUR < PILOTO_SUR and PILOTO_NORTE < JALISCO_NORTE, "La región piloto se sale de Jalisco (norte-sur)."


def mostrar_configuracion():
    """Imprime la configuración para revisarla de un vistazo."""
    print("Proyecto:      ", CARPETA_PROYECTO)
    print("Años:           entrena con", ANIO_ENTRENAMIENTO, "y prueba con", ANIO_PRUEBA)
    print("Jalisco:        oeste", JALISCO_OESTE, "sur", JALISCO_SUR, "este", JALISCO_ESTE, "norte", JALISCO_NORTE)
    print("Región piloto:  oeste", PILOTO_OESTE, "sur", PILOTO_SUR, "este", PILOTO_ESTE, "norte", PILOTO_NORTE)
    print("Archivos de FIRMS que se van a descargar:")
    for anio in ANIOS:
        for sensor in FIRMS_SENSORES:
            print("  ", FIRMS_URL.format(sensor=sensor, anio=anio))
    print("Capas de CONAFOR:")
    for anio in ANIOS:
        print("  ", anio, "->", CONAFOR_CAPAS[anio])


# Esto solo se ejecuta al correr "python scripts/config.py", no cuando otro script hace "import config".
if __name__ == "__main__":
    revisar_regiones()
    crear_carpetas()
    mostrar_configuracion()
    print("Configuración correcta. Carpetas de datos listas.")
