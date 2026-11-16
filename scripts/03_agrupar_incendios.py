# 03_agrupar_incendios.py
# Junta los puntos de calor cercanos (en distancia y en tiempo) en "incendios candidatos".
# Un incendio produce muchos puntos de calor; aquí se decide cuáles pertenecen al mismo incendio.
# Lee:     datos/procesados/puntos_calor_jalisco.csv      (lo escribe el script 01)
# Escribe: datos/procesados/puntos_agrupados.csv          (cada punto con el incendio al que pertenece)
#          datos/procesados/incendios_candidatos.csv      (una fila por incendio candidato)
# Uso:     python scripts/03_agrupar_incendios.py

import pandas as pd
from sklearn.cluster import DBSCAN

import config


def agrupar_puntos(puntos):
    """Asigna a cada punto el número de grupo (incendio candidato) al que pertenece."""
    # DBSCAN mide distancias entre números de la misma escala. Por eso el tiempo se pasa a
    # horas y luego a "metros": con los valores de config, 48 horas pesan igual que 1,000 m.
    horas = (puntos["fecha_hora_utc"] - puntos["fecha_hora_utc"].min()).dt.total_seconds() / 3600
    horas_como_metros = horas * config.METROS_POR_HORA
    coordenadas = list(zip(puntos["x"], puntos["y"], horas_como_metros))
    # min_samples=1: un punto solo también cuenta como grupo (puede ser un incendio pequeño).
    modelo = DBSCAN(eps=config.DISTANCIA_MAXIMA_M, min_samples=1)
    puntos = puntos.copy()
    puntos["grupo"] = modelo.fit_predict(coordenadas)
    return puntos


def poner_identificadores(puntos):
    """Cambia el número de grupo por un identificador como 2025-0412 (año y número por orden de inicio)."""
    inicio = puntos.groupby("grupo")["fecha_hora_local"].min().sort_values()
    anio = inicio.dt.year
    # cumcount numera los grupos dentro de cada año: 1, 2, 3… en el orden en que empezaron.
    numero = anio.groupby(anio).cumcount() + 1
    identificadores = anio.astype(str) + "-" + numero.astype(str).str.zfill(4)
    puntos["incendio_id"] = puntos["grupo"].map(identificadores)
    return puntos.drop(columns="grupo")


def resumir_incendios(puntos):
    """Arma la tabla de incendios candidatos: una fila por incendio, con su centro y sus fechas."""
    grupos = puntos.groupby("incendio_id")
    incendios = pd.DataFrame({
        "anio": grupos["fecha_hora_local"].min().dt.year,
        "inicio": grupos["fecha_hora_local"].min(),      # primera detección (hora local)
        "fin": grupos["fecha_hora_local"].max(),         # última detección (hora local)
        "lat": grupos["lat"].mean().round(5),            # centro: promedio de sus puntos
        "lon": grupos["lon"].mean().round(5),
        "x": grupos["x"].mean().round(1),
        "y": grupos["y"].mean().round(1),
        "n_puntos": grupos.size(),
    })
    return incendios.reset_index()


def mostrar_resumen(incendios):
    """Imprime cuántos incendios candidatos salieron y de qué tamaño, para revisar a simple vista."""
    print("Incendios candidatos por año:")
    print(incendios.groupby("anio").size().to_string())
    print("Puntos de calor por incendio:")
    print("  con 1 punto:        ", (incendios["n_puntos"] == 1).sum())
    print("  con 2 a 4 puntos:   ", incendios["n_puntos"].between(2, 4).sum())
    print("  con 5 a 14 puntos:  ", incendios["n_puntos"].between(5, 14).sum())
    print("  con 15 a 39 puntos: ", incendios["n_puntos"].between(15, 39).sum())
    print("  con 40 o más puntos:", (incendios["n_puntos"] >= 40).sum())


def main():
    if not config.ARCHIVO_PUNTOS_CALOR.exists():
        raise SystemExit(f"No se encontró {config.ARCHIVO_PUNTOS_CALOR}. Corre primero el script 01.")
    puntos = pd.read_csv(config.ARCHIVO_PUNTOS_CALOR, parse_dates=["fecha_hora_utc", "fecha_hora_local"])
    print("Puntos de calor leídos:", len(puntos))

    puntos = poner_identificadores(agrupar_puntos(puntos))
    incendios = resumir_incendios(puntos)

    puntos.to_csv(config.ARCHIVO_PUNTOS_AGRUPADOS, index=False)
    incendios.to_csv(config.ARCHIVO_CANDIDATOS, index=False)

    mostrar_resumen(incendios)
    print("Listo:", len(incendios), "incendios candidatos guardados en", config.ARCHIVO_CANDIDATOS)


if __name__ == "__main__":
    main()
