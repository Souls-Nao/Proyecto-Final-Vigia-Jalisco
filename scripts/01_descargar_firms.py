# 01_descargar_firms.py
# Descarga los puntos de calor de NASA FIRMS (México, 2024 y 2025) y se queda con los de Jalisco.
# Lee:     internet (archivos anuales de FIRMS y el polígono de Jalisco del INEGI).
# Escribe: datos/crudos/firms/*.csv            (descargas completas de México; no se suben)
#          datos/referencia/jalisco.geojson    (polígono del estado)
#          datos/procesados/puntos_calor_jalisco.csv
# Uso:     python scripts/01_descargar_firms.py

import geopandas as gpd
import pandas as pd
import requests

import config


def descargar_archivo(url, destino):
    """Baja un archivo de internet. Si ya está en la computadora, no lo vuelve a bajar."""
    if destino.exists():
        print("  Ya estaba descargado:", destino.name)
        return
    print("  Descargando", url)
    respuesta = requests.get(url, timeout=300)
    if respuesta.status_code != 200:
        raise SystemExit(f"No se pudo descargar {url} (código {respuesta.status_code}). "
                         "Revisa tu conexión a internet y vuelve a correr el script.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(respuesta.content)


def leer_puntos(ruta, sensor, anio):
    """Lee un archivo de FIRMS y deja solo los puntos que caen en la caja de Jalisco."""
    # La hora y la confianza se leen como texto: la hora viene como "0739" (7:39) y perdería
    # el cero inicial; la confianza de VIIRS es una letra.
    puntos = pd.read_csv(ruta, dtype={"acq_time": str, "confidence": str})
    en_caja = (puntos["longitude"].between(config.JALISCO_OESTE, config.JALISCO_ESTE)
               & puntos["latitude"].between(config.JALISCO_SUR, config.JALISCO_NORTE))
    puntos = puntos[en_caja].copy()
    puntos["sensor"] = sensor
    puntos["anio"] = anio
    return puntos


def normalizar_confianza(puntos):
    """Devuelve la confianza como número de 0 a 1, sin importar el sensor."""
    # MODIS la da de 0 a 100; VIIRS la da como letra (l, n, h) y se traduce con la tabla de config.
    como_numero = pd.to_numeric(puntos["confidence"], errors="coerce") / 100
    como_letra = puntos["confidence"].map(config.CONFIANZA_VIIRS)
    return como_numero.fillna(como_letra)


def ordenar_columnas(puntos):
    """Cambia los nombres de FIRMS por nombres en español y arma la fecha y hora."""
    # FIRMS da la hora en tiempo universal (UTC). Guardamos también la hora local de Jalisco,
    # porque CONAFOR registra sus fechas en hora local.
    texto_fecha = puntos["acq_date"] + " " + puntos["acq_time"].str.zfill(4)
    fecha_hora_utc = pd.to_datetime(texto_fecha, format="%Y-%m-%d %H%M")
    return pd.DataFrame({
        "lat": puntos["latitude"],
        "lon": puntos["longitude"],
        "fecha_hora_utc": fecha_hora_utc,
        "fecha_hora_local": fecha_hora_utc + pd.Timedelta(hours=config.HORAS_UTC_A_LOCAL),
        "anio": puntos["anio"],
        "sensor": puntos["sensor"],
        "satelite": puntos["satellite"],
        "confianza": normalizar_confianza(puntos).round(2),
        "frp": puntos["frp"],                 # potencia radiativa del fuego, en megawatts
        "dia_noche": puntos["daynight"],      # D = de día, N = de noche
        "tipo_fuente": puntos["type"],        # 0 vegetación, 1 volcán, 2 fuente fija, 3 mar
    })


def recortar_a_jalisco(puntos, jalisco):
    """Quita los puntos que quedaron fuera del polígono de Jalisco y agrega x, y en metros."""
    geometria = gpd.points_from_xy(puntos["lon"], puntos["lat"])
    puntos_geo = gpd.GeoDataFrame(puntos, geometry=geometria, crs=config.CRS_GRADOS)
    # sjoin deja solo los puntos que caen dentro del polígono.
    dentro = gpd.sjoin(puntos_geo, jalisco[["geometry"]], predicate="within")
    # Para medir distancias después, pasamos a metros (UTM 13N).
    en_metros = dentro.to_crs(config.CRS_METROS)
    dentro["x"] = en_metros.geometry.x.round(1)
    dentro["y"] = en_metros.geometry.y.round(1)
    return pd.DataFrame(dentro.drop(columns=["geometry", "index_right"]))


def mostrar_resumen(puntos):
    """Imprime cuántos puntos quedaron por año y sensor, para revisar a simple vista."""
    print("Puntos de calor en Jalisco por año y sensor:")
    print(puntos.groupby(["anio", "sensor"]).size().to_string())
    print("Tipo de fuente (0 vegetación, 1 volcán, 2 fuente fija, 3 mar):")
    print(puntos["tipo_fuente"].value_counts().sort_index().to_string())


def main():
    config.crear_carpetas()

    print("1. Polígono de Jalisco (INEGI)")
    descargar_archivo(config.JALISCO_POLIGONO_URL, config.ARCHIVO_JALISCO)
    jalisco = gpd.read_file(config.ARCHIVO_JALISCO).to_crs(config.CRS_GRADOS)

    print("2. Archivos anuales de FIRMS")
    tablas = []
    for anio in config.ANIOS:
        for sensor in config.FIRMS_SENSORES:
            destino = config.CARPETA_CRUDOS / "firms" / f"{sensor}_{anio}_Mexico.csv"
            descargar_archivo(config.FIRMS_URL.format(sensor=sensor, anio=anio), destino)
            tablas.append(leer_puntos(destino, sensor, anio))
    puntos = pd.concat(tablas, ignore_index=True)
    print("  Puntos dentro de la caja de Jalisco:", len(puntos))

    print("3. Recorte al polígono de Jalisco")
    puntos = recortar_a_jalisco(ordenar_columnas(puntos), jalisco)
    puntos = puntos.sort_values("fecha_hora_utc")
    puntos.to_csv(config.ARCHIVO_PUNTOS_CALOR, index=False)

    mostrar_resumen(puntos)
    print("Listo:", len(puntos), "puntos guardados en", config.ARCHIVO_PUNTOS_CALOR)


if __name__ == "__main__":
    main()
