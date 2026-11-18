# medir_agrupamiento.py
# Mide cuánto tardan el agrupamiento (DBSCAN, script 03) y la clasificación por reglas (script 05)
# cuando crece la cantidad de datos, para comprobar con datos reales su complejidad aproximada.
# Lee:     datos/procesados/puntos_calor_jalisco.csv     (script 01)
#          datos/procesados/incendios_etiquetados.csv    (script 04b)
# Escribe: reportes/tiempos_agrupamiento.csv
# Uso:     python scripts/medir_agrupamiento.py          (tarda menos de un minuto)

import importlib
import math
import time

import pandas as pd

import config

# Los scripts empiezan con número, así que se importan dando el nombre como texto.
agrupamiento = importlib.import_module("03_agrupar_incendios")
clasificacion = importlib.import_module("05_clasificar")

# Tamaños que se prueban: de 1/16 de los datos reales a todos. Cada uno es el doble del anterior,
# así se ve cuánto crece el tiempo cuando los datos se duplican.
FRACCIONES = [1 / 16, 1 / 8, 1 / 4, 1 / 2, 1]
# Cada medición se repite y se toma el tiempo más bajo: es el que menos afectan otros programas.
REPETICIONES = 3
# Semilla fija para que las muestras sean las mismas cada vez que se corre.
SEMILLA = 2026


def medir_una_vez(funcion, datos):
    """Corre la función varias veces con los mismos datos y devuelve el tiempo más bajo, en milisegundos."""
    mejor = None
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        funcion(datos)
        transcurrido = (time.perf_counter() - inicio) * 1000
        if mejor is None or transcurrido < mejor:
            mejor = transcurrido
    return mejor


def medir_algoritmo(nombre, funcion, tabla):
    """Mide un algoritmo con muestras de tamaño creciente. Devuelve una lista de diccionarios."""
    filas = []
    for fraccion in FRACCIONES:
        muestra = tabla.sample(frac=fraccion, random_state=SEMILLA)
        milisegundos = medir_una_vez(funcion, muestra)
        filas.append({"algoritmo": nombre, "n": len(muestra), "milisegundos": round(milisegundos, 1)})
        print(f"  {nombre}: n = {len(muestra):>6}  ->  {milisegundos:8.1f} ms")
    return filas


def crecimiento(filas):
    """Calcula k tal que el tiempo crece como n^k, con los dos tamaños más grandes.
    k cerca de 1 = crece como n; un poco más de 1 = n log n; cerca de 2 = n²."""
    chica, grande = filas[-2], filas[-1]
    return math.log(grande["milisegundos"] / chica["milisegundos"]) / math.log(grande["n"] / chica["n"])


def main():
    for archivo in [config.ARCHIVO_PUNTOS_CALOR, config.ARCHIVO_ETIQUETADOS]:
        if not archivo.exists():
            raise SystemExit(f"No se encontró {archivo}. Corre primero los scripts 01 a 04b.")
    puntos = pd.read_csv(config.ARCHIVO_PUNTOS_CALOR, parse_dates=["fecha_hora_utc", "fecha_hora_local"])
    incendios = pd.read_csv(config.ARCHIVO_ETIQUETADOS)

    print("Midiendo (el tiempo más bajo de", REPETICIONES, "repeticiones):")
    filas_dbscan = medir_algoritmo("dbscan", agrupamiento.agrupar_puntos, puntos)
    filas_reglas = medir_algoritmo("reglas", clasificacion.clasificar, incendios)

    config.CARPETA_REPORTES.mkdir(parents=True, exist_ok=True)
    ruta = config.CARPETA_REPORTES / "tiempos_agrupamiento.csv"
    pd.DataFrame(filas_dbscan + filas_reglas).to_csv(ruta, index=False)

    print("Al duplicar los datos, el tiempo crece como n^k:")
    print(f"  DBSCAN (n = puntos de calor): k = {crecimiento(filas_dbscan):.2f}")
    print(f"  Reglas (n = incendios candidatos): k = {crecimiento(filas_reglas):.2f}")
    print("Listo: guardado en", ruta)


if __name__ == "__main__":
    main()
