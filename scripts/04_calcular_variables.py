# 04_calcular_variables.py
# Calcula, para cada incendio candidato, las variables con las que después se clasifica:
# cuántas veces lo vio el satélite, qué tan intenso fue, si es una fuente fija, qué tan cerca
# está de una población, si el terreno es forestal y si cae en un área natural protegida.
# Lee:     datos/procesados/puntos_agrupados.csv        (script 03)
#          datos/procesados/incendios_candidatos.csv    (script 03)
#          datos/referencia/localidades_jalisco.csv     (script 02b)
#          datos/crudos/conabio/usv250s7gw.zip          (script 02b, vegetación)
#          datos/crudos/conabio/anpmx.zip               (script 02b, áreas protegidas)
# Escribe: datos/procesados/incendios_variables.csv
# Uso:     python scripts/04_calcular_variables.py
#
# Pendiente: las variables de clima (Sprint 2).

import geopandas as gpd
import pandas as pd

import config


def contar_pasadas(puntos):
    """Cuenta en cuántas pasadas de satélite distintas se detectó cada incendio."""
    # Se ordenan los puntos de cada incendio y satélite por hora. Empieza una pasada nueva
    # cuando es el primer punto, o cuando pasaron más de 30 minutos desde el punto anterior.
    puntos = puntos.sort_values(["incendio_id", "satelite", "fecha_hora_utc"])
    espera = puntos.groupby(["incendio_id", "satelite"])["fecha_hora_utc"].diff()
    pasada_nueva = espera.isna() | (espera > pd.Timedelta(minutes=config.MINUTOS_MISMA_PASADA))
    return pasada_nueva.groupby(puntos["incendio_id"]).sum()


def variables_del_satelite(puntos):
    """Resume los puntos de calor de cada incendio: persistencia, intensidad, confianza y horario."""
    grupos = puntos.groupby("incendio_id")
    duracion = grupos["fecha_hora_utc"].max() - grupos["fecha_hora_utc"].min()
    return pd.DataFrame({
        "n_pasadas": contar_pasadas(puntos),
        "duracion_horas": (duracion.dt.total_seconds() / 3600).round(1),
        "frp_max": grupos["frp"].max().round(1),            # punto más intenso (MW)
        "frp_total": grupos["frp"].sum().round(1),          # suma de todos sus puntos (MW)
        "confianza_media": grupos["confianza"].mean().round(2),
        "fraccion_nocturna": (puntos["dia_noche"] == "N").groupby(puntos["incendio_id"]).mean().round(2),
        "fraccion_puntos_fijos": (puntos["tipo_fuente"] == 2).groupby(puntos["incendio_id"]).mean().round(2),
    })


def cuadro_de(tabla):
    """Devuelve el cuadro de 1 km en el que cae cada fila, como texto (por ejemplo "669_2175")."""
    cuadro_x = (tabla["x"] // config.CUADRO_FUENTE_FIJA_M).astype(int).astype(str)
    cuadro_y = (tabla["y"] // config.CUADRO_FUENTE_FIJA_M).astype(int).astype(str)
    return cuadro_x + "_" + cuadro_y


def meses_con_calor(puntos):
    """Cuenta en cuántos meses distintos del año hubo puntos de calor en el lugar de cada incendio."""
    puntos = puntos.assign(cuadro=cuadro_de(puntos), mes=puntos["fecha_hora_local"].dt.month,
                           anio_local=puntos["fecha_hora_local"].dt.year)
    # A cada punto se le anota en cuántos meses de ese año hubo calor en su cuadro de 1 km.
    meses_del_cuadro = puntos.groupby(["cuadro", "anio_local"])["mes"].transform("nunique")
    # Un incendio grande toca muchos cuadros. Se toma la mediana de sus puntos para que un solo
    # cuadro con una fuente fija no marque a todo el incendio.
    return meses_del_cuadro.groupby(puntos["incendio_id"]).median().round().astype(int)


def localidad_mas_cercana(incendios, localidades):
    """Busca, para cada incendio, la localidad con población suficiente que le queda más cerca."""
    pobladas = localidades[localidades["poblacion"] >= config.POBLACION_MINIMA_LOCALIDAD]
    # Se trabaja en metros (UTM 13N) para que la distancia salga en metros.
    geo_incendios = gpd.GeoDataFrame(incendios[["incendio_id"]],
                                     geometry=gpd.points_from_xy(incendios["x"], incendios["y"]), crs=config.CRS_METROS)
    geo_localidades = gpd.GeoDataFrame(pobladas[["nombre", "poblacion"]],
                                       geometry=gpd.points_from_xy(pobladas["x"], pobladas["y"]), crs=config.CRS_METROS)
    cercanas = gpd.sjoin_nearest(geo_incendios, geo_localidades, distance_col="distancia_m")
    # Si dos localidades quedan exactamente a la misma distancia, se toma la primera.
    cercanas = cercanas.drop_duplicates("incendio_id").set_index("incendio_id")
    return pd.DataFrame({
        "dist_localidad_km": (cercanas["distancia_m"] / 1000).round(2),
        "poblacion_localidad": cercanas["poblacion"],
        "nombre_localidad": cercanas["nombre"],
    })


def leer_mapa(archivo_zip, capa):
    """Lee de un .zip solo la parte del mapa que cae en la caja de Jalisco, y la pasa a metros."""
    caja = (config.JALISCO_OESTE, config.JALISCO_SUR, config.JALISCO_ESTE, config.JALISCO_NORTE)
    mapa = gpd.read_file(f"zip://{archivo_zip}!{capa}", bbox=caja, encoding="utf-8")
    return mapa.to_crs(config.CRS_METROS)


def puntos_de_incendios(incendios):
    """Convierte la tabla de incendios en puntos (el centro de cada uno), en metros."""
    geometria = gpd.points_from_xy(incendios["x"], incendios["y"])
    return gpd.GeoDataFrame(incendios[["incendio_id"]], geometry=geometria, crs=config.CRS_METROS)


def vegetacion_del_lugar(incendios):
    """Busca el tipo de vegetación en el centro de cada incendio y dice si es forestal."""
    vegetacion = leer_mapa(config.ARCHIVO_VEGETACION, config.VEGETACION_CAPA)[["DESCRIPCIO", "geometry"]]
    # sjoin pega a cada incendio el polígono de vegetación en el que cae su centro.
    cruce = gpd.sjoin(puntos_de_incendios(incendios), vegetacion, how="left", predicate="within")
    cruce = cruce.drop_duplicates("incendio_id").set_index("incendio_id")
    tipo = cruce["DESCRIPCIO"].fillna("SIN DATO")
    # Es forestal si su tipo NO empieza con ninguno de los usos no forestales de config.
    no_forestal = tipo.str.startswith(config.USOS_NO_FORESTALES) | (tipo == "SIN DATO")
    return pd.DataFrame({"vegetacion": tipo.str.capitalize(), "es_forestal": (~no_forestal).astype(int)})


def area_protegida_del_lugar(incendios):
    """Dice si el centro de cada incendio cae dentro de un área natural protegida federal, y en cuál."""
    areas = leer_mapa(config.ARCHIVO_AREAS_PROTEGIDAS, config.AREAS_PROTEGIDAS_CAPA)[["NOMBRE", "geometry"]]
    cruce = gpd.sjoin(puntos_de_incendios(incendios), areas, how="left", predicate="within")
    cruce = cruce.drop_duplicates("incendio_id").set_index("incendio_id")
    return pd.DataFrame({
        "en_area_protegida": cruce["NOMBRE"].notna().astype(int),
        "area_protegida": cruce["NOMBRE"].fillna("ninguna"),
    })


def esta_en_piloto(incendios):
    """Dice si el centro del incendio cae dentro de la región piloto (1) o no (0)."""
    dentro = (incendios["lon"].between(config.PILOTO_OESTE, config.PILOTO_ESTE)
              & incendios["lat"].between(config.PILOTO_SUR, config.PILOTO_NORTE))
    return dentro.astype(int)


def mostrar_resumen(incendios):
    """Imprime un resumen de las variables para revisarlas a simple vista."""
    print("Incendios con variables:", len(incendios))
    print("  detectados en 2 o más pasadas:", (incendios["n_pasadas"] >= 2).sum())
    print("  marcados como fuente fija:    ", incendios["fuente_fija"].sum())
    print("  a menos de 2 km de una localidad:", (incendios["dist_localidad_km"] < 2).sum())
    print("  en terreno forestal:          ", incendios["es_forestal"].sum())
    print("  en área natural protegida:    ", incendios["en_area_protegida"].sum())
    print("  en la región piloto:          ", incendios["en_piloto"].sum())
    columnas = ["n_puntos", "n_pasadas", "duracion_horas", "frp_max", "dist_localidad_km"]
    print(incendios[columnas].describe().loc[["mean", "50%", "max"]].round(1).to_string())


def main():
    necesarios = [config.ARCHIVO_PUNTOS_AGRUPADOS, config.ARCHIVO_CANDIDATOS, config.ARCHIVO_LOCALIDADES,
                  config.ARCHIVO_VEGETACION, config.ARCHIVO_AREAS_PROTEGIDAS]
    for archivo in necesarios:
        if not archivo.exists():
            raise SystemExit(f"No se encontró {archivo}. Corre primero los scripts 02b y 03.")
    puntos = pd.read_csv(config.ARCHIVO_PUNTOS_AGRUPADOS, parse_dates=["fecha_hora_utc", "fecha_hora_local"])
    incendios = pd.read_csv(config.ARCHIVO_CANDIDATOS)
    localidades = pd.read_csv(config.ARCHIVO_LOCALIDADES)

    # Cada grupo de variables se calcula por separado y se pega a la tabla de incendios.
    incendios = incendios.join(variables_del_satelite(puntos), on="incendio_id")
    incendios = incendios.join(meses_con_calor(puntos).rename("meses_con_calor"), on="incendio_id")
    es_fija = ((incendios["fraccion_puntos_fijos"] >= config.FRACCION_PUNTOS_FIJOS)
               | (incendios["meses_con_calor"] >= config.MESES_FUENTE_FIJA))
    incendios["fuente_fija"] = es_fija.astype(int)
    incendios = incendios.join(localidad_mas_cercana(incendios, localidades), on="incendio_id")
    incendios = incendios.join(vegetacion_del_lugar(incendios), on="incendio_id")
    incendios = incendios.join(area_protegida_del_lugar(incendios), on="incendio_id")
    incendios["en_piloto"] = esta_en_piloto(incendios)

    incendios.to_csv(config.ARCHIVO_VARIABLES, index=False)
    mostrar_resumen(incendios)
    print("Listo: guardado en", config.ARCHIVO_VARIABLES)


if __name__ == "__main__":
    main()
