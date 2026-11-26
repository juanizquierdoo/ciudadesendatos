"""Comprobaciones del mapa de precios de España (mapa_precios.py y preparar_mapa.py).

Uso (desde la carpeta del proyecto):   python tests/test_mapa_precios.py
Solo usa la biblioteca estándar. Imprime OK o FALLA y termina con código 1 si algo falla.
El dibujo (JavaScript) se prueba aparte en un navegador; aquí se comprueban los límites, los datos que
lleva el mapa (valores de referencia y regla de fiabilidad), el peso de los archivos, la página y el sitemap.
"""
from pathlib import Path
import csv
import html
import json
import re
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
import mapa_precios as mp  # noqa: E402
from config import ANIO, DISTRITOS, MUNICIPIOS, REFERENCIA  # noqa: E402

GEO = BASE / "datos_limpios" / "mapa"
WEB = BASE / "web" / mp.SLUG
MAX_ESPANA_KB, MAX_PROV_KB = 2600, 1500   # sin comprimir; GitHub Pages los sirve comprimidos (unas 4 veces menos)
resultados = []


def comprobar(descripcion, errores):
    errores = list(errores)
    estado = "OK" if not errores else "FALLA"
    resultados.append(estado)
    print(f"[{estado:5}] {descripcion}")
    for e in errores[:8]:
        print("        -", e)


if not (GEO / "espana.json").exists():
    print("[OK   ] Sin límites en datos_limpios/mapa (preparar_mapa.py no se ha ejecutado): no hay mapa que comprobar")
    sys.exit(0)

geo = json.loads((GEO / "espana.json").read_text(encoding="utf-8"))
munis = {r["cod_muni"].zfill(5): r for r in csv.DictReader(open(MUNICIPIOS, encoding="utf-8-sig"))}
dist = {r["codigo"].zfill(7): r for r in csv.DictReader(open(DISTRITOS, encoding="utf-8-sig"))}


def refs_validas(geoms, n):
    return [g for g, rs in geoms.items() for r in rs for a in r if not (0 <= (a if a >= 0 else ~a) < n)]


# ---- límites
err = [f"municipio {m} sin límites" for m in sorted(set(munis) - set(geo["municipios"]))]
err += [f"{m}: límite de un municipio que no está en los datos" for m in sorted(set(geo["municipios"]) - set(munis))]
comprobar(f"Límites de todos los municipios con datos ({len(munis)})", err)
comprobar("Los arcos de España existen", [f"{g}: arco inexistente" for g in refs_validas(geo["municipios"], len(geo["arcos"]))])

prov = sorted({m[:2] for m in geo["municipios"]})
err, unidades = [], {}
for p in prov:
    f = GEO / "p" / f"{p}.json"
    if not f.exists():
        err.append(f"falta p/{p}.json")
        continue
    j = json.loads(f.read_text(encoding="utf-8"))
    err += [f"p/{p}: {g} con arco inexistente" for g in refs_validas(j["unidades"], len(j["arcos"]))]
    unidades.update(j["unidades"])
comprobar(f"Un archivo de detalle por provincia ({len(prov)}) con arcos válidos", err)

con_varios = {}
for d in dist:
    con_varios.setdefault(d[:5], set()).add(d)
esperadas = set()
for m in munis:
    ds = con_varios.get(m, set())
    esperadas |= ds if len(ds) > 1 else {m}
falta = sorted(esperadas - set(unidades))
sobra = sorted(set(unidades) - esperadas)
comprobar("Cada distrito de los datos tiene su límite (municipios con más de un distrito)",
          [f"sin límite: {x}" for x in falta] + [f"límite sin datos: {x}" for x in sobra])

# ---- web
if not (WEB / "index.html").exists():
    comprobar("Existe la página del mapa", [f"falta {WEB / 'index.html'}"])
    sys.exit(1)
s = (WEB / "index.html").read_text(encoding="utf-8")
esp = json.loads((WEB / "espana.json").read_text(encoding="utf-8"))
D = esp.get("datos", {})

err = []
for cod, (nom, alq, ren, pct) in REFERENCIA.get(ANIO, {}).items():
    x = D.get(cod)
    if not x:
        err.append(f"{nom}: sin datos en el mapa")
        continue
    if x[0] != nom and nom not in x[0]:
        err.append(f"{cod}: nombre {x[0]} ≠ {nom}")
    if x[1] is None or abs(x[1] - alq) > 0.6:
        err.append(f"{nom}: alquiler {x[1]} ≠ {alq}")
    if x[3] is None or abs(x[3] - ren) > 0.6:
        err.append(f"{nom}: renta {x[3]} ≠ {ren}")
    if x[4] is None or abs(x[4] - pct) > 0.05:
        err.append(f"{nom}: alquiler/renta {x[4]} ≠ {pct}")
comprobar("Valores de referencia en el mapa (Madrid, Valencia, Valladolid)", err)

err = []
for cod, x in D.items():
    r = munis[cod]
    if r["fiabilidad"] not in mp.FIABLES and (x[1] is not None or x[4] is not None):
        err.append(f"{x[0]} ({cod}): muestra alquiler con fiabilidad {r['fiabilidad']}")
    if r["fiabilidad"] in mp.FIABLES and x[1] is None:
        err.append(f"{x[0]} ({cod}): falta el alquiler")
    if (r["fiabilidad"] == "pocos_datos") != bool(x[6]):
        err.append(f"{x[0]} ({cod}): aviso de pocos datos mal puesto")
nd = 0
for f in sorted((WEB / "p").glob("*.json")):
    for cod, x in json.loads(f.read_text(encoding="utf-8"))["datos"].items():
        nd += 1
        r = dist[cod]
        if r["fiabilidad"] not in mp.FIABLES and x[1] is not None:
            err.append(f"distrito {cod}: muestra alquiler con fiabilidad {r['fiabilidad']}")
        if r["fiabilidad"] in mp.FIABLES and x[1] is not None and abs(float(r["alquiler_mes"]) - x[1]) > 0.6:
            err.append(f"distrito {cod}: alquiler {x[1]} ≠ {r['alquiler_mes']}")
comprobar(f"Regla de fiabilidad del alquiler (menos de 30 inmuebles, sin cifra) en {len(D)} municipios y {nd} distritos", err)

err = []
kb = (WEB / "espana.json").stat().st_size / 1024
if kb > MAX_ESPANA_KB:
    err.append(f"espana.json pesa {kb:.0f} KB (máximo {MAX_ESPANA_KB})")
for f in sorted((WEB / "p").glob("*.json")):
    kb = f.stat().st_size / 1024
    if kb > MAX_PROV_KB:
        err.append(f"p/{f.name} pesa {kb:.0f} KB (máximo {MAX_PROV_KB})")
comprobar("Peso de los archivos del mapa (ligero en el móvil)", err)


def texto(x):
    x = re.sub(r"<script.*?</script>|<style.*?</style>", " ", x, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x)))


t = texto(s)
err = []
for frase in ("Ojo con las zonas turísticas", "Elaboración propia con datos extraídos del sitio web del INE",
              "Ministerio de Vivienda", "no inventamos ni estimamos"):
    if frase not in t:
        err.append(f"falta «{frase}»")
if "__ESCALA__" in s:
    err.append("escala sin rellenar en el JavaScript")
if re.search(r"https?://(?!creativecommons|opendatacommons|www\.openstreetmap|ciudadesendatos)", " ".join(re.findall(r'(?:src|href)="([^"]+)"', s))):
    err.append("la página carga algo de otro sitio")
comprobar("Página del mapa: aviso turístico, fuentes y sin recursos de terceros", err)

sm = BASE / "web" / "sitemap.xml"
err = []
if sm.exists() and f"/{mp.SLUG}/<" not in sm.read_text(encoding="utf-8"):
    err.append("el sitemap no incluye /mapa/")
if f'href="{mp.SLUG}/"' not in (BASE / "web" / "index.html").read_text(encoding="utf-8"):
    err.append("la portada no enlaza al mapa")
comprobar("Mapa en el sitemap y enlazado desde la portada", err)

sys.exit(1 if "FALLA" in resultados else 0)
