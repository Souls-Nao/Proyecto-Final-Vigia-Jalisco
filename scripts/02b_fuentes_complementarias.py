# 02b_fuentes_complementarias.py
# Descarga las fuentes que complementan a los puntos de calor:
#   1) las localidades de Jalisco (dónde vive la gente y cuánta),
#   2) el mapa de uso del suelo y vegetación del INEGI (para saber si un lugar es forestal) y
#   3) las áreas naturales protegidas federales.
# Lee:     internet (INEGI y geoportal de CONABIO).
# Escribe: datos/referencia/localidades_jalisco.csv
#          datos/crudos/conabio/usv250s7gw.zip   (vegetación de todo el país, 317 MB; no se sube)
#          datos/crudos/conabio/anpmx.zip        (áreas protegidas, 6 MB; no se sube)
# Uso:     python scripts/02b_fuentes_complementarias.py     (la primera vez tarda varios minutos)

import geopandas as gpd
import pandas as pd
import requests

import config


def pedir_datos(url):
    """Pide una lista al servicio del INEGI y la devuelve. Avisa con claridad si falla."""
    respuesta = requests.get(url, timeout=120)
    if respuesta.status_code != 200 or "datos" not in respuesta.json():
        raise SystemExit(f"El INEGI no entregó los datos de {url}. "
                         "Revisa tu conexión a internet o intenta más tarde.")
    return respuesta.json()["datos"]


def descargar_archivo_grande(url, destino):
    """Baja un archivo pesado por partes, para no llenar la memoria. Si ya está, no lo vuelve a bajar."""
    if destino.exists():
        print("  Ya estaba descargado:", destino.name)
        return
    print("  Descargando", url, "(puede tardar varios minutos)")
    destino.parent.mkdir(parents=True, exist_ok=True)
    respuesta = requests.get(url, stream=True, timeout=600)
    if respuesta.status_code != 200:
        raise SystemExit(f"No se pudo descargar {url} (código {respuesta.status_code}). Intenta más tarde.")
    # Se guarda primero con otro nombre: si la descarga se corta, no queda un archivo a medias
    # con el nombre bueno.
    temporal = destino.with_suffix(".descargando")
    with open(temporal, "wb") as archivo:
        for parte in respuesta.iter_content(chunk_size=1024 * 1024):
            archivo.write(parte)
    temporal.rename(destino)


def descargar_localidades():
    """Baja las localidades de todos los municipios de Jalisco y las junta en una sola tabla."""
    municipios = pedir_datos(config.INEGI_MUNICIPIOS_URL)
    print("  Municipios de Jalisco:", len(municipios))
    filas = []
    # El servicio entrega las localidades de un municipio a la vez.
    for municipio in municipios:
        url = config.INEGI_LOCALIDADES_URL.format(municipio=municipio["cve_mun"])
        for localidad in pedir_datos(url):
            filas.append({
                "clave": localidad["cvegeo"],
                "nombre": localidad["nomgeo"],
                "municipio": municipio["nomgeo"],
                "ambito": localidad["ambito"],              # URBANO o RURAL
                "lat": localidad["latitud"],
                "lon": localidad["longitud"],
                "poblacion": localidad["pob_total"],        # Censo de Población y Vivienda 2020
            })
    return pd.DataFrame(filas)


def limpiar_localidades(localidades):
    """Pasa los textos a números, quita lo que no sirve y agrega las coordenadas en metros."""
    for columna in ["lat", "lon", "poblacion"]:
        localidades[columna] = pd.to_numeric(localidades[columna], errors="coerce")
    # Sin coordenadas no se puede medir distancia; sin habitantes no hay población que proteger.
    localidades = localidades.dropna(subset=["lat", "lon"])
    localidades = localidades[localidades["poblacion"] > 0].copy()
    localidades["poblacion"] = localidades["poblacion"].astype(int)
    geometria = gpd.points_from_xy(localidades["lon"], localidades["lat"], crs=config.CRS_GRADOS)
    en_metros = gpd.GeoSeries(geometria).to_crs(config.CRS_METROS)
    localidades["x"] = en_metros.x.round(1).values
    localidades["y"] = en_metros.y.round(1).values
    return localidades


def main():
    config.crear_carpetas()
    print("1. Localidades de Jalisco (INEGI)")
    localidades = limpiar_localidades(descargar_localidades())
    localidades.to_csv(config.ARCHIVO_LOCALIDADES, index=False)

    print("Localidades con habitantes:", len(localidades))
    print("  urbanas:", (localidades["ambito"] == "URBANO").sum(),
          "| rurales:", (localidades["ambito"] == "RURAL").sum())
    print("  población total:", localidades["poblacion"].sum())
    print("  guardadas en", config.ARCHIVO_LOCALIDADES)

    print("2. Uso del suelo y vegetación (INEGI, Serie VII)")
    descargar_archivo_grande(config.VEGETACION_URL, config.ARCHIVO_VEGETACION)

    print("3. Áreas naturales protegidas federales (CONANP)")
    descargar_archivo_grande(config.AREAS_PROTEGIDAS_URL, config.ARCHIVO_AREAS_PROTEGIDAS)

    print("Listo: fuentes complementarias descargadas.")


if __name__ == "__main__":
    main()
