# probar_clasificacion.py
# Comprueba con incendios inventados, de resultado conocido, que las reglas de los pasos A y B
# del script 05 clasifican como se espera.
# Lee:     nada (los casos de prueba están escritos aquí mismo).
# Escribe: nada. Si todo está bien, termina con "Todas las pruebas pasaron".
# Uso:     python pruebas/probar_clasificacion.py

import importlib
import sys
from pathlib import Path

# Los scripts viven en la carpeta scripts/. Se agrega a la lista de lugares donde Python busca.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
# El nombre del script empieza con número, así que se importa dando el nombre como texto.
clasificador = importlib.import_module("05_clasificar")


def incendio_base(**cambios):
    """Arma un incendio de prueba: pequeño, forestal, visto una vez y lejos de todo. Se le cambian datos."""
    incendio = {
        "n_puntos": 1, "n_pasadas": 1, "duracion_horas": 0.0, "frp_max": 5.0,
        "fuente_fija": 0, "meses_con_calor": 1, "es_forestal": 1, "vegetacion": "Bosque de encino",
        "en_area_protegida": 0, "area_protegida": "ninguna",
        "dist_localidad_km": 3.0, "nombre_localidad": "Localidad de prueba", "poblacion_localidad": 500,
    }
    incendio.update(cambios)
    return incendio


def probar_paso_a():
    """Paso A: cada regla con un caso que la activa."""
    clasificar = clasificador.clasificar_incendio
    # Regla 1: una fuente fija es falsa alarma aunque sea grande y persistente.
    assert clasificar(incendio_base(fuente_fija=1, meses_con_calor=11, n_pasadas=8, n_puntos=30))["es_real"] == 0
    # Regla 2: forestal y visto en 2 pasadas es real.
    assert clasificar(incendio_base(n_pasadas=2, n_puntos=2))["es_real"] == 1
    # Regla 3: un grupo de 15 puntos es real aunque el terreno no sea forestal.
    assert clasificar(incendio_base(es_forestal=0, n_puntos=15))["es_real"] == 1
    # Regla 4: forestal pero visto una sola vez es probable falsa alarma.
    assert clasificar(incendio_base())["es_real"] == 0
    # Regla 4: no forestal y pequeño es probable falsa alarma, aunque se vea 2 veces.
    assert clasificar(incendio_base(es_forestal=0, n_pasadas=2, n_puntos=3))["es_real"] == 0
    # Una falsa alarma no lleva nivel.
    assert clasificar(incendio_base())["nivel"] == ""
    print("Paso A: 6 casos correctos")


def probar_paso_b():
    """Paso B: el puntaje y el nivel de incendios reales con resultado conocido."""
    clasificar = clasificador.clasificar_incendio
    real = dict(n_pasadas=2)    # con esto pasan el paso A
    # Sin ninguna condición: 0 puntos, nivel bajo.
    resultado = clasificar(incendio_base(**real))
    assert (resultado["puntaje"], resultado["nivel"]) == (0, "bajo")
    # 5 puntos de calor (+1): nivel medio.
    resultado = clasificar(incendio_base(**real, n_puntos=5))
    assert (resultado["puntaje"], resultado["nivel"]) == (1, "medio")
    # 15 puntos (+2) y 30 MW (+1): 3 puntos, nivel alto.
    resultado = clasificar(incendio_base(**real, n_puntos=15, frp_max=30))
    assert (resultado["puntaje"], resultado["nivel"]) == (3, "alto")
    # 40 puntos (+3), 100 MW (+2), 24 h (+1), área protegida (+1) y lejos (+1): 8 puntos, crítico.
    resultado = clasificar(incendio_base(**real, n_puntos=40, frp_max=100, duracion_horas=24,
                                         en_area_protegida=1, area_protegida="La Primavera", dist_localidad_km=4))
    assert (resultado["puntaje"], resultado["nivel"]) == (8, "critico")
    # Justo debajo de cada corte no suma: 4 puntos de calor, 29.9 MW y 23.9 horas dan 0.
    resultado = clasificar(incendio_base(**real, n_puntos=4, frp_max=29.9, duracion_horas=23.9))
    assert (resultado["puntaje"], resultado["nivel"]) == (0, "bajo")
    print("Paso B: 5 casos correctos")


def probar_regla_de_seguridad():
    """Regla de seguridad: cerca de una localidad, el nivel sube al menos a alto."""
    clasificar = clasificador.clasificar_incendio
    # Un incendio pequeño (nivel bajo) a 0.5 km de una localidad sube a alto, y lo explica.
    resultado = clasificar(incendio_base(n_pasadas=2, dist_localidad_km=0.5))
    assert resultado["nivel"] == "alto"
    assert "Regla de seguridad" in resultado["razones"]
    # A 1 km exacto ya no aplica (la regla es "menos de 1 km").
    assert clasificar(incendio_base(n_pasadas=2, dist_localidad_km=1.0))["nivel"] == "bajo"
    # Un incendio crítico cerca de una localidad se queda crítico: la regla nunca baja el nivel.
    resultado = clasificar(incendio_base(n_pasadas=2, n_puntos=40, frp_max=100, dist_localidad_km=0.5))
    assert resultado["nivel"] == "critico"
    # La regla no convierte una falsa alarma en incendio.
    assert clasificar(incendio_base(dist_localidad_km=0.5))["es_real"] == 0
    print("Regla de seguridad: 4 casos correctos")


def main():
    probar_paso_a()
    probar_paso_b()
    probar_regla_de_seguridad()
    print("Todas las pruebas pasaron.")


if __name__ == "__main__":
    main()
