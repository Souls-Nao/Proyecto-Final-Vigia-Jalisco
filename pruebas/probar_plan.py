# probar_plan.py
# Comprueba el reparto de brigadas con un caso pequeño cuyo resultado se calculó a mano.
# Es el MISMO caso que está al final de web/js/plan.js (función casoDePrueba): si los dos dan lo
# mismo, el plan del navegador y el de Python coinciden.
# Lee:     nada (el caso está escrito aquí mismo).
# Escribe: nada. Si todo está bien, termina con "Todas las pruebas pasaron".
# Uso:     python pruebas/probar_plan.py

import sys
from pathlib import Path

# Los scripts viven en la carpeta scripts/. Se agrega a la lista de lugares donde Python busca.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import plan_ataque

BASES = {"B1": {"lat": 20.0, "lon": -103.0}, "B2": {"lat": 20.0, "lon": -103.5}}
BRIGADAS = [
    {"id": "BR1", "base": "B1", "tipo": "terrestre"}, {"id": "BR2", "base": "B1", "tipo": "terrestre"},
    {"id": "BR3", "base": "B2", "tipo": "terrestre"}, {"id": "BR4", "base": "B2", "tipo": "terrestre"},
]
# I3 se detectó primero; I1 e I2 son de nivel medio (piden 2 brigadas) e I3 es bajo (pide 1).
INCENDIOS = [
    {"id": "I1", "nivel": "medio", "inicio": "2025-04-15T12:00", "lat": 20.0, "lon": -103.2},
    {"id": "I2", "nivel": "medio", "inicio": "2025-04-15T13:00", "lat": 20.0, "lon": -103.3},
    {"id": "I3", "nivel": "bajo", "inicio": "2025-04-15T11:00", "lat": 20.0, "lon": -103.1},
]
# Desde B2, el camino a I2 es muy lento (40 min) aunque en línea recta quede cerca.
TIEMPOS = {"I1": {"B1": 10, "B2": 12}, "I2": {"B1": 11, "B2": 40}, "I3": {"B1": 5, "B2": 6}}


def resumen(plan):
    """Convierte las asignaciones en textos como "BR1>I1:10" para compararlas fácil."""
    return " ".join(f"{a['brigada']}>{a['incendio']}:{a['minutos']}" for a in plan["asignaciones"])


def probar_orden():
    """Los dos incendios medios van primero (I1 se alcanza en 10 min, I2 en 11) y luego el bajo."""
    orden = [i["id"] for i in plan_ataque.orden_de_atencion(INCENDIOS, TIEMPOS)]
    assert orden == ["I1", "I2", "I3"], orden
    print("Orden de atención: correcto")


def probar_voraz():
    """I1 toma las dos brigadas de B1 (10 min); a I2 le quedan las de B2 (40 min); I3 se queda sin brigada."""
    plan = plan_ataque.generar_plan(INCENDIOS, BRIGADAS, BASES, TIEMPOS, metodo="voraz")
    assert resumen(plan) == "BR1>I1:10 BR2>I1:10 BR3>I2:40 BR4>I2:40", resumen(plan)
    assert plan["brigadas_faltantes"] == {"I1": 0, "I2": 0, "I3": 1}, plan["brigadas_faltantes"]
    print("Método voraz: correcto")


def probar_mas_cercana():
    """Por orden de detección (I3, I1, I2), una brigada cada uno, por línea recta."""
    # I3 e I1 quedan más cerca de B1; I2 queda más cerca de B2, aunque por camino tarde 40 min.
    plan = plan_ataque.generar_plan(INCENDIOS, BRIGADAS, BASES, TIEMPOS, metodo="cercana")
    assert resumen(plan) == "BR1>I3:5 BR2>I1:10 BR3>I2:40", resumen(plan)
    assert plan["brigadas_faltantes"] == {"I3": 0, "I1": 1, "I2": 1}, plan["brigadas_faltantes"]
    print("Método de la más cercana: correcto")


def probar_motobomba_y_apoyo_aereo():
    """Un incendio crítico pide 4 brigadas, una motobomba y recomendación de apoyo aéreo."""
    incendios = [{"id": "I4", "nivel": "critico", "inicio": "2025-04-15T10:00", "lat": 20.0, "lon": -103.4}]
    brigadas = BRIGADAS + [{"id": "BR5", "base": "B2", "tipo": "motobomba"}]
    plan = plan_ataque.generar_plan(incendios, brigadas, BASES, {"I4": {"B1": 30, "B2": 8}}, metodo="voraz")
    # Primero llegan las dos de B2 (8 min), luego las dos de B1 (30 min) y la motobomba de B2.
    assert resumen(plan) == "BR3>I4:8 BR4>I4:8 BR1>I4:30 BR2>I4:30 BR5>I4:8", resumen(plan)
    assert plan["recomendar_apoyo_aereo"] == ["I4"] and plan["sin_motobomba"] == []
    # Sin la unidad con motobomba, el plan avisa que falta.
    plan = plan_ataque.generar_plan(incendios, BRIGADAS, BASES, {"I4": {"B1": 30, "B2": 8}}, metodo="voraz")
    assert plan["sin_motobomba"] == ["I4"]
    print("Motobomba y apoyo aéreo: correcto")


def main():
    probar_orden()
    probar_voraz()
    probar_mas_cercana()
    probar_motobomba_y_apoyo_aereo()
    print("Todas las pruebas pasaron.")


if __name__ == "__main__":
    main()
