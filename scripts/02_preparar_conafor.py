# 02_preparar_conafor.py
# Descarga los incendios forestales que CONAFOR registró en Jalisco (2024 y 2025) y los deja limpios.
# Estos registros son las "etiquetas": con ellos sabremos qué incendios fueron reales y de qué tamaño.
# Lee:     internet (capas de polígonos de incendios de CONAFOR en IDEFOR).
# Escribe: datos/crudos/conafor/conafor_jalisco_<anio>.geojson   (descarga tal cual; no se sube)
#          datos/procesados/incendios_conafor_jalisco.csv        (una fila por incendio)
#          datos/procesados/incendios_conafor_jalisco.geojson    (los mismos, con su polígono)
# Uso:     python scripts/02_preparar_conafor.py

import geopandas as gpd
import pandas as pd
import requests

import config


def descargar_capa(anio, destino):
    """Pide a IDEFOR los incendios de Jalisco de un año. Si ya están descargados, no los vuelve a pedir."""
    if destino.exists():
        print("  Ya estaba descargado:", destino.name)
        return
    print("  Descargando incendios de CONAFOR de", anio)
    # WFS es el servicio estándar para bajar capas de mapas. El filtro pide solo Jalisco.
    parametros = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": config.CONAFOR_CAPAS[anio],
        "outputFormat": "application/json",
        "CQL_FILTER": f"ESTADO='{config.CONAFOR_ESTADO}'",
    }
    respuesta = requests.get(config.CONAFOR_SERVICIO, params=parametros, timeout=300)
    if respuesta.status_code != 200 or not respuesta.text.startswith("{"):
        raise SystemExit(f"IDEFOR no entregó los datos de {anio} (código {respuesta.status_code}). "
                         "Revisa tu conexión a internet o intenta más tarde.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(respuesta.text, encoding="utf-8")


def limpiar_incendios(crudos, anio):
    """Cambia los nombres de CONAFOR por nombres claros y calcula el centro de cada polígono."""
    # Algunos polígonos vienen con errores de dibujo; make_valid los repara sin moverlos.
    crudos["geometry"] = crudos.geometry.make_valid()
    # El centro se calcula en metros (UTM 13N) y también se guarda en latitud y longitud.
    centros_m = crudos.to_crs(config.CRS_METROS).geometry.centroid
    centros_grados = centros_m.to_crs(config.CRS_GRADOS)
    fecha_inicio = pd.to_datetime(crudos["FECHAINIC"], errors="coerce")
    fecha_fin = pd.to_datetime(crudos["FECHALIQ"], errors="coerce")
    incendios = gpd.GeoDataFrame({
        "id_conafor": crudos["CLAVEINC"],
        "anio": anio,
        "municipio": crudos["MUNICIPIO"],
        "fecha_inicio": fecha_inicio.dt.strftime("%Y-%m-%d"),
        "fecha_fin": fecha_fin.dt.strftime("%Y-%m-%d"),      # fecha de liquidación (incendio apagado)
        "duracion_dias": (fecha_fin - fecha_inicio).dt.days,
        "superficie_ha": crudos["AREA_HA"].round(2),
        "causa": crudos["CAUSA"],
        "vegetacion": crudos["TIPVEG"],
        "tipo_incendio": crudos["TIPOINC"],
        "impacto": crudos["TIPIMPAC"],
        # CONAFOR escribe "N/A" cuando no hay área protegida. Se cambia por "ninguna" porque
        # pandas confunde "N/A" con un dato faltante al leer el CSV.
        "area_protegida": crudos["ANP"].replace("N/A", "ninguna"),
        "metodo_poligono": crudos["POLIGONO"],
        "lat": centros_grados.y.round(5),
        "lon": centros_grados.x.round(5),
        "x": centros_m.x.round(1),
        "y": centros_m.y.round(1),
    }, geometry=crudos.geometry, crs=crudos.crs)
    return incendios


def guardar_poligonos(poligonos):
    """Guarda los polígonos con menos detalle, para que el archivo pese poco."""
    # Los polígonos originales traen un vértice cada pocos metros y pesan 27 MB.
    # Se simplifican en metros y se guardan en grados con 6 decimales (unos 10 centímetros).
    en_metros = poligonos.to_crs(config.CRS_METROS)
    # Al simplificar, unos pocos polígonos quedan con cruces; make_valid los repara.
    en_metros["geometry"] = en_metros.geometry.simplify(config.SIMPLIFICAR_POLIGONOS_M).make_valid()
    en_metros.to_crs(config.CRS_GRADOS).to_file(
        config.ARCHIVO_CONAFOR_POLIGONOS, driver="GeoJSON", COORDINATE_PRECISION=6)


def mostrar_resumen(incendios):
    """Imprime conteos y datos faltantes, para saber qué tan completas vienen las etiquetas."""
    print("Incendios registrados por año:")
    print(incendios.groupby("anio").size().to_string())
    print("Datos faltantes por columna (0 = completa):")
    faltantes = incendios.drop(columns="geometry").isna().sum()
    print(faltantes[faltantes > 0].to_string() if faltantes.sum() > 0 else "  ninguno")
    print("Superficie afectada (hectáreas) por año:")
    print(incendios.groupby("anio")["superficie_ha"].describe().round(1).to_string())
    print("Duración en días (de inicio a liquidación) por año:")
    print(incendios.groupby("anio")["duracion_dias"].describe().round(1).to_string())


def main():
    config.crear_carpetas()

    print("1. Descarga desde IDEFOR (CONAFOR)")
    tablas = []
    for anio in config.ANIOS:
        destino = config.CARPETA_CRUDOS / "conafor" / f"conafor_jalisco_{anio}.geojson"
        descargar_capa(anio, destino)
        tablas.append(limpiar_incendios(gpd.read_file(destino), anio))
    incendios = pd.concat(tablas, ignore_index=True)

    print("2. Guardar la tabla y los polígonos")
    incendios.drop(columns="geometry").to_csv(config.ARCHIVO_CONAFOR, index=False)
    # En el archivo de polígonos van solo las columnas que se usan para cruzar con los puntos de calor.
    columnas = ["id_conafor", "anio", "fecha_inicio", "fecha_fin", "superficie_ha", "geometry"]
    guardar_poligonos(incendios[columnas])

    mostrar_resumen(incendios)
    print("Listo:", len(incendios), "incendios guardados en", config.ARCHIVO_CONAFOR)


if __name__ == "__main__":
    main()
