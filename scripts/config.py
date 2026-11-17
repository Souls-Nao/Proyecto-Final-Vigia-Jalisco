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

# Polígono oficial de Jalisco, para el recorte fino de los puntos de calor.
# Fuente: servicio del Marco Geoestadístico del INEGI (versión de diciembre de 2025).
# El 14 al final es la clave de Jalisco en el catálogo de entidades del INEGI.
JALISCO_POLIGONO_URL = "https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgee/14"

# Jalisco usa todo el año la hora del centro de México, que va 6 horas atrás de la hora
# universal (UTC) en la que FIRMS da sus horas. Fuente: Ley de los Husos Horarios de 2022,
# que eliminó el horario de verano.
HORAS_UTC_A_LOCAL = -6

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
ARCHIVO_JALISCO = CARPETA_REFERENCIA / "jalisco.geojson"                      # script 01 (polígono del estado)
ARCHIVO_LOCALIDADES = CARPETA_REFERENCIA / "localidades_jalisco.csv"          # script 02b
ARCHIVO_BASES = CARPETA_REFERENCIA / "bases.csv"                              # bases de brigadas (hipotéticas)
ARCHIVO_RED_VIAL = CARPETA_CRUDOS / "red_vial_piloto.graphml"                 # script 06 (no se sube)
ARCHIVO_PUNTOS_CALOR = CARPETA_PROCESADOS / "puntos_calor_jalisco.csv"        # script 01
ARCHIVO_CONAFOR = CARPETA_PROCESADOS / "incendios_conafor_jalisco.csv"        # script 02 (tabla)
ARCHIVO_CONAFOR_POLIGONOS = CARPETA_PROCESADOS / "incendios_conafor_jalisco.geojson"  # script 02 (polígonos)
ARCHIVO_PUNTOS_AGRUPADOS = CARPETA_PROCESADOS / "puntos_agrupados.csv"        # script 03 (cada punto con su incendio)
ARCHIVO_CANDIDATOS = CARPETA_PROCESADOS / "incendios_candidatos.csv"          # script 03 (una fila por incendio)
ARCHIVO_VARIABLES = CARPETA_PROCESADOS / "incendios_variables.csv"            # script 04
ARCHIVO_ETIQUETADOS = CARPETA_PROCESADOS / "incendios_etiquetados.csv"        # script 04b
ARCHIVO_CLASIFICADOS = CARPETA_PROCESADOS / "incendios_clasificados.csv"      # script 05

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

# FIRMS da la confianza de MODIS como número de 0 a 100 y la de VIIRS como letra:
# l (baja), n (nominal) y h (alta). Para tener una sola escala de 0 a 1, cada letra se cambia
# por el punto medio del rango que MODIS usa para esa misma clase: baja 0 a 30, nominal 30 a 80
# y alta 80 a 100 (guía de usuario de fuego activo de MODIS). Valor inicial; se revisa en OP1.
CONFIANZA_VIIRS = {"l": 0.15, "n": 0.55, "h": 0.90}

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
# Al guardar los polígonos de CONAFOR se quitan los vértices que cambian el contorno menos de
# esta distancia. Justificación: un píxel de VIIRS mide 375 m, así que 20 m no afecta el cruce
# con los puntos de calor y el archivo baja de 27 MB a pocos MB.
SIMPLIFICAR_POLIGONOS_M = 20


# ----------------------------------------------------------------------------
# 6b. Fuente F3 · Localidades del INEGI (script 02b)
# ----------------------------------------------------------------------------
# El mismo servicio del Marco Geoestadístico entrega la lista de municipios de un estado y las
# localidades de cada municipio, con su ubicación y su población del Censo 2020.
# Fuente: https://www.inegi.org.mx/servicios/catalogounico.html (comprobado el 12 nov 2026).
INEGI_MUNICIPIOS_URL = "https://gaia.inegi.org.mx/wscatgeo/v2/mgem/14"
INEGI_LOCALIDADES_URL = "https://gaia.inegi.org.mx/wscatgeo/v2/localidades/14/{municipio}"

# ----------------------------------------------------------------------------
# 6c. Fuentes F4 y F5 · Vegetación y áreas naturales protegidas (script 02b)
# ----------------------------------------------------------------------------
# Las dos capas se bajan del geoportal de CONABIO, que redistribuye datos oficiales.
# (La primera opción era IDEFOR de CONAFOR, pero su servidor de mapas no respondía el 12 y 13 nov.)
#
# Vegetación: "Uso del suelo y vegetación, escala 1:250 000, Serie VII" del INEGI, todo el país.
# El archivo pesa 317 MB; por eso se guarda en datos/crudos/ y no se sube.
VEGETACION_URL = "http://www.conabio.gob.mx/informacion/gis/maps/geo/usv250s7gw.zip"
ARCHIVO_VEGETACION = CARPETA_CRUDOS / "conabio" / "usv250s7gw.zip"
VEGETACION_CAPA = "usv250s7gw.shp"        # nombre del mapa dentro del archivo .zip

# Áreas naturales protegidas FEDERALES de CONANP (versión de julio de 2025). No incluye las
# estatales ni las municipales: es el plan B previsto para esta fuente y se declara como limitación.
AREAS_PROTEGIDAS_URL = "http://www.conabio.gob.mx/informacion/gis/maps/geo/anpmx.zip"
ARCHIVO_AREAS_PROTEGIDAS = CARPETA_CRUDOS / "conabio" / "anpmx.zip"
AREAS_PROTEGIDAS_CAPA = "anpmx.shp"

# Un lugar NO es forestal si su tipo de vegetación empieza con alguna de estas palabras: son los
# usos agropecuarios, urbanos, el agua y los terrenos sin vegetación de la clasificación del INEGI.
# Todo lo demás (bosques, selvas, matorrales, pastizal natural y vegetación secundaria) cuenta
# como forestal. Justificación: CONAFOR solo registra incendios en terreno forestal.
USOS_NO_FORESTALES = ("AGRICULTURA", "PASTIZAL INDUCIDO", "PASTIZAL CULTIVADO", "ASENTAMIENTOS HUMANOS",
                      "CUERPO DE AGUA", "ACUÍCOLA", "SIN VEGETACIÓN", "DESPROVISTO", "PALMAR INDUCIDO")

# ----------------------------------------------------------------------------
# 7. Agrupamiento de puntos de calor en incendios candidatos (script 03)
# ----------------------------------------------------------------------------
# Dos puntos de calor se consideran del mismo incendio si están cerca en distancia y en tiempo.
# Valor inicial; se calibra en OP1. Justificación del valor inicial: un píxel de MODIS mide
# 1 km, así que dos detecciones del mismo fuego pueden quedar separadas hasta esa distancia.
DISTANCIA_MAXIMA_M = 1000
# Valor inicial; se calibra en OP1. Justificación del valor inicial: 3 de cada 4 incendios
# registrados por CONAFOR en Jalisco duran 1 día o menos (reportes/analisis_datos.md), y
# 48 horas dan margen para que el satélite vuelva a pasar sobre un incendio que sigue activo.
VENTANA_HORAS = 48
# Para que DBSCAN compare distancia y tiempo con una sola regla, las horas se convierten a
# "metros": 48 horas valen lo mismo que 1,000 metros.
METROS_POR_HORA = DISTANCIA_MAXIMA_M / VENTANA_HORAS


# ----------------------------------------------------------------------------
# 8. Variables de cada incendio (script 04)
# ----------------------------------------------------------------------------
# Detecciones del mismo satélite con menos de 30 minutos de diferencia cuentan como una sola
# pasada. Justificación: cada satélite tarda cerca de 100 minutos en dar una vuelta a la Tierra,
# así que no puede ver dos veces el mismo lugar en menos de media hora.
MINUTOS_MISMA_PASADA = 30

# Para la distancia a la población solo cuentan localidades con al menos estos habitantes.
# Valor inicial; se calibra en OP1. Justificación: la mitad de las localidades de Jalisco tiene
# 14 habitantes o menos (ranchos); sin este mínimo casi todo incendio quedaría "cerca de una
# localidad" y la regla de seguridad perdería sentido.
POBLACION_MINIMA_LOCALIDAD = 100

# Fuente fija = lugar que emite calor casi todo el año (industria, ladrilleras), no un incendio.
# Se marca de dos maneras:
# 1) FIRMS ya etiqueta algunos puntos como fuente fija (tipo 2). Si al menos la mitad de los
#    puntos del incendio son de ese tipo, se marca. Valor inicial.
FRACCION_PUNTOS_FIJOS = 0.5
# 2) Se divide el estado en cuadros de 1 km y se cuenta en cuántos meses distintos del año hubo
#    puntos de calor en cada cuadro. Con 6 meses o más se considera fuente fija. Valor inicial;
#    se calibra en OP1. Justificación: el 88 % de los puntos de calor cae de marzo a junio
#    (4 meses); un lugar con calor en 6 meses o más no sigue la temporada de incendios.
CUADRO_FUENTE_FIJA_M = 1000
MESES_FUENTE_FIJA = 6


# ----------------------------------------------------------------------------
# 9. Etiquetas: cruce de los candidatos con los registros de CONAFOR (script 04b)
# ----------------------------------------------------------------------------
# Un candidato se etiqueta como "real" si su centro queda a esta distancia o menos del polígono
# de un incendio registrado por CONAFOR...
# Calibrado con 2024 (el valor inicial era 3 km). Justificación: de los candidatos que coinciden
# en fecha con un registro, casi todos están dentro del polígono o a menos de 1 km; más lejos,
# las coincidencias se reparten parejo, como si fueran casualidad (reportes/analisis_datos.md).
TOLERANCIA_KM = 1
# ...y si sus fechas se traslapan con las del registro, con este margen de días.
# Calibrado con 2024 (el valor inicial era 3 días). Justificación: a 1 y 2 días de distancia
# todavía hay más coincidencias que las que da la casualidad; a 3 días o más, ya no.
TOLERANCIA_DIAS = 2

# Niveles de severidad, de menor a mayor. En los datos van sin acento.
NIVELES = ["bajo", "medio", "alto", "critico"]
# Superficie (hectáreas) en la que empieza cada nivel real: menos de 30 es bajo, de 30 a 100
# medio, de 100 a 600 alto y 600 o más crítico.
# Justificación: son los cuartiles (redondeados) de la superficie de los incendios de 2024 que
# sí detectó el satélite: 31.5, 97.4 y 606.3 ha. Así cada nivel tiene la cuarta parte de los casos.
CORTES_SEVERIDAD_HA = [30, 100, 600]

# ----------------------------------------------------------------------------
# 10. Paso A por reglas: ¿incendio real o falsa alarma? (script 05)
# ----------------------------------------------------------------------------
# Las reglas se ajustaron SOLO con los datos de 2024 y se prueban con 2025 (decisión D9).
# Regla 1: fuente fija -> falsa alarma.
# Regla 2: terreno forestal y visto en al menos estas pasadas de satélite -> real.
PASADAS_MINIMAS_REAL = 2
# Regla 3: un grupo con al menos estos puntos de calor -> real, aunque el terreno no sea forestal.
PUNTOS_MINIMOS_REAL = 15
# Regla 4: todo lo demás -> probable falsa alarma.
#
# "prob_real" de cada regla = parte de los candidatos de 2024 que cumplieron esa regla y
# coincidieron con un registro de CONAFOR. Medido con 2024 (reportes/analisis_datos.md).
# Ojo: CONAFOR no registra todos los incendios, así que estos números son un mínimo.
PROB_REAL = {
    "fuente_fija": 0.00,          # 0 de 154
    "forestal_persistente": 0.36,  # 346 de 965
    "grupo_grande": 0.48,         # 10 de 21
    "forestal_una_pasada": 0.11,  # 234 de 2,095
    "no_forestal": 0.03,          # 100 de 3,794
}

# ----------------------------------------------------------------------------
# 11. Paso B por reglas: nivel de severidad (script 05)
# ----------------------------------------------------------------------------
# Cada condición que se cumple suma un punto. Ajustado con los incendios reales de 2024.
PUNTOS_SEVERIDAD = [5, 15, 40]     # con 5, 15 o 40 puntos de calor o más: +1, +2 o +3
FRP_SEVERIDAD = [30, 100]          # con intensidad máxima de 30 o 100 MW o más: +1 o +2
DURACION_SEVERIDAD_H = 24          # si duró 24 horas o más: +1
# Dentro de un área natural protegida: +1 (no predice el tamaño; cuenta por lo que está en riesgo).
# Lejos de las localidades: +1. Justificación: en 2024 los incendios a menos de 2 km de una
# localidad quemaron 38 ha (mediana) y los que estaban a más de 8 km, 837 ha: lejos de la gente
# se detectan y se atienden más tarde. Con esta condición, los incendios críticos clasificados
# como bajos pasaron de 67 a 15.
DISTANCIA_LEJOS_KM = 4
# Puntaje mínimo de cada nivel: 0 es bajo, 1 o 2 medio, 3 o 4 alto y 5 o más crítico.
# (El punto de partida era 0-1, 2-3, 4-5 y 6+; con 2024 estos cortes aciertan más.)
PUNTAJE_MINIMO_NIVEL = [1, 3, 5]

# Regla de seguridad: un incendio a menos de esta distancia de una localidad (de 100 habitantes
# o más) sube al menos a nivel alto, aunque sea pequeño.
# El valor inicial era 2 km, pero a esa distancia está 1 de cada 5 incendios reales de 2024 y la
# regla dejaría de ser excepcional. A menos de 1 km está el 5 %. Confirmado por el equipo el 13 nov 2026.
DISTANCIA_SEGURIDAD_KM = 1
NIVEL_MINIMO_SEGURIDAD = "alto"


# ----------------------------------------------------------------------------
# 12. Tabla de respuesta: recursos que se recomiendan para cada nivel
# ----------------------------------------------------------------------------
# SUPUESTO DEL EQUIPO. No está validado por un brigadista ni por un especialista en manejo del
# fuego; se declara como limitación. La idea: cada nivel pide una brigada más que el anterior,
# la unidad con motobomba entra desde el nivel alto y en el crítico se RECOMIENDA pedir apoyo
# aéreo (la herramienta no lo asigna ni lo solicita).
TABLA_RESPUESTA = {
    "bajo":    {"brigadas": 1, "motobomba": False, "apoyo_aereo": False},
    "medio":   {"brigadas": 2, "motobomba": False, "apoyo_aereo": False},
    "alto":    {"brigadas": 3, "motobomba": True,  "apoyo_aereo": False},
    "critico": {"brigadas": 4, "motobomba": True,  "apoyo_aereo": True},
}
# Peso de cada nivel al repartir brigadas: llegar tarde a un incendio crítico "cuesta" 8 veces
# más que llegar tarde a uno bajo. Supuesto del equipo: cada nivel pesa el doble que el anterior.
PESO_NIVEL = {"bajo": 1, "medio": 2, "alto": 4, "critico": 8}

# ----------------------------------------------------------------------------
# 13. Rutas en la región piloto (script 06)
# ----------------------------------------------------------------------------
# Servidores públicos de donde se puede bajar la red de caminos de OpenStreetMap. Se prueban en
# orden: si uno está saturado o no responde, se intenta con el siguiente.
# Fuente: lista de servidores públicos de Overpass en la wiki de OpenStreetMap
# (https://wiki.openstreetmap.org/wiki/Overpass_API#Public_Overpass_API_instances).
SERVIDORES_OSM = [
    "https://overpass-api.de/api",
    "https://maps.mail.ru/osm/tools/overpass/api",
    "https://overpass.private.coffee/api",
]

# Tipos de camino de OpenStreetMap que se usan. Se incluyen las brechas ("track") porque son
# el acceso al bosque; se dejan fuera andadores y ciclovías, por donde no pasa un vehículo.
TIPOS_DE_CAMINO = ("motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|"
                   "tertiary|tertiary_link|unclassified|residential|living_street|service|track")
# Velocidad (km/h) que se supone en cada tipo de camino cuando OpenStreetMap no trae su límite.
# SUPUESTO DEL EQUIPO (valores iniciales): límites usuales de tránsito para calles (30), avenidas
# (40 a 60) y carreteras (80 a 90), y velocidades bajas en brechas y accesos. Son tiempos de un
# vehículo en condiciones normales, sin tráfico; no están medidos con brigadas reales.
VELOCIDADES_KMH = {
    "motorway": 90, "motorway_link": 60, "trunk": 80, "trunk_link": 50,
    "primary": 60, "primary_link": 40, "secondary": 50, "secondary_link": 40,
    "tertiary": 40, "tertiary_link": 30, "unclassified": 30, "residential": 30,
    "living_street": 20, "service": 20, "track": 20,
}
# Las rutas se guardan con menos detalle para que el archivo del sitio pese poco: se quitan los
# puntos que cambian el trazo menos de 30 metros (no se nota en el mapa).
SIMPLIFICAR_RUTAS_M = 30


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
    print("Polígono de Jalisco (INEGI):")
    print("  ", JALISCO_POLIGONO_URL)
    print("Vegetación (INEGI, vía CONABIO):", VEGETACION_URL)
    print("Áreas protegidas (CONANP, vía CONABIO):", AREAS_PROTEGIDAS_URL)
    print("Capas de CONAFOR:")
    for anio in ANIOS:
        print("  ", anio, "->", CONAFOR_CAPAS[anio])


# Esto solo se ejecuta al correr "python scripts/config.py", no cuando otro script hace "import config".
if __name__ == "__main__":
    revisar_regiones()
    crear_carpetas()
    mostrar_configuracion()
    print("Configuración correcta. Carpetas de datos listas.")
