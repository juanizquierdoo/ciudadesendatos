"""Barrios con nombre a partir de OpenStreetMap, para las ciudades sin fuente oficial utilizable (B-32).

Juan lo aprobó el 20/11/2026: usar OpenStreetMap donde no se pueda comprobar de otra forma, con la cita
en el pie de la web (no bajo cada tabla).

Entrada: datos_municipales/osm/osm_calles_N.csv y osm_barrios_N.json (los baja Juan con
datos_municipales/osm/descargar_osm.html, que crea osm_descarga.py). Datos © colaboradores de OpenStreetMap, ODbL.

Método (cruce propio):
  1. Cada calle de OSM se sitúa en un barrio: el polígono de barrio que contiene su punto central
     (admin_level 10 o place=neighbourhood/quarter; si no hay, admin_level 9 o place=suburb); si no cae
     en ninguno, el punto de barrio de OSM más cercano a menos de 800 m.
  2. Cada sección censal del INE reparte su población entre los barrios de sus calles (callejero
     electoral del INE: cada tramo de calle de la sección cuenta 1, repartido entre los barrios por los
     que pasa esa calle en OSM).
  3. En cada distrito del INE se nombran hasta 5 barrios con al menos el 5 % de la población, si al
     menos la mitad de los tramos de calle del distrito (ponderados por población) caen en algún barrio de OSM.
Sevilla y Málaga se calculan también, solo para comparar con sus barrios oficiales (no se escriben).

Uso: python zonas_osm.py   y después   python actualizar.py --desde 4
"""
import csv
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict

from config import DATOS
from zonas_ciudades import bonito, poblacion_secciones

OSM = DATOS.parent / "datos_municipales" / "osm"
CAJ = DATOS.parent / "datos_originales" / "caj_esp_072026"
SALIDA = DATOS / "zonas_nombradas.csv"
MIN_CUOTA, MAX_BARRIOS, MIN_COBERTURA, MAX_DIST_M = 0.05, 5, 0.5, 800
SOLO_COMPROBAR = {"41091", "29067"}
FECHA = "20/11/2026"
FUENTE = (f"© colaboradores de OpenStreetMap (ODbL), consulta Overpass del {FECHA}: barrios (admin_level 9-10 y "
          "place=suburb/neighbourhood/quarter) y calles con su punto central. Cruce propio con el callejero electoral del INE "
          "(julio 2026); peso: población del ADRH del INE. La lista resultante se publica con licencia ODbL")
NOTA = "Se nombran hasta 5 barrios donde vive al menos el 5 % de la población del distrito."

TIPOS = set("""CALLE CL C AVENIDA AVDA AV AVINGUDA ETORBIDEA PLAZA PZA PL PLAZUELA PLACA PLAZOLETA PASEO PS PASSEIG PASAJE PJE
PASSATGE CAMINO CMNO CAMI CARRETERA CTRA TRAVESIA TRVA TRAVESSERA RONDA RDA GLORIETA GTA CALLEJON CJON VIA CUESTA CTA
BULEVAR BLVR RAMBLA CARRER CARRERO RUA RUELA KALEA PLAZAOLA ENPARANTZA PASEALEKUA URBANIZACION URB BARRIO BO GRUPO
COSTANILLA SENDA ESCALINATA PARQUE AUTOVIA AUTOPISTA TRAVESSIA PLACETA PRAZA ROTONDA""".split())
VACIAS = set("DE DEL LA LAS LOS EL D L I Y DELS DES DA DO DAS DOS A AL S N".split())


def tokens(s):
    s = unicodedata.normalize("NFD", s.upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    t = [x for x in re.split(r"[^A-Z0-9]+", s) if x]
    return frozenset(x for x in t if x not in TIPOS and x not in VACIAS)


# ---------- OSM ----------
def leer_calles():
    calles = defaultdict(list)          # muni -> [(nombre, lat, lon)]
    for f in sorted(OSM.glob("osm_calles_*.csv")):
        muni = None
        for r in csv.reader(open(f, encoding="utf-8"), delimiter="|"):
            if not r or r[0] == "@type":
                continue
            if r[0] == "area":
                muni = r[1]
            elif muni and r[0] == "way" and r[-2]:
                # el nombre puede llevar "|": la latitud y la longitud son siempre las dos últimas columnas
                calles[muni].append(("|".join(r[2:-2]), float(r[-2]), float(r[-1])))
    return calles


def leer_barrios():
    out = defaultdict(lambda: {"poli": [], "nodos": []})
    for f in sorted(OSM.glob("osm_barrios_*.json")):
        muni = None
        for e in json.load(open(f, encoding="utf-8"))["elements"]:
            t = e.get("tags", {})
            if e["type"] == "area":
                muni = t.get("ine:municipio")
                continue
            nom = t.get("name")
            if not muni or not nom or re.match(r"(?i)^(distrito|districte|barrutia)\b|^\d+$", nom):
                continue
            if e["type"] == "node":
                out[muni]["nodos"].append((nom, e["lat"], e["lon"]))
                continue
            nivel = 1 if (t.get("admin_level") == "10" or t.get("place") in ("neighbourhood", "quarter")) else 2
            lineas = [e["geometry"]] if e["type"] == "way" else [m["geometry"] for m in e.get("members", []) if m.get("geometry")]
            segs = []
            for g in lineas:
                pts = [(p["lon"], p["lat"]) for p in g if p]
                segs += list(zip(pts, pts[1:]))
            if segs:
                xs = [p[0] for s in segs for p in s]; ys = [p[1] for s in segs for p in s]
                out[muni]["poli"].append((nivel, nom, (min(xs), min(ys), max(xs), max(ys)), segs))
    return out


def dentro(x, y, segs):
    c = False
    for (x1, y1), (x2, y2) in segs:
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def barrio_de(lat, lon, b, muni_nombre):
    for nivel in (1, 2):
        for n, nom, (a, bb, c, d), segs in b["poli"]:
            if n == nivel and a <= lon <= c and bb <= lat <= d and dentro(lon, lat, segs) and nom != muni_nombre:
                return nom
    mejor, dmin = None, MAX_DIST_M
    for nom, la, lo in b["nodos"]:
        dm = math.hypot((lo - lon) * 111320 * math.cos(math.radians(lat)), (la - lat) * 110540)
        if dm < dmin and nom != muni_nombre:
            mejor, dmin = nom, dm
    return mejor


# ---------- INE ----------
def calles_ine(munis):
    vias = {}
    for l in open(next(CAJ.glob("VIAS.*")), encoding="latin-1"):
        if l[:5] in munis:
            vias[(l[:5], l[47:52])] = l[57:107].strip()
    sec = defaultdict(Counter)            # seccion -> Counter(nombre INE -> tramos)
    for l in open(next(CAJ.glob("TRAM.*")), encoding="latin-1"):
        if l[:5] in munis:
            n = vias.get((l[:5], l[160:165]))
            if n:
                sec[l[:5] + l[70:72] + l[72:75]][n] += 1
    return sec


ARTICULOS = re.compile(r"^(el|la|les|los|las|els|es|sa|ses|so|o|a|os|as|l'|l’|s'|s’|d'|d’)\b", re.I)


def arregla(k):
    """Solo mayúsculas: 'SAN JOSE' -> 'San Jose'; 'carme' -> 'Carme' (los artículos en minúscula se respetan)."""
    if k == k.upper():
        return bonito(k)
    if k[:1].islower() and not ARTICULOS.match(k):
        return k[:1].upper() + k[1:]
    return k


def main():
    import pandas as pd
    calles, barrios = leer_calles(), leer_barrios()
    munis = set(calles)
    if not munis:
        print("No hay archivos osm_calles_*.csv en", OSM); return
    nombres_muni = {c["cod_muni"]: c["nombre"] for c in json.load(open(DATOS / "ciudades_nivel1.json", encoding="utf-8"))["ciudades"]}
    pob = poblacion_secciones()
    sec_ine = calles_ine(munis)
    filas, informe = [], []
    for muni in sorted(munis, key=lambda m: -sum(v for s, v in pob.items() if s[:5] == m)):
        b = barrios.get(muni, {"poli": [], "nodos": []})
        idx = defaultdict(Counter)                    # tokens -> Counter(barrio)
        for nom, la, lo in calles[muni]:
            k = tokens(nom)
            if k:
                idx[k][barrio_de(la, lo, b, nombres_muni.get(muni))] += 1
        post = defaultdict(set)                       # palabra -> claves que la contienen
        for x in idx:
            for tk in x:
                post[tk].add(x)
        cache = {}

        def buscar(n):
            if n not in cache:
                k = tokens(n)
                c = idx.get(k)
                if c is None and len(k) >= 2:
                    sup = set.intersection(*(post.get(tk, set()) for tk in k))
                    sub = {x for tk in k for x in post.get(tk, ()) if len(x) >= 2 and x <= k}
                    cand = sup | sub
                    c = idx[min(cand, key=lambda x: len(x ^ k))] if cand else None
                cache[n] = c
            return cache[n]

        dist_b, cub, tot = defaultdict(Counter), Counter(), Counter()
        for s, cs in sec_ine.items():
            if s[:5] != muni:
                continue
            d, p = s[:7], pob.get(s, 0)
            tot[d] += p
            reparto, asignado = Counter(), 0.0
            for n, w in cs.items():
                c = buscar(n)
                if c:
                    con = {k: v for k, v in c.items() if k}
                    tt = sum(con.values())
                    asignado += w * tt / sum(c.values())
                    for k, v in con.items():
                        reparto[k] += w * v / tt
            st = sum(reparto.values())
            if st:
                # cobertura: parte de los tramos de calle de la sección que caen en algún barrio de OSM
                cub[d] += p * asignado / sum(cs.values())
                for k, v in reparto.items():
                    dist_b[d][k] += p * v / st
        for d in sorted(tot):
            cov = cub[d] / tot[d] if tot[d] else 0
            t = sum(dist_b[d].values())
            noms = [arregla(k) for k, v in dist_b[d].most_common() if t and v / t >= MIN_CUOTA][:MAX_BARRIOS]
            informe.append((muni, nombres_muni.get(muni, ""), d, cov, noms, len(b["poli"]), len(b["nodos"])))
            if cov >= MIN_COBERTURA and noms and muni not in SOLO_COMPROBAR:
                filas.append({"codigo": d, "zonas": "|".join(noms), "fuente": FUENTE, "cita": "", "nota": NOTA})
    for m, n, d, cov, noms, npol, nnod in informe:
        print(f"{m} {n[:22]:22} {d[-2:]} cob {cov:4.0%} pol {npol:3} nod {nnod:3}: {', '.join(noms)}")
    # no se pisan ciudades con fuente oficial (zonas_ciudades.py, Valladolid...)
    previas = list(csv.DictReader(open(SALIDA, encoding="utf-8"))) if SALIDA.exists() else []
    oficiales = {r["codigo"][:5] for r in previas if "OpenStreetMap" not in r["fuente"]}
    nuevas = [f for f in filas if f["codigo"][:5] not in oficiales]
    otras = [r for r in previas if "OpenStreetMap" not in r["fuente"]]
    with open(SALIDA, "w", encoding="utf-8", newline="") as out:
        w = csv.DictWriter(out, fieldnames=["codigo", "zonas", "fuente", "cita", "nota"], restval="")
        w.writeheader()
        w.writerows(otras + nuevas)
    print(f"Escritos {len(nuevas)} distritos de {len({f['codigo'][:5] for f in nuevas})} ciudades con barrios de OpenStreetMap; "
          f"conservadas {len(otras)} filas de fuentes oficiales")


if __name__ == "__main__":
    main()
