"""Comprobaciones de las páginas por comunidad autónoma (B-18).

Uso (desde la carpeta del proyecto):   python tests/test_comunidades.py
Solo usa la biblioteca estándar. Imprime OK o FALLA y termina con código 1 si algo falla.
"""
from pathlib import Path
import json
import re
import sys

BASE = Path(__file__).resolve().parent.parent
WEB = BASE / "web"
CIUDADES = BASE / "datos_limpios" / "ciudades_nivel1.json"
CCAA = BASE / "datos_limpios" / "comunidades.json"
MIN_CIUDADES = 3
# Valores de referencia leídos a mano en la hoja CCAA del SERPAVI 2011-2024 (19/11/2026)
REFERENCIA = {"01": (550.0, 7.35), "13": (800.0, 12.12), "10": (525.78, 6.32)}

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


def leer(ruta):
    f = WEB / ruta / "index.html"
    return f.read_text(encoding="utf-8") if f.exists() else None


ciudades = json.loads(CIUDADES.read_text(encoding="utf-8"))["ciudades"]
ccaa = json.loads(CCAA.read_text(encoding="utf-8"))["comunidades"]
prov_ccaa = {p: x["cod_ccaa"] for x in ccaa for p in x["provincias"]}

comprobar("comunidades.json tiene las 19 comunidades y ciudades autónomas y las 52 provincias",
          ([f"{len(ccaa)} comunidades"] if len(ccaa) != 19 else []) + ([f"{len(prov_ccaa)} provincias"] if len(prov_ccaa) != 52 else []))
comprobar("Valores de referencia del SERPAVI por comunidad (Andalucía, Madrid, C. Valenciana)",
          [f"{c}: {x['alquiler_mes']} / {x['eur_m2']} (esperado {REFERENCIA[c]})" for x in ccaa for c in [x["cod_ccaa"]]
           if c in REFERENCIA and (x["alquiler_mes"], x["eur_m2"]) != REFERENCIA[c]])

por_ccaa = {}
for c in ciudades:
    por_ccaa.setdefault(prov_ccaa[c["cod_muni"][:2]], []).append(c)

# qué comunidades tienen página: las que tienen 3 o más ciudades
paginas = {}
for d in (WEB / "comunidades").glob("*/index.html"):
    s = d.read_text(encoding="utf-8")
    paginas[d.parent.name] = s
errores = []
esperadas = set()
for x in ccaa:
    n = len(por_ccaa.get(x["cod_ccaa"], []))
    # la página de una comunidad enlaza a todas sus ciudades: se identifica por los enlaces de su tabla
    slugs = {c["slug"] for c in por_ccaa.get(x["cod_ccaa"], [])}
    encontradas = [k for k, s in paginas.items() if slugs and set(re.findall(r'<tr id="c-([a-z0-9-]+)"', s)) == slugs]
    if n >= MIN_CIUDADES:
        esperadas.update(encontradas)
        if len(encontradas) != 1:
            errores.append(f"{x['nombre']} ({n} ciudades): {len(encontradas)} páginas con exactamente sus ciudades")
sobran = set(paginas) - esperadas
errores += [f"página de comunidad que no corresponde (o con ciudades de más/menos): {k}" for k in sorted(sobran)]
comprobar(f"Una página por cada comunidad con {MIN_CIUDADES}+ ciudades, con exactamente sus ciudades; ninguna para las demás", errores)

# cada página de comunidad muestra el alquiler oficial de la comunidad
errores = []
for x in ccaa:
    slugs = {c["slug"] for c in por_ccaa.get(x["cod_ccaa"], [])}
    for k, s in paginas.items():
        if set(re.findall(r'<tr id="c-([a-z0-9-]+)"', s)) == slugs:
            esperado = f"{round(x['alquiler_mes']):,}".replace(",", ".") + " €/mes"
            if esperado not in s:
                errores.append(f"{k}: no muestra «{esperado}»")
comprobar("Cada página de comunidad muestra el alquiler mediano oficial de la comunidad", errores)

# cada ciudad de una comunidad con página enlaza a ella (miga de pan visible y JSON-LD)
errores = []
for k, s in paginas.items():
    for slug in re.findall(r'<tr id="c-([a-z0-9-]+)"', s):
        c = leer(slug) or ""
        miga = re.search(r'<nav class="migas".*?</nav>', c)
        if not miga or f'href="../comunidades/{k}/"' not in miga.group(0):
            errores.append(f"{slug}: la miga de pan no enlaza a comunidades/{k}/")
        if f'/comunidades/{k}/"' not in c.split("<body>")[0]:
            errores.append(f"{slug}: la miga de pan del JSON-LD no incluye comunidades/{k}/")
comprobar("Cada ciudad enlaza a su comunidad (miga de pan visible y en datos estructurados)", errores)

# todas las ciudades comparan con su comunidad
errores = [c["slug"] for c in ciudades if "En el conjunto " not in (leer(c["slug"]) or "")]
comprobar("Todas las fichas de ciudad comparan su alquiler con el de su comunidad", errores)

# índice de comunidades: existe y enlaza a todas las páginas
indice = leer("comunidades") or ""
errores = [] if indice else ["falta web/comunidades/index.html"]
errores += [f"el índice no enlaza a {k}" for k in paginas if f'href="../comunidades/{k}/"' not in indice]
comprobar("El índice de comunidades existe y enlaza a todas las páginas de comunidad", errores)

# sitemap: todas las páginas HTML están en el sitemap y viceversa
sm = WEB / "sitemap.xml"
if sm.exists():
    base_url = re.search(r"<loc>(https?://[^/]+)/", sm.read_text(encoding="utf-8")).group(1)
    en_sitemap = {u[len(base_url) + 1:] for u in re.findall(r"<loc>(.*?)</loc>", sm.read_text(encoding="utf-8"))}
    en_web = {("" if f.parent == WEB else f.parent.relative_to(WEB).as_posix() + "/") for f in WEB.rglob("index.html")}
    comprobar("El sitemap tiene todas las páginas (también las de comunidades) y ninguna de más",
              [f"falta en el sitemap: {u}" for u in sorted(en_web - en_sitemap)] + [f"sobra en el sitemap: {u}" for u in sorted(en_sitemap - en_web)])

total_falla = resultados.count("FALLA")
print(f"\n{len(resultados) - total_falla} OK, {total_falla} FALLA")
sys.exit(1 if total_falla else 0)
