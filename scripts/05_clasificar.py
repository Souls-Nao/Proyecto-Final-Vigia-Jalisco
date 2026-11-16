# 05_clasificar.py
# Clasifica cada incendio candidato en dos pasos:
#   Paso A: ¿es un incendio real o una probable falsa alarma?
#   Paso B: si es real, ¿qué nivel de severidad tiene? (bajo, medio, alto o critico)
# Además guarda las RAZONES de cada decisión, para que la herramienta pueda explicarla.
# Por ahora el único método es "reglas"; el método "bosque" (bosque aleatorio) llega en el Sprint 2.
# Lee:     datos/procesados/incendios_etiquetados.csv     (script 04b)
# Escribe: datos/procesados/incendios_clasificados.csv
# Uso:     python scripts/05_clasificar.py

import pandas as pd

import config


def paso_a_reglas(incendio):
    """Decide si un incendio es real. Devuelve (es_real, nombre de la regla, razón en palabras)."""
    if incendio["fuente_fija"] == 1:
        razon = f"Fuente fija: el lugar tuvo puntos de calor en {incendio['meses_con_calor']} meses del año"
        return 0, "fuente_fija", razon
    if incendio["es_forestal"] == 1 and incendio["n_pasadas"] >= config.PASADAS_MINIMAS_REAL:
        razon = f"Terreno forestal ({incendio['vegetacion']}) y visto en {incendio['n_pasadas']} pasadas de satélite"
        return 1, "forestal_persistente", razon
    if incendio["n_puntos"] >= config.PUNTOS_MINIMOS_REAL:
        return 1, "grupo_grande", f"Grupo grande: {incendio['n_puntos']} puntos de calor"
    if incendio["es_forestal"] == 1:
        return 0, "forestal_una_pasada", "Terreno forestal, pero visto en una sola pasada de satélite"
    return 0, "no_forestal", f"Terreno no forestal ({incendio['vegetacion']})"


def puntaje_severidad(incendio):
    """Suma los puntos de severidad de un incendio. Devuelve (puntaje, lista de razones)."""
    puntaje = 0
    razones = []
    # Tamaño: +1, +2 o +3 según cuántos puntos de calor tiene.
    puntos = sum(incendio["n_puntos"] >= corte for corte in config.PUNTOS_SEVERIDAD)
    if puntos > 0:
        puntaje += puntos
        razones.append(f"{incendio['n_puntos']} puntos de calor (+{puntos})")
    # Intensidad: +1 o +2 según su punto más fuerte.
    puntos = sum(incendio["frp_max"] >= corte for corte in config.FRP_SEVERIDAD)
    if puntos > 0:
        puntaje += puntos
        razones.append(f"Intensidad máxima de {incendio['frp_max']:.0f} MW (+{puntos})")
    if incendio["duracion_horas"] >= config.DURACION_SEVERIDAD_H:
        puntaje += 1
        razones.append(f"Duró {incendio['duracion_horas']:.0f} horas (+1)")
    if incendio["en_area_protegida"] == 1:
        puntaje += 1
        razones.append(f"Dentro del área natural protegida {incendio['area_protegida']} (+1)")
    if incendio["dist_localidad_km"] >= config.DISTANCIA_LEJOS_KM:
        puntaje += 1
        razones.append(f"Lejos de poblaciones: a {incendio['dist_localidad_km']:.1f} km de la más cercana (+1)")
    return puntaje, razones


def nivel_por_puntaje(puntaje):
    """Convierte el puntaje en nivel: 0 bajo, 1-2 medio, 3-4 alto, 5 o más critico."""
    posicion = sum(puntaje >= minimo for minimo in config.PUNTAJE_MINIMO_NIVEL)
    return config.NIVELES[posicion]


def aplicar_regla_seguridad(nivel, incendio):
    """Si el incendio está muy cerca de una localidad, sube al menos a nivel alto."""
    cerca = incendio["dist_localidad_km"] < config.DISTANCIA_SEGURIDAD_KM
    es_menor = config.NIVELES.index(nivel) < config.NIVELES.index(config.NIVEL_MINIMO_SEGURIDAD)
    if cerca and es_menor:
        razon = (f"Regla de seguridad: a {incendio['dist_localidad_km']:.1f} km de {incendio['nombre_localidad']} "
                 f"({incendio['poblacion_localidad']:,} hab.), sube a nivel {config.NIVEL_MINIMO_SEGURIDAD}")
        return config.NIVEL_MINIMO_SEGURIDAD, razon
    return nivel, None


def clasificar_incendio(incendio):
    """Clasifica un incendio con las reglas de los pasos A y B. Devuelve un diccionario."""
    es_real, regla, razon = paso_a_reglas(incendio)
    resultado = {"es_real": es_real, "prob_real": config.PROB_REAL[regla], "nivel": "", "puntaje": 0}
    razones = [razon]
    # El paso B solo se aplica a los incendios que el paso A considera reales.
    if es_real == 1:
        puntaje, razones_severidad = puntaje_severidad(incendio)
        nivel, razon_seguridad = aplicar_regla_seguridad(nivel_por_puntaje(puntaje), incendio)
        razones += razones_severidad
        if razon_seguridad:
            razones.append(razon_seguridad)
        resultado["nivel"] = nivel
        resultado["puntaje"] = puntaje
    # Las razones se guardan en una sola celda, separadas por " | ".
    resultado["razones"] = " | ".join(razones)
    return resultado


def clasificar(incendios, metodo="reglas"):
    """Clasifica todos los incendios con el método indicado y devuelve la tabla con el resultado."""
    if metodo != "reglas":
        raise SystemExit(f'El método "{metodo}" todavía no existe. Por ahora solo está "reglas".')
    resultados = incendios.apply(clasificar_incendio, axis=1, result_type="expand")
    return pd.concat([incendios, resultados], axis=1)


def comparar_con_conafor(incendios, anio):
    """Compara la clasificación de un año con las etiquetas de CONAFOR e imprime las cuentas."""
    datos = incendios[incendios["anio"] == anio]
    aciertos = ((datos["es_real"] == 1) & (datos["conafor_coincide"] == 1)).sum()
    dichos_reales = (datos["es_real"] == 1).sum()
    registrados = (datos["conafor_coincide"] == 1).sum()
    print(f"{anio} · paso A: de {dichos_reales} clasificados como reales, {aciertos} coinciden con CONAFOR "
          f"(precisión {aciertos / dichos_reales:.2f}); de {registrados} que coinciden con CONAFOR, "
          f"se encontraron {aciertos} (sensibilidad {aciertos / registrados:.2f})")
    # Paso B: solo en los que son reales para las reglas Y tienen nivel real conocido.
    ambos = datos[(datos["es_real"] == 1) & (datos["conafor_coincide"] == 1)]
    posicion_dicha = ambos["nivel"].apply(config.NIVELES.index)
    posicion_real = ambos["nivel_real"].apply(config.NIVELES.index)
    print(f"{anio} · paso B: en {len(ambos)} incendios, mismo nivel {(posicion_dicha == posicion_real).mean():.2f}; "
          f"mismo nivel o uno de diferencia {((posicion_dicha - posicion_real).abs() <= 1).mean():.2f}")


def main():
    if not config.ARCHIVO_ETIQUETADOS.exists():
        raise SystemExit(f"No se encontró {config.ARCHIVO_ETIQUETADOS}. Corre primero el script 04b.")
    incendios = pd.read_csv(config.ARCHIVO_ETIQUETADOS)

    incendios = clasificar(incendios, metodo="reglas")
    incendios.to_csv(config.ARCHIVO_CLASIFICADOS, index=False)

    reales = incendios[incendios["es_real"] == 1]
    print("Candidatos:", len(incendios), "| clasificados como reales:", len(reales))
    print("Reales por año y nivel:")
    print(reales.groupby(["anio", "nivel"]).size().unstack()[config.NIVELES].to_string())
    print("Comparación rápida con CONAFOR (2024 se usó para ajustar; 2025 es la prueba):")
    for anio in config.ANIOS:
        comparar_con_conafor(incendios, anio)
    print("Listo: guardado en", config.ARCHIVO_CLASIFICADOS)


if __name__ == "__main__":
    main()
