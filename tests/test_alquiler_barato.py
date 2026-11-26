"""Comprobaciones de las páginas de alquiler barato (alquiler_barato.py, B-38).

Uso (desde la carpeta del proyecto):   python tests/test_alquiler_barato.py
Solo usa la biblioteca estándar. Imprime OK o FALLA y termina con código 1 si algo falla.
"""
from pathlib import Path
import html
import json
import re
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
import alquiler_barato as ab  # noqa: E402
from config import ANIO  # noqa: E402

WEB = BASE / "web"
DATOS = BASE / "datos_limpios" / "ciudades_nivel1.json"
DATOS_CCAA = BASE / "datos_limpios" / "comunidades.json"
MIN_PARRAFOS, MIN_PALABRAS = 5, 150

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
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))


def eur(x):
    return f"{round(x):,}".replace(",", ".") + " €"


def leer(ruta):
    f = WEB / ruta / "index.html"
    return f.read_text(encoding="utf-8") if f.exists() else ""


# mismas ciudades que generar_web.main()
todas = [c for c in json.loads(DATOS.read_text(encoding="utf-8"))["ciudades"]
         if c.get("alquiler_pct_renta") is not None and c.get("renta_hogar") and c.get("alquiler_mes")]
por_slug = {c["slug"]: c for c in todas}
provs = ab.provincias(todas)
rutas = {f"rankings/{ab.SLUG_CCAA}/": leer(f"rankings/{ab.SLUG_CCAA}/")}
rutas.update({f"{ab.CARPETA}/{cap['slug']}/": leer(f"{ab.CARPETA}/{cap['slug']}/") for cap, _ in provs})

# 1. existen, sitemap, portada, enlaces cruzados y desde las fichas
err = [f"falta web/{r}" for r, v in rutas.items() if not v]
if len(provs) < 5:
    err.append(f"solo {len(provs)} provincias con página (se esperaban al menos 5)")
mapa = (WEB / "sitemap.xml").read_text(encoding="utf-8") if (WEB / "sitemap.xml").exists() else ""
for r in rutas:
    if mapa and f"/{r}</loc>" not in mapa:
        err.append(f"{r}: no está en el sitemap")
if f'href="rankings/{ab.SLUG_CCAA}/"' not in leer(""):
    err.append("la portada no enlaza el ranking por comunidad")
nac = rutas[f"rankings/{ab.SLUG_CCAA}/"]
for cap, otras in provs:
    if f'href="../../{ab.CARPETA}/{cap["slug"]}/"' not in nac:
        err.append(f"el ranking por comunidad no enlaza {cap['slug']}")
    for c in [cap] + otras:
        if f'href="../{ab.CARPETA}/{cap["slug"]}/"' not in leer(f"{c['slug']}/"):
            err.append(f"la ficha de {c['slug']} no enlaza {ab.CARPETA}/{cap['slug']}/")
con_pag = {c["slug"] for cap, otras in provs for c in [cap] + otras}
for c in todas:
    if c["slug"] not in con_pag and f'href="../{ab.CARPETA}/' in leer(f"{c['slug']}/"):
        err.append(f"la ficha de {c['slug']} enlaza una página de provincia que no es la suya")
comprobar(f"{len(rutas)} páginas (1 por comunidad + {len(provs)} por provincia) en sitemap, portada y fichas", err)

# 2. texto propio
err, vistos = [], {}
for r, raw in rutas.items():
    m = re.search(r'<section id="claves">(.*?)</section>', raw, re.S)
    ps = re.findall(r"<p>(.*?)</p>", m.group(1), re.S) if m else []
    palabras = sum(len(texto(p).split()) for p in ps)
    if len(ps) < MIN_PARRAFOS or palabras < MIN_PALABRAS:
        err.append(f"{r}: {len(ps)} párrafos y {palabras} palabras (mínimo {MIN_PARRAFOS} y {MIN_PALABRAS})")
    for p in ps:
        if p in vistos and vistos[p] != r:
            err.append(f"{r}: párrafo repetido en {vistos[p]}")
        vistos[p] = r
    if re.search(r"\bnan\b|\bNone\b", texto(raw)):
        err.append(f"{r}: aparece nan o None")
comprobar("Cada página tiene su propio texto (5 párrafos o más, ninguno repetido) y sin nan/None", err)

# 3. cifras de las páginas de provincia iguales que el JSON
err = []
for cap, otras in provs:
    raw = rutas[f"{ab.CARPETA}/{cap['slug']}/"]
    t = texto(raw)
    vis = sorted(ab.visibles(cap), key=lambda x: (x["alquiler_mes"], x["numero"]))
    bd = vis[0]
    if f"menos de {eur(cap['alquiler_mes'])} al mes" not in t:
        err.append(f"{cap['slug']}: no muestra la mediana de la ciudad ({eur(cap['alquiler_mes'])})")
    if f"el más barato es {ab.nd(bd)}, con {eur(bd['alquiler_mes'])}" not in t:
        err.append(f"{cap['slug']}: distrito más barato distinto de {ab.nd(bd)} ({eur(bd['alquiler_mes'])})")
    if f"unos {eur((cap['alquiler_mes'] - bd['alquiler_mes']) * 12)} menos al año" not in t:
        err.append(f"{cap['slug']}: ahorro al año mal calculado")
    tb = re.search(r'<section id="tabla">(.*?)</section>', raw, re.S).group(1)
    filas = re.findall(r"<tr><td data-v=\"\d+\">\d+</td>(.*?)</tr>", tb, re.S)
    if len(filas) != len(vis) + 1 + len(otras):
        err.append(f"{cap['slug']}: {len(filas)} filas en la tabla (se esperaban {len(vis) + 1 + len(otras)})")
    # columnas numéricas tras la de tipo: alquiler, €/m², superficie, ingresos, alquiler sobre renta
    alq = [float(re.findall(r'<td data-v="([\d.]*)">', f)[0]) for f in filas]
    if alq != sorted(alq):
        err.append(f"{cap['slug']}: la tabla no va del alquiler más bajo al más alto")
    esperados = sorted([x["alquiler_mes"] for x in vis] + [c["alquiler_mes"] for c in [cap] + otras])
    if [round(a, 2) for a in alq] != [round(a, 2) for a in esperados]:
        err.append(f"{cap['slug']}: alquileres de la tabla distintos del JSON")
    ocultos = [x for x in cap["distritos"] if x not in vis]
    for x in ocultos:
        if f'#d{x["numero"]}"' in tb:
            err.append(f"{cap['slug']}: muestra el distrito {x['numero']} con menos de 30 inmuebles")
    for f in filas:
        ing = re.findall(r'<td data-v="([\d.]*)">', f)
        if abs(float(ing[3]) - float(ing[0]) / ab.U) > 0.02:
            err.append(f"{cap['slug']}: ingresos necesarios mal calculados")
            break
comprobar("Páginas de provincia: mediana, distrito más barato, ahorro, ingresos y tabla iguales que el JSON (sin distritos de < 30 inmuebles)", err)

# 4. ranking por comunidad: ciudad más barata y más cara iguales que el JSON
err = []
if DATOS_CCAA.exists():
    prov_cc = {}
    nombres = {}
    for x in json.loads(DATOS_CCAA.read_text(encoding="utf-8"))["comunidades"]:
        prov_cc.update({p: x["cod_ccaa"] for p in x["provincias"]})
    grupos = {}
    for c in todas:
        grupos.setdefault(prov_cc[c["cod_muni"][:2]], []).append(c)
    filas = re.findall(r'<tr id="cc-([^"]+)">(.*?)</tr>', nac, re.S)
    if len(filas) != len(grupos):
        err.append(f"{len(filas)} comunidades en la tabla y {len(grupos)} con ciudades")
    hrefs = [re.findall(r'href="\.\./\.\./([^/"#]+)/"', f) for _, f in filas]
    baratas = {min(cs, key=lambda c: (c["alquiler_mes"], c["nombre"]))["slug"] for cs in grupos.values()}
    caras = {max(cs, key=lambda c: (c["alquiler_mes"], c["nombre"]))["slug"] for cs in grupos.values()}
    vistas_b = {h[-2] if len(h) >= 2 else None for h in hrefs}
    vistas_c = {h[-1] if h else None for h in hrefs}
    if vistas_b != baratas:
        err.append(f"ciudades más baratas distintas del JSON: {sorted(vistas_b ^ baratas)[:6]}")
    if vistas_c != caras:
        err.append(f"ciudades más caras distintas del JSON: {sorted(vistas_c ^ caras)[:6]}")
else:
    err.append("falta comunidades.json")
comprobar("Ranking por comunidad: una fila por comunidad con ciudades, con su ciudad más barata y más cara", err)

# 5. enlaces internos de estas páginas apuntan a páginas que existen
err = []
for r, raw in rutas.items():
    for h in re.findall(r'href="(\.\./\.\./[^"#?]*)', raw):
        destino = (WEB / r / h).resolve()
        if h.endswith("/") and not (destino / "index.html").exists():
            err.append(f"{r}: enlace roto {h}")
comprobar("Todos los enlaces internos llevan a una página que existe", err)

# 6. título sin año, H1 con año, metodología, aviso de distancias y aviso turístico en la costa
err = []
for r, raw in rutas.items():
    tit = re.search(r"<title>(.*?)</title>", raw).group(1)
    if str(ANIO) in tit or len(tit) > 60:
        err.append(f"{r}: título con año o de más de 60 caracteres ({tit})")
    if not re.search(rf"<h1>[^<]*\({ANIO}\)</h1>", raw):
        err.append(f"{r}: el H1 no lleva el año")
    if 'id="metodologia"' not in raw:
        err.append(f"{r}: sin metodología")
for cap, _ in provs:
    raw = rutas[f"{ab.CARPETA}/{cap['slug']}/"]
    if "no tenemos datos oficiales de distancia" not in texto(raw):
        err.append(f"{cap['slug']}: falta el aviso de distancias y transporte")
for slug in ("malaga", "valencia", "alacant-alicante", "las-palmas-de-gran-canaria"):
    raw = rutas.get(f"{ab.CARPETA}/{slug}/")
    if raw and "Ojo con las zonas turísticas" not in raw:
        err.append(f"{slug}: falta el aviso de zonas turísticas")
if "Ojo con las zonas turísticas" in rutas.get(f"{ab.CARPETA}/madrid/", ""):
    err.append("madrid: lleva el aviso de zonas turísticas y no es de costa")
comprobar("Título sin año, año en el H1, metodología, aviso de distancias y aviso turístico solo en la costa", err)

# 7. valor de referencia de Madrid
raw = rutas.get(f"{ab.CARPETA}/madrid/", "")
comprobar("Madrid muestra su alquiler mediano de referencia (868,75 € → 869 €)",
          [] if "menos de 869 € al mes" in texto(raw) else ["no aparece 869 €"])

ok = resultados.count("OK")
print(f"\nTest de alquiler barato: {ok} OK, {len(resultados) - ok} FALLA")
sys.exit(0 if ok == len(resultados) else 1)
