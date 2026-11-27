"""Comprobaciones de los rankings temáticos (rankings_temas.py, B-29).

Uso (desde la carpeta del proyecto):   python tests/test_rankings_temas.py
Solo usa la biblioteca estándar. Imprime OK o FALLA y termina con código 1 si algo falla.
"""
from pathlib import Path
import html
import json
import re
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
from rankings_temas import TEMAS, UMBRAL_ASEQUIBLE, AÑOS_SUBIDA  # noqa: E402
from config import ANIO  # noqa: E402

WEB = BASE / "web"
DATOS = BASE / "datos_limpios" / "ciudades_nivel1.json"
MIN_PARRAFOS, MIN_PALABRAS = 5, 120

resultados = []


def comprobar(descripcion, errores):
    errores = list(errores)
    estado = "OK" if not errores else "FALLA"
    resultados.append(estado)
    print(f"[{estado:5}] {descripcion}")
    for e in errores[:8]:
        print("        -", e)
    if len(errores) > 8:
        print(f"        ... y {len(errores) - 8} más")


def texto(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s))


def eur(x):
    return f"{round(x):,}".replace(",", ".") + " €"


def filas(raw):
    return re.findall(r"<tr(?: id=\"[^\"]*\")?><td data-v=\"\d+\">\d+</td>(.*?)</tr>", raw)


ciudades = json.loads(DATOS.read_text(encoding="utf-8"))["ciudades"]
por_slug = {c["slug"]: c for c in ciudades}
pag = {}
for s, _, _ in TEMAS:
    f = WEB / "rankings" / s / "index.html"
    pag[s] = f.read_text(encoding="utf-8") if f.exists() else ""

# 1. existen, están en el sitemap y en la portada
err = [f"falta web/rankings/{s}/" for s, v in pag.items() if not v]
mapa = (WEB / "sitemap.xml").read_text(encoding="utf-8") if (WEB / "sitemap.xml").exists() else ""
portada = (WEB / "index.html").read_text(encoding="utf-8")
for s in pag:
    if mapa and f"/rankings/{s}/</loc>" not in mapa:
        err.append(f"{s}: no está en el sitemap")
    if f'href="rankings/{s}/"' not in portada:
        err.append(f"{s}: la portada no lo enlaza")
comprobar(f"Los {len(TEMAS)} rankings temáticos existen, están en el sitemap y la portada los enlaza", err)

# 2. texto propio: mínimo de párrafos y palabras, sin párrafos repetidos entre páginas
err, vistos = [], {}
for s, raw in pag.items():
    m = re.search(r'<section id="claves">(.*?)</section>', raw, re.S)
    ps = re.findall(r"<p>(.*?)</p>", m.group(1), re.S) if m else []
    palabras = sum(len(texto(p).split()) for p in ps)
    if len(ps) < MIN_PARRAFOS or palabras < MIN_PALABRAS:
        err.append(f"{s}: {len(ps)} párrafos y {palabras} palabras (mínimo {MIN_PARRAFOS} y {MIN_PALABRAS})")
    for p in ps:
        if p in vistos and vistos[p] != s:
            err.append(f"{s}: párrafo repetido en {vistos[p]}")
        vistos[p] = s
comprobar("Cada página tiene su propio texto (5 párrafos o más, ninguno repetido)", err)

# 3. cada fila enlaza a la ficha de una ciudad existente
err = []
for s, raw in pag.items():
    fs = filas(raw)
    if not fs:
        err.append(f"{s}: tabla sin filas")
    for fila in fs:
        slugs = re.findall(r'href="\.\./\.\./([^/"]+)/', fila)
        if not slugs or slugs[0] not in por_slug:
            err.append(f"{s}: fila sin enlace válido a una ficha: {texto(fila)[:60]}")
            break
comprobar("Cada fila de las tablas enlaza a la ficha de su ciudad", err)

# 4. número de filas igual que los datos
err = []
A0 = ANIO - AÑOS_SUBIDA


def serie(c, a):
    return next((x["alquiler_mes"] for x in c["serie_alquiler"] if x["anio"] == a and x.get("alquiler_mes")), None)


esperado = {
    "donde-mas-sube-el-alquiler": sum(1 for c in ciudades if serie(c, A0) and serie(c, ANIO)),
    "sueldo-para-vivir-de-alquiler": len(ciudades),
    "ciudades-mas-jovenes": sum(1 for c in ciudades if c.get("edad_media") is not None),
    "barrios-con-mas-renta": sum(1 for c in ciudades for x in c["distritos"] if x.get("renta_hogar")),
    "barrios-con-el-alquiler-mas-caro": sum(1 for c in ciudades for x in c["distritos"]
                                            if x["fiabilidad"] in ("ok", "pocos_datos") and x.get("alquiler_mes") is not None),
}
for s, nfil in esperado.items():
    if len(filas(pag[s])) != nfil:
        err.append(f"{s}: {len(filas(pag[s]))} filas (esperadas {nfil})")
comprobar("Cada tabla tiene tantas filas como datos válidos hay en el JSON", err)

# 5. cifras: valores de referencia y cálculos
err = []
REF = {"madrid": 868.75, "valencia": 680.83, "valladolid": 530.83}
raw = pag["sueldo-para-vivir-de-alquiler"]
for slug, alq in REF.items():
    m = re.search(rf'<tr id="c-{slug}">(.*?)</tr>', raw)
    if not m or eur(alq) not in texto(m.group(1)) or eur(alq / (UMBRAL_ASEQUIBLE / 100)) not in texto(m.group(1)):
        err.append(f"sueldo: {slug} no muestra {eur(alq)} ni {eur(alq / (UMBRAL_ASEQUIBLE / 100))}")
raw = pag["donde-mas-sube-el-alquiler"]
for slug in REF:
    c = por_slug[slug]
    ch = (serie(c, ANIO) / serie(c, A0) - 1) * 100
    esp = ("+" if ch > 0 else "") + f"{ch:.1f}".replace(".", ",") + " %"
    m = re.search(rf'<tr id="c-{slug}">(.*?)</tr>', raw)
    if not m or esp not in texto(m.group(1)):
        err.append(f"subida: {slug} debería mostrar {esp}")
# orden: la primera fila de cada tabla es el máximo (o el mínimo) que corresponde
prim = lambda s: re.findall(r'href="\.\./\.\./([^/"]+)/', filas(pag[s])[0])[0]
if prim("ciudades-mas-jovenes") != min(ciudades, key=lambda c: (c["edad_media"], c["nombre"]))["slug"]:
    err.append("jóvenes: la primera fila no es la ciudad con menor edad media")
if prim("sueldo-para-vivir-de-alquiler") != min(ciudades, key=lambda c: (c["alquiler_mes"], c["nombre"]))["slug"]:
    err.append("sueldo: la primera fila no es la ciudad con el alquiler más bajo")
max_renta = max((x for c in ciudades for x in c["distritos"] if x.get("renta_hogar")), key=lambda x: x["renta_hogar"])
if eur(max_renta["renta_hogar"]) not in texto(filas(pag["barrios-con-mas-renta"])[0]):
    err.append("renta por distrito: la primera fila no es el distrito con más renta")
comprobar("Cifras correctas (valores de referencia, cálculo del 30 %, subidas y orden de las tablas)", err)

# 6. distritos con menos de 30 inmuebles: nunca muestran alquiler
err = []
ocultos = {(c["slug"], x["nombre"]) for c in ciudades for x in c["distritos"] if x["fiabilidad"] not in ("ok", "pocos_datos")}
for s in ("barrios-con-mas-renta", "barrios-con-el-alquiler-mas-caro"):
    for fila in filas(pag[s]):
        nom = html.unescape(re.search(r'<th scope="row" data-v="([^"]*)"', fila).group(1)).replace("’", "'")
        slug = re.findall(r'href="\.\./\.\./([^/"]+)/', fila)[0]
        if (slug, nom) in ocultos:
            if s == "barrios-con-el-alquiler-mas-caro":
                err.append(f"{s}: aparece {nom} ({slug}) con menos de 30 inmuebles")
            elif re.findall(r'<td data-v="([^"]*)">', fila)[3:5] != ["", ""]:
                err.append(f"{s}: {nom} ({slug}) muestra alquiler con menos de 30 inmuebles")
comprobar("Los distritos con menos de 30 inmuebles no muestran alquiler", err)

# 7. metodología y año en el título
err = []
for s, raw in pag.items():
    if 'id="metodologia"' not in raw:
        err.append(f"{s}: falta la metodología")
    if f"({ANIO})</title>" in raw:
        err.append(f"{s}: el <title> lleva el año (decisión 23/11/2026: va sin año)")
    if str(ANIO) in re.search(r"<h1>(.*?)</h1>", raw, re.S).group(1) or f"Datos oficiales de {ANIO}." not in raw:
        err.append(f"{s}: el H1 lleva el año o falta la línea con el año de los datos")
comprobar("Metodología en cada página, año en la línea bajo el H1 y no en el <title> ni en el H1", err)

print(f"\nResultado: {resultados.count('OK')} OK, {resultados.count('FALLA')} FALLA")
sys.exit(1 if "FALLA" in resultados else 0)
