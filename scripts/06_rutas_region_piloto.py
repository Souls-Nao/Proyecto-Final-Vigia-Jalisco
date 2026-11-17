# 06_rutas_region_piloto.py
# Calcula, para cada incendio real de la región piloto, cuánto tarda en llegar por camino cada base
# de brigadas y por dónde. Es lo pesado del plan de ataque: el navegador solo reparte las brigadas.
# Lee:     datos/procesados/incendios_clasificados.csv   (script 05)
#          datos/referencia/bases.csv                     (bases hipotéticas)
#          internet (red de caminos de OpenStreetMap, solo la primera vez)
# Escribe: datos/crudos/red_vial_piloto.graphml           (red de caminos; pesa mucho y no se sube)
#          web/datos/rutas_piloto.json
# Uso:     python scripts/06_rutas_region_piloto.py       (la primera vez tarda varios minutos)

import json
from datetime import date

import networkx as nx
import osmnx as ox
import pandas as pd
from shapely.geometry import LineString

import config


def descargar_red_vial():
    """Baja la red de caminos de la región piloto, probando un servidor tras otro hasta que uno responda."""
    caja = (config.PILOTO_OESTE, config.PILOTO_SUR, config.PILOTO_ESTE, config.PILOTO_NORTE)
    # El filtro deja solo los tipos de camino por los que pasa un vehículo (ver config).
    filtro = f'["highway"~"^({config.TIPOS_DE_CAMINO})$"]'
    for servidor in config.SERVIDORES_OSM:
        print("  Descargando la red de caminos desde", servidor, "(varios minutos)…")
        ox.settings.overpass_url = servidor
        try:
            return ox.graph_from_bbox(caja, custom_filter=filtro)
        except Exception as error:
            # Los servidores públicos se saturan a ratos; se avisa y se prueba con el siguiente.
            print("  Ese servidor no respondió:", str(error).splitlines()[0][:100])
    raise SystemExit("Ningún servidor de OpenStreetMap respondió. Intenta de nuevo en unos minutos.")


def obtener_red_vial():
    """Devuelve la red de caminos de la región piloto. La descarga la primera vez y después la reutiliza."""
    if config.ARCHIVO_RED_VIAL.exists():
        print("  Red de caminos ya descargada; se lee del disco.")
        return ox.load_graphml(config.ARCHIVO_RED_VIAL)
    red = descargar_red_vial()
    # A cada tramo se le pone su velocidad y, con ella, el tiempo en segundos que toma recorrerlo.
    red = ox.add_edge_speeds(red, hwy_speeds=config.VELOCIDADES_KMH)
    red = ox.add_edge_travel_times(red)
    ox.save_graphml(red, config.ARCHIVO_RED_VIAL)
    return red


def nodo_mas_cercano(red, lat, lon):
    """Busca el cruce de caminos más cercano a un lugar. Devuelve (nodo, distancia en metros)."""
    nodo, distancia_m = ox.distance.nearest_nodes(red, X=lon, Y=lat, return_dist=True)
    return nodo, round(float(distancia_m))


def camino_hasta(anteriores, destino):
    """Reconstruye la lista de nodos desde la base hasta el destino, yendo hacia atrás."""
    # "anteriores" dice, para cada nodo, de qué nodo viene el camino más rápido desde la base.
    camino = [destino]
    while anteriores[camino[-1]]:
        camino.append(anteriores[camino[-1]][0])
    camino.reverse()
    return camino


def trazo_de_ruta(red, nodos):
    """Convierte una lista de nodos en la línea que se dibuja en el mapa: [[lat, lon], …]."""
    if len(nodos) < 2:
        return [[round(red.nodes[nodos[0]]["y"], 5), round(red.nodes[nodos[0]]["x"], 5)]]
    # Cada tramo trae su forma real (con curvas); se pegan todas una tras otra.
    tramos = ox.routing.route_to_gdf(red, nodos, weight="travel_time")
    puntos = [punto for forma in tramos.geometry for punto in forma.coords]
    # Se quitan puntos que casi no cambian el trazo. Un grado mide unos 111 km.
    linea = LineString(puntos).simplify(config.SIMPLIFICAR_RUTAS_M / 111_000)
    return [[round(lat, 5), round(lon, 5)] for lon, lat in linea.coords]


def rutas_de_una_base(red, base, accesos):
    """Calcula tiempo (minutos) y trazo desde una base hasta el punto de acceso de cada incendio."""
    nodo_base, _ = nodo_mas_cercano(red, base["lat"], base["lon"])
    # Dijkstra: una sola corrida da el camino más rápido de la base a TODOS los nodos de la red.
    anteriores, segundos = nx.dijkstra_predecessor_and_distance(red, nodo_base, weight="travel_time")
    tiempos, trazos = {}, {}
    for incendio_id, acceso in accesos.items():
        if acceso["nodo"] not in segundos:
            continue        # no hay camino de esta base a ese punto (calles de un solo sentido, etc.)
        tiempos[incendio_id] = round(segundos[acceso["nodo"]] / 60, 1)
        trazos[incendio_id] = trazo_de_ruta(red, camino_hasta(anteriores, acceso["nodo"]))
    return tiempos, trazos


def lista_de_brigadas(bases):
    """Arma la lista de brigadas: cada base aporta sus brigadas terrestres y sus unidades con motobomba."""
    brigadas = []
    for _, base in bases.iterrows():
        tipos = ["terrestre"] * base["brigadas_terrestres"] + ["motobomba"] * base["motobombas"]
        for tipo in tipos:
            brigadas.append({"id": f"BR{len(brigadas) + 1:02d}", "base": base["base_id"], "tipo": tipo})
    return brigadas


def main():
    for archivo in [config.ARCHIVO_CLASIFICADOS, config.ARCHIVO_BASES]:
        if not archivo.exists():
            raise SystemExit(f"No se encontró {archivo}. Corre primero el script 05 y revisa datos/referencia/.")
    incendios = pd.read_csv(config.ARCHIVO_CLASIFICADOS, keep_default_na=False)
    incendios = incendios[(incendios["es_real"] == 1) & (incendios["en_piloto"] == 1)]
    bases = pd.read_csv(config.ARCHIVO_BASES)
    print("Incendios reales en la región piloto:", len(incendios), "| bases:", len(bases))

    print("1. Red de caminos")
    red = obtener_red_vial()
    print("  cruces:", red.number_of_nodes(), "| tramos:", red.number_of_edges())

    print("2. Punto de acceso de cada incendio (el cruce de caminos más cercano a su centro)")
    accesos = {}
    for _, incendio in incendios.iterrows():
        nodo, distancia_m = nodo_mas_cercano(red, incendio["lat"], incendio["lon"])
        accesos[incendio["incendio_id"]] = {"nodo": nodo, "dist_acceso_m": distancia_m,
                                            "lat": round(red.nodes[nodo]["y"], 5), "lon": round(red.nodes[nodo]["x"], 5)}

    print("3. Tiempos y rutas desde cada base")
    tiempos = {incendio_id: {} for incendio_id in accesos}
    rutas = {}
    for _, base in bases.iterrows():
        tiempos_base, trazos_base = rutas_de_una_base(red, base, accesos)
        for incendio_id, minutos in tiempos_base.items():
            tiempos[incendio_id][base["base_id"]] = minutos
            rutas[f"{incendio_id}|{base['base_id']}"] = trazos_base[incendio_id]
        print(f"  {base['base_id']} {base['nombre']}: llega a {len(tiempos_base)} de {len(accesos)} incendios")

    contenido = {
        "generado": date.today().isoformat(),
        "nota": "Las bases son HIPOTÉTICAS (supuesto del equipo). Los tiempos son de un vehículo por camino, "
                "sin tráfico, hasta el punto de acceso: el cruce de caminos más cercano al incendio.",
        "bases": [{"id": b["base_id"], "nombre": b["nombre"], "lat": b["lat"], "lon": b["lon"],
                   "hipotetica": bool(b["hipotetica"])} for _, b in bases.iterrows()],
        "brigadas": lista_de_brigadas(bases),
        "accesos": {i: {"lat": a["lat"], "lon": a["lon"], "dist_acceso_m": a["dist_acceso_m"]} for i, a in accesos.items()},
        "tiempos": tiempos,
        "rutas": rutas,
    }
    destino = config.CARPETA_WEB_DATOS / "rutas_piloto.json"
    destino.write_text(json.dumps(contenido, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Listo: {len(rutas)} rutas guardadas en {destino} ({destino.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    main()
