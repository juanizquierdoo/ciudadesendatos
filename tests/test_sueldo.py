"""Comprobaciones de la herramienta "¿Dónde puedo vivir con mi sueldo?" (herramienta_sueldo.py).

Uso (desde la carpeta del proyecto):   python tests/test_sueldo.py
Solo usa la biblioteca estándar. Imprime OK o FALLA y termina con código 1 si algo falla.
La parte interactiva (JavaScript) se prueba aparte en un navegador; aquí se comprueban
los datos incrustados, la parte fija de la página, el sitemap y la portada.
"""
from pathlib import Path
import html
import json
import re
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
import herramienta_sueldo as hs  # noqa: E402
from config import ANIO  # noqa: E402

WEB = BASE / "web"
PAG = WEB / hs.SLUG / "index.html"
DATOS = BASE / "datos_limpios" / "ciudades_nivel1.json"
resultados = []


def comprobar(descripcion, errores):
    errores = list(errores)
    estado = "OK" if not errores else "FALLA"
    resultados.append(estado)
    print(f"[{estado:5}] {descripcion}")
    for e in errores[:8]:
        print("        -", e)


def texto(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))


if not PAG.exists():
    comprobar("Existe la página de la herramienta", [f"falta {PAG}"])
    sys.exit(1)
s = PAG.read_text(encoding="utf-8")
t = texto(s)
ciudades = {c["slug"]: c for c in json.loads(DATOS.read_text(encoding="utf-8"))["ciudades"]}
m = re.search(r'<script type="application/json" id="sueldo-datos">(.*?)</script>', s, re.S)
datos = json.loads(m.group(1).replace("<\\/", "</")) if m else []

comprobar("Datos incrustados en la página", [] if datos else ["no hay bloque sueldo-datos"])

err = []
for nom, slug, prov, cc, alq, ds in datos:
    c = ciudades.get(slug)
    if not c:
        err.append(f"{slug}: no está en el JSON")
        continue
    if abs(c["alquiler_mes"] - alq) > 0.01:
        err.append(f"{nom}: alquiler {alq} ≠ {c['alquiler_mes']}")
    if not (WEB / slug / "index.html").exists():
        err.append(f"{nom}: su ficha no existe")
    por_num = {x["numero"]: x for x in c.get("distritos") or []}
    for num, dn, da, pocos, barrios in ds:
        x = por_num.get(num)
        if x is None or abs(x["alquiler_mes"] - da) > 0.01:
            err.append(f"{nom} distrito {num}: alquiler distinto del JSON")
        elif x["fiabilidad"] not in ("ok", "pocos_datos"):
            err.append(f"{nom} distrito {num}: menos de 30 inmuebles y aun así se usa")
        elif bool(pocos) != (x["fiabilidad"] == "pocos_datos"):
            err.append(f"{nom} distrito {num}: marca de pocos datos mal puesta")
comprobar("Alquiler de cada ciudad y distrito igual que el JSON (y sin distritos de menos de 30 inmuebles)", err)

ref = {"madrid": 868.75, "valencia": 680.83, "valladolid": 530.83}
comprobar("Valores de referencia en los datos de la herramienta",
          [f"{k}: {next((d[4] for d in datos if d[1] == k), None)} ≠ {v}" for k, v in ref.items()
           if next((d[4] for d in datos if d[1] == k), None) != v])

# Ningún código postal ni dato vacío en lo que se ve o en los nombres de distrito
nombres = [d[1] for c in datos for d in c[5]]
comprobar("Ningún código postal en los nombres de distrito ni en el texto",
          [n for n in nombres if re.search(r"\bCP\b|\b\d{5}\b", n)][:5]
          + (["texto con 'CP'"] if re.search(r"\bCP \d", t) else []))
comprobar("Ningún 'nan', 'None', 'null', 'undefined' ni llaves sin rellenar",
          [w for w in ("nan", "None", "null", "undefined") if re.search(rf"\b{w}\b", t)] + (["{"] if re.search(r"\{\w+\}", t) else []))

# Tabla fija: cada fila coincide con el cálculo de resumen()
todas = [c for c in ciudades.values() if c.get("alquiler_pct_renta") is not None and c.get("renta_hogar") and c.get("alquiler_mes")]
slugs = {d[1] for d in datos}
todas = [c for c in todas if c["slug"] in slugs]
err = []
for ing in hs.INGRESOS_REF:
    r = hs.resumen(todas, ing)
    fila = f"{len(r['ciudades'])} de {len(todas)}"
    pat = re.escape(f"{ing:,}".replace(",", ".")) + r" € [\d.]+ € " + re.escape(fila) + " " + re.escape(f"{len(r['distritos'])} de {r['n_distritos']}")
    if not re.search(pat, t):
        err.append(f"{ing} €: no aparece '{fila}' / {len(r['distritos'])} distritos")
    # comprobación independiente de resumen()
    tope = ing * hs.PCT_DEFECTO / 100
    if len(r["ciudades"]) != sum(1 for c in todas if c["alquiler_mes"] <= tope):
        err.append(f"{ing} €: resumen() cuenta mal las ciudades")
comprobar("Tabla 'Hasta dónde llega cada sueldo' correcta", err)

err = []
if "Qué dicen los datos" not in t:
    err.append("falta 'Qué dicen los datos'")
if "Cómo se ha calculado" not in t:
    err.append("falta la metodología")
if "no anuncios" not in t:
    err.append("no explica que son contratos vigentes, no anuncios")
if f"({ANIO})" not in re.search(r"<title>(.*?)</title>", s).group(1):
    err.append("el título no lleva el año")
if "no se envía ni se guarda" not in t:
    err.append("falta la nota de privacidad")
comprobar("Texto propio, metodología, año y aviso de privacidad", err)

err = []
mapa = (WEB / "sitemap.xml").read_text(encoding="utf-8") if (WEB / "sitemap.xml").exists() else ""
if mapa and f"/{hs.SLUG}/</loc>" not in mapa:
    err.append("no está en el sitemap")
if f'href="{hs.SLUG}/"' not in (WEB / "index.html").read_text(encoding="utf-8"):
    err.append("la portada no la enlaza")
comprobar("En el sitemap y enlazada desde la portada", err)

falla = resultados.count("FALLA")
print(f"\n{resultados.count('OK')} OK, {falla} FALLA")
sys.exit(1 if falla else 0)
