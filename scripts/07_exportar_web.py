# 07_exportar_web.py
# Convierte la tabla de incendios clasificados en los archivos JSON que lee el sitio web:
# uno por año, solo con lo que el mapa necesita mostrar. También copia al sitio los números de
# las reglas (los de config.py), para que el navegador use exactamente los mismos.
# Lee:     datos/procesados/incendios_clasificados.csv     (script 05)
# Escribe: web/datos/incendios_2024.json, web/datos/incendios_2025.json y web/datos/reglas.json
# Uso:     python scripts/07_exportar_web.py

import json
from datetime import date

import pandas as pd

import config


def incendio_para_web(fila):
    """Convierte una fila de la tabla en el diccionario que se guarda en el JSON."""
    coincide = fila["conafor_coincide"] == 1
    return {
        "id": fila["incendio_id"],
        "inicio": fila["inicio"][:16].replace(" ", "T"),     # "2025-04-15 19:42:00" -> "2025-04-15T19:42"
        "fin": fila["fin"][:16].replace(" ", "T"),
        "lat": round(fila["lat"], 4),                        # 4 decimales son unos 11 metros
        "lon": round(fila["lon"], 4),
        "n_puntos": int(fila["n_puntos"]),
        "n_pasadas": int(fila["n_pasadas"]),
        "frp_max": float(fila["frp_max"]),
        "es_real": fila["es_real"] == 1,
        "prob_real": float(fila["prob_real"]),
        # Las falsas alarmas no tienen nivel: en el JSON se escribe null.
        "nivel": fila["nivel"] if fila["es_real"] == 1 else None,
        "razones": fila["razones"].split(" | "),
        "en_piloto": fila["en_piloto"] == 1,
        "conafor": {
            "coincide": bool(coincide),
            "superficie_ha": float(fila["conafor_superficie_ha"]) if coincide else None,
        },
    }


def exportar_anio(incendios, anio):
    """Escribe el archivo JSON de un año y devuelve su ruta."""
    del_anio = incendios[incendios["anio"] == anio].sort_values("inicio")
    contenido = {
        "anio": anio,
        "generado": date.today().isoformat(),
        "metodo": "reglas",
        "incendios": [incendio_para_web(fila) for _, fila in del_anio.iterrows()],
    }
    ruta = config.CARPETA_WEB_DATOS / f"incendios_{anio}.json"
    # separators quita los espacios sobrantes para que el archivo pese menos.
    ruta.write_text(json.dumps(contenido, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return ruta


def exportar_reglas():
    """Escribe los números de las reglas para las páginas "Probar clasificación" y "Plan de ataque"."""
    reglas = {
        "generado": date.today().isoformat(),
        "nota": "Copia de scripts/config.py. No editar a mano: cambiar config.py y correr el script 07.",
        "niveles": config.NIVELES,
        # Paso A
        "pasadas_minimas_real": config.PASADAS_MINIMAS_REAL,
        "puntos_minimos_real": config.PUNTOS_MINIMOS_REAL,
        "prob_real": config.PROB_REAL,
        # Paso B
        "puntos_severidad": config.PUNTOS_SEVERIDAD,
        "frp_severidad": config.FRP_SEVERIDAD,
        "duracion_severidad_h": config.DURACION_SEVERIDAD_H,
        "distancia_lejos_km": config.DISTANCIA_LEJOS_KM,
        "puntaje_minimo_nivel": config.PUNTAJE_MINIMO_NIVEL,
        "distancia_seguridad_km": config.DISTANCIA_SEGURIDAD_KM,
        "nivel_minimo_seguridad": config.NIVEL_MINIMO_SEGURIDAD,
        # Plan de ataque
        "tabla_respuesta": config.TABLA_RESPUESTA,
        "peso_nivel": config.PESO_NIVEL,
    }
    ruta = config.CARPETA_WEB_DATOS / "reglas.json"
    ruta.write_text(json.dumps(reglas, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def main():
    if not config.ARCHIVO_CLASIFICADOS.exists():
        raise SystemExit(f"No se encontró {config.ARCHIVO_CLASIFICADOS}. Corre primero el script 05.")
    config.crear_carpetas()
    # keep_default_na=False: las celdas vacías (nivel de una falsa alarma) se leen como texto vacío.
    incendios = pd.read_csv(config.ARCHIVO_CLASIFICADOS, keep_default_na=False)

    for anio in config.ANIOS:
        ruta = exportar_anio(incendios, anio)
        cuantos = (incendios["anio"] == anio).sum()
        print(f"{ruta.name}: {cuantos} incendios, {ruta.stat().st_size / 1_000_000:.1f} MB")
    print(exportar_reglas().name + ": reglas y tabla de respuesta copiadas de config.py")
    print("Listo: archivos guardados en", config.CARPETA_WEB_DATOS)


if __name__ == "__main__":
    main()
