"""Posición de cada distrito en el mapa esquemático de las fichas (casillas como el de Madrid).

Ninguna fuente oficial descargada trae las coordenadas de los distritos, así que la posición se calcula
con datos que ya están en la carpeta:
  1. Callejero electoral del INE (datos_originales/caj_esp_072026, TRAM y VIAS): en qué distrito está cada
     tramo de calle. Una calle se asigna a un distrito si al menos el 80 % de sus tramos están en él.
  2. Calles de OpenStreetMap con su punto central (datos_municipales/osm/osm_calles_*.csv, © colaboradores
     de OpenStreetMap, ODbL): las calles de cada distrito se buscan por nombre (mismo cruce que zonas_osm.py).
  3. Centro del distrito = mediana de la latitud y de la longitud de esos puntos (al menos MIN_PUNTOS).
     Distritos rurales con pocas calles con nombre (sobre todo en Galicia): centro de sus parroquias, es
     decir, las entidades colectivas del INE (fichero UP) que tienen en OpenStreetMap un límite de parroquia
     (place=civil_parish) con el mismo nombre, ponderadas por sus tramos de calle; solo si se encuentra al
     menos la mitad de los tramos del distrito. Si algún distrito no llega a nada de esto, la ciudad no tiene mapa.
  4. Los centros se colocan en una rejilla (asignación óptima, método húngaro) que respeta su posición
     relativa: lo que está al norte queda arriba, lo que está al este, a la derecha. No son límites reales.
Madrid conserva su colocación hecha a mano (aprobada antes); el cálculo coincide con ella en el 99 % de las
comparaciones norte-sur y este-oeste entre pares de distritos (se comprueba en tests/test_mapa.py).

Solo ciudades con al menos MIN_DISTRITOS distritos: con menos, el mapa no aporta nada a la tabla.
Salida: datos_limpios/mapa_distritos.csv (codigo, col, fila, puntos, metodo).
Uso: python mapa_distritos.py   (también lo ejecuta actualizar.py)
"""
import csv
import json
import math
import re
import statistics
from collections import Counter, defaultdict

from config import DATOS
from zonas_osm import CAJ, OSM, calles_ine, leer_calles, tokens

SALIDA = DATOS / "mapa_distritos.csv"
MIN_DISTRITOS, MIN_PUNTOS, CUOTA_CALLE = 5, 10, 0.8
MEZCLA, DENSIDAD, MAX_COL = 0.5, 1.6, 8

# Madrid: colocación hecha a mano (columna, fila), la que ya estaba publicada
MADRID = {1: (2, 3), 2: (2, 4), 3: (3, 3), 4: (3, 2), 5: (3, 1), 6: (2, 1), 7: (2, 2), 8: (2, 0),
          9: (1, 1), 10: (0, 2), 11: (1, 3), 12: (1, 4), 13: (4, 3), 14: (4, 2), 15: (4, 1),
          16: (4, 0), 17: (2, 5), 18: (5, 3), 19: (5, 2), 20: (5, 1), 21: (6, 0)}


def parroquias(munis):
    """Centro (del rectángulo que la contiene) de cada parroquia de OSM: {muni: {tokens del nombre: (lat, lon)}}"""
    out = defaultdict(dict)
    for f in sorted(OSM.glob("osm_barrios_*.json")):
        muni = None
        for e in json.load(open(f, encoding="utf-8"))["elements"]:
            t = e.get("tags", {})
            if e["type"] == "area":
                muni = t.get("ine:municipio")
            elif muni in munis and t.get("place") == "civil_parish" and t.get("name") and e["type"] == "relation":
                pts = [(q["lat"], q["lon"]) for mb in e.get("members", []) if mb.get("geometry") for q in mb["geometry"] if q]
                if pts:
                    la, lo = [a for a, b in pts], [b for a, b in pts]
                    out[muni][tokens(t["name"])] = ((min(la) + max(la)) / 2, (min(lo) + max(lo)) / 2)
    return out


def centros_parroquias(munis, distritos):
    """{codigo_distrito: (lat, lon, n_parroquias)} para los distritos pedidos, si se encuentra >= 50 % de sus tramos."""
    par = parroquias(munis)
    nombre = {}
    for l in open(next(CAJ.glob("UP.*")), encoding="latin-1"):
        if l[:5] in munis and l[5:7] != "00" and l[7:12] == "00000":      # entidad colectiva (parroquia)
            nombre[l[:7]] = l[160:230].strip() or l[90:160].strip()
    tramos = defaultdict(Counter)
    for l in open(next(CAJ.glob("TRAM.*")), encoding="latin-1"):
        if l[:5] + l[70:72] in distritos:
            tramos[l[:5] + l[70:72]][l[:5] + l[78:80]] += 1

    def buscar(m, n):
        # 'ADAI (SANTA MARIA MADANELA)' -> 'Adai'; 'TRASANCOS (SANTA ICIA)' -> 'Santa Icía de Trasancos'
        for k in (tokens(re.sub(r"\s*\((?!(A|O|AS|OS)\)).*$", "", n)), tokens(n)):
            if k in par[m]:
                return par[m][k]

    out = {}
    for d, cnt in tramos.items():
        hall = [(buscar(d[:5], nombre[k]), v) for k, v in cnt.items() if k in nombre]
        hall = [(p, v) for p, v in hall if p]
        peso = sum(v for p, v in hall)
        if hall and peso >= 0.5 * sum(cnt.values()):
            out[d] = (sum(p[0] * v for p, v in hall) / peso, sum(p[1] * v for p, v in hall) / peso, len(hall))
    return out


def centros(munis):
    """{muni: {codigo_distrito: (lat, lon, n_puntos)}}"""
    calles = leer_calles()
    munis = munis & set(calles)
    via_d = defaultdict(lambda: defaultdict(Counter))       # muni -> calle INE -> Counter(distrito -> tramos)
    for s, cs in calles_ine(munis).items():
        for nom, w in cs.items():
            via_d[s[:5]][nom][s[:7]] += w
    out = {}
    for m in sorted(munis):
        idx = defaultdict(list)
        for nom, la, lo in calles[m]:
            k = tokens(nom)
            if k:
                idx[k].append((la, lo))
        pts = defaultdict(list)
        for nom, cnt in via_d[m].items():
            d, v = cnt.most_common(1)[0]
            if v / sum(cnt.values()) >= CUOTA_CALLE:
                pts[d] += idx.get(tokens(nom), [])
        out[m] = {d: (statistics.median(a for a, b in p), statistics.median(b for a, b in p), len(p))
                  for d, p in pts.items() if p}
    return out


def hungaro(coste):
    """Asignación de coste mínimo (filas <= columnas). Devuelve la columna elegida para cada fila."""
    n, m, INF = len(coste), len(coste[0]), float("inf")
    u, v, p, way = [0] * (n + 1), [0] * (m + 1), [0] * (m + 1), [0] * (m + 1)
    for i in range(1, n + 1):
        p[0], j0 = i, 0
        minv, usado = [INF] * (m + 1), [False] * (m + 1)
        while True:
            usado[j0] = True
            i0, delta, j1 = p[j0], INF, 0
            for j in range(1, m + 1):
                if not usado[j]:
                    cur = coste[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j], way[j] = cur, j0
                    if minv[j] < delta:
                        delta, j1 = minv[j], j
            for j in range(m + 1):
                if usado[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    res = [None] * n
    for j in range(1, m + 1):
        if p[j]:
            res[p[j] - 1] = j - 1
    return res


def rejilla(cen):
    """{distrito: (lat, lon, ...)} -> {distrito: (col, fila)}, norte arriba y este a la derecha."""
    ds = sorted(cen)
    n = len(ds)
    lat0 = sum(cen[d][0] for d in ds) / n
    xy = {d: (cen[d][1] * math.cos(math.radians(lat0)) * 111.32, cen[d][0] * 110.54) for d in ds}
    xs, ys = [p[0] for p in xy.values()], [p[1] for p in xy.values()]
    w, h = (max(xs) - min(xs)) or 1, (max(ys) - min(ys)) or 1
    celdas = max(round(n * DENSIDAD), n + 3)
    cols = max(2, min(MAX_COL, round(math.sqrt(celdas * w / h))))
    filas = max(2, math.ceil(celdas / cols))
    # mezcla de posición real y orden (rango): evita que un distrito muy alejado aplaste a los demás
    rx = {d: i / (n - 1) for i, d in enumerate(sorted(ds, key=lambda d: xy[d][0]))}
    ry = {d: i / (n - 1) for i, d in enumerate(sorted(ds, key=lambda d: -xy[d][1]))}
    pos = {d: (((1 - MEZCLA) * (xy[d][0] - min(xs)) / w + MEZCLA * rx[d]) * (cols - 1),
               ((1 - MEZCLA) * (max(ys) - xy[d][1]) / h + MEZCLA * ry[d]) * (filas - 1)) for d in ds}
    huecos = [(c, f) for f in range(filas) for c in range(cols)]
    elegido = hungaro([[(pos[d][0] - c) ** 2 + (pos[d][1] - f) ** 2 for c, f in huecos] for d in ds])
    g = {d: huecos[elegido[i]] for i, d in enumerate(ds)}
    # quitar filas y columnas vacías
    cs, fs = sorted({c for c, f in g.values()}), sorted({f for c, f in g.values()})
    return {d: (cs.index(c), fs.index(f)) for d, (c, f) in g.items()}


def main():
    ciudades = json.load(open(DATOS / "ciudades_nivel1.json", encoding="utf-8"))["ciudades"]
    con_dist = {c["cod_muni"]: c for c in ciudades if len(c["distritos"]) >= MIN_DISTRITOS}
    cen = centros(set(con_dist))
    filas, sin = [], []
    for m, c in sorted(con_dist.items(), key=lambda kv: -kv[1]["poblacion"]):
        codigos = [x["codigo"] for x in c["distritos"]]
        if m == "28079":
            for x in c["distritos"]:
                col, fila = MADRID[x["numero"]]
                filas.append({"codigo": x["codigo"], "col": col, "fila": fila, "puntos": "", "metodo": "manual"})
            continue
        cm = dict(cen.get(m, {}))
        pocos = [k for k in codigos if cm.get(k, (0, 0, 0))[2] < MIN_PUNTOS]
        metodo = {k: "calles" for k in codigos}
        if pocos and m in cen:
            for k, v in centros_parroquias({m}, set(pocos)).items():
                cm[k] = (v[0], v[1], MIN_PUNTOS)          # vale como centro aunque tenga pocas calles
                metodo[k] = f"parroquias ({v[2]})"
        faltan = [k for k in codigos if cm.get(k, (0, 0, 0))[2] < MIN_PUNTOS]
        if faltan:
            sin.append(f"{c['nombre']} ({len(faltan)} de {len(codigos)} distritos sin calles suficientes)"
                       if m in cen else f"{c['nombre']} (no hay calles de OpenStreetMap descargadas)")
            continue
        for k, (col, fila) in sorted(rejilla({k: cm[k] for k in codigos}).items()):
            filas.append({"codigo": k, "col": col, "fila": fila, "puntos": cen[m].get(k, (0, 0, 0))[2], "metodo": metodo[k]})
    with open(SALIDA, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["codigo", "col", "fila", "puntos", "metodo"])
        w.writeheader()
        w.writerows(filas)
    n = len({r["codigo"][:5] for r in filas})
    print(f"Mapa esquemático: {n} ciudades ({len(filas)} distritos) -> {SALIDA.name}")
    print(f"Sin mapa ({len(sin)}), con {MIN_DISTRITOS} distritos o más:", "; ".join(sin))
    print(f"Sin mapa por tener menos de {MIN_DISTRITOS} distritos:",
          sum(1 for c in ciudades if 0 < len(c["distritos"]) < MIN_DISTRITOS))


if __name__ == "__main__":
    main()
