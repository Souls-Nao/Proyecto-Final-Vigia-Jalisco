# probar_agrupamiento.py
# Comprueba con un caso pequeño, hecho a mano, que el agrupamiento del script 03 hace lo esperado.
# Lee:     nada (los puntos de prueba están escritos aquí mismo).
# Escribe: nada. Si todo está bien, termina con "Todas las pruebas pasaron".
# Uso:     python pruebas/probar_agrupamiento.py

import importlib
import sys
from pathlib import Path

import pandas as pd

# Los scripts viven en la carpeta scripts/. Se agrega a la lista de lugares donde Python busca.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
# El nombre del script empieza con número, así que no se puede escribir "import 03_agrupar…".
# import_module hace lo mismo recibiendo el nombre como texto.
agrupar = importlib.import_module("03_agrupar_incendios")


def punto(x, y, fecha_hora):
    """Arma un punto de calor de prueba con las columnas que usa el agrupamiento."""
    momento = pd.Timestamp(fecha_hora)
    return {"x": x, "y": y, "lat": 20.0, "lon": -103.0,
            "fecha_hora_utc": momento, "fecha_hora_local": momento - pd.Timedelta(hours=6)}


def preparar_caso():
    """Seis puntos inventados que forman tres incendios (ver los comentarios de cada uno)."""
    return pd.DataFrame([
        # Incendio A: dos puntos a 300 m, con 2 horas de diferencia.
        punto(500000, 2200000, "2025-04-10 20:00"),
        punto(500300, 2200000, "2025-04-10 22:00"),
        # Incendio B: a 50 km del A, el mismo día. Dura varios días: tres puntos a 400 m,
        # cada uno 24 horas después del anterior.
        punto(550000, 2200000, "2025-04-10 20:00"),
        punto(550400, 2200000, "2025-04-11 20:00"),
        punto(550800, 2200000, "2025-04-12 20:00"),
        # Incendio C: en el mismo lugar que el A, pero un mes después.
        punto(500000, 2200000, "2025-05-10 20:00"),
    ])


def main():
    puntos = agrupar.poner_identificadores(agrupar.agrupar_puntos(preparar_caso()))
    ids = puntos["incendio_id"].tolist()
    print("Identificadores asignados:", ids)

    # 1. Deben salir exactamente tres incendios.
    assert len(set(ids)) == 3, "Se esperaban 3 incendios"
    # 2. Los dos puntos cercanos en distancia y tiempo son el mismo incendio (A).
    assert ids[0] == ids[1], "Los puntos del incendio A deberían estar juntos"
    # 3. Dos incendios lejanos el mismo día no se mezclan (A y B).
    assert ids[0] != ids[2], "Los incendios A y B no deberían mezclarse"
    # 4. Un incendio que dura varios días sigue siendo uno solo (B).
    assert ids[2] == ids[3] == ids[4], "El incendio B debería ser uno solo aunque dure 3 días"
    # 5. El mismo lugar un mes después es otro incendio (C). Este era el problema P10.
    assert ids[0] != ids[5], "El mismo lugar un mes después debería ser otro incendio"
    # 6. Los identificadores van por año y por orden de inicio.
    assert ids[0] == "2025-0001" and ids[5] == "2025-0003", "La numeración no va en orden de inicio"

    incendios = agrupar.resumir_incendios(puntos)
    assert incendios["n_puntos"].tolist() == [2, 3, 1], "El conteo de puntos por incendio no coincide"

    print("Todas las pruebas pasaron.")


if __name__ == "__main__":
    main()
