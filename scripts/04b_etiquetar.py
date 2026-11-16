# 04b_etiquetar.py
# Cruza los incendios candidatos con los registros de CONAFOR para saber cuáles coinciden con un
# incendio registrado ("real") y de qué tamaño fue. Esas son las ETIQUETAS: sirven para ajustar
# las reglas con 2024 y para comprobar con 2025 qué tan bien clasifican.
# Lee:     datos/procesados/incendios_variables.csv            (script 04)
#          datos/procesados/incendios_conafor_jalisco.geojson  (script 02)
# Escribe: datos/procesados/incendios_etiquetados.csv
# Uso:     python scripts/04b_etiquetar.py

import geopandas as gpd
import pandas as pd

import config


def leer_registros():
    """Lee los polígonos de CONAFOR, los repara y los pasa a metros."""
    registros = gpd.read_file(config.ARCHIVO_CONAFOR_POLIGONOS)
    registros["geometry"] = registros.geometry.make_valid()
    registros["fecha_inicio"] = pd.to_datetime(registros["fecha_inicio"])
    registros["fecha_fin"] = pd.to_datetime(registros["fecha_fin"])
    return registros.to_crs(config.CRS_METROS)


def pares_cercanos(incendios, registros):
    """Arma las parejas candidato-registro que quedan a la distancia de tolerancia o menos."""
    centros = gpd.GeoDataFrame(incendios[["incendio_id", "inicio", "fin"]],
                               geometry=gpd.points_from_xy(incendios["x"], incendios["y"]), crs=config.CRS_METROS)
    # Se dibuja un círculo de 1 km alrededor de cada candidato y se ve qué polígonos toca.
    circulos = centros.copy()
    circulos["geometry"] = centros.geometry.buffer(config.TOLERANCIA_KM * 1000)
    pares = gpd.sjoin(circulos, registros, predicate="intersects")
    # Distancia real del centro del candidato al polígono (0 si está adentro).
    poligonos = registros.geometry.loc[pares["index_right"]]
    pares["distancia_m"] = centros.geometry.loc[pares.index].distance(poligonos, align=False).values
    return pares


def dias_de_separacion(pares):
    """Días entre las fechas del candidato y las del registro; 0 si se traslapan."""
    primer_dia = pares["inicio"].dt.normalize()     # normalize quita la hora y deja solo el día
    ultimo_dia = pares["fin"].dt.normalize()
    dias_antes = (pares["fecha_inicio"] - ultimo_dia).dt.days.clip(lower=0)   # terminó antes del registro
    dias_despues = (primer_dia - pares["fecha_fin"]).dt.days.clip(lower=0)    # empezó después de liquidado
    return dias_antes + dias_despues


def nivel_por_superficie(superficie_ha):
    """Convierte la superficie quemada en el nivel real: bajo, medio, alto o critico."""
    posicion = sum(superficie_ha >= corte for corte in config.CORTES_SEVERIDAD_HA)
    return config.NIVELES[posicion]


def etiquetar(incendios, registros):
    """Agrega a cada candidato si coincide con un registro de CONAFOR, con cuál y su nivel real."""
    pares = pares_cercanos(incendios, registros)
    pares = pares[dias_de_separacion(pares) <= config.TOLERANCIA_DIAS]
    # Si un candidato coincide con varios registros, se queda con el más cercano.
    mejores = pares.sort_values("distancia_m").drop_duplicates("incendio_id").set_index("incendio_id")
    etiquetas = pd.DataFrame({
        "conafor_id": mejores["id_conafor"],
        "conafor_superficie_ha": mejores["superficie_ha"],
        "nivel_real": mejores["superficie_ha"].apply(nivel_por_superficie),
    })
    incendios = incendios.join(etiquetas, on="incendio_id")
    incendios["conafor_coincide"] = incendios["conafor_id"].notna().astype(int)
    return incendios


def mostrar_resumen(incendios, registros):
    """Imprime cuántos candidatos coinciden y cuántos registros de CONAFOR vio el satélite."""
    for anio in config.ANIOS:
        del_anio = incendios[incendios["anio"] == anio]
        reales = del_anio[del_anio["conafor_coincide"] == 1]
        registros_del_anio = (registros["anio"] == anio).sum()
        print(f"{anio}: {len(del_anio)} candidatos, {len(reales)} coinciden con CONAFOR "
              f"({100 * len(reales) / len(del_anio):.1f} %)")
        print(f"      registros de CONAFOR con al menos un candidato: "
              f"{reales['conafor_id'].nunique()} de {registros_del_anio}")
        print("      nivel real de los que coinciden:", reales["nivel_real"].value_counts().reindex(config.NIVELES).to_dict())


def main():
    for archivo in [config.ARCHIVO_VARIABLES, config.ARCHIVO_CONAFOR_POLIGONOS]:
        if not archivo.exists():
            raise SystemExit(f"No se encontró {archivo}. Corre primero los scripts 02 y 04.")
    incendios = pd.read_csv(config.ARCHIVO_VARIABLES, parse_dates=["inicio", "fin"])
    registros = leer_registros()

    incendios = etiquetar(incendios, registros)
    incendios.to_csv(config.ARCHIVO_ETIQUETADOS, index=False)

    mostrar_resumen(incendios, registros)
    print("Listo: guardado en", config.ARCHIVO_ETIQUETADOS)


if __name__ == "__main__":
    main()
