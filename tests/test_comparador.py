"""Comprobaciones del comparador de ciudades (comparador_ciudades.py).

Uso (desde la carpeta del proyecto):   python tests/test_comparador.py
Solo usa la biblioteca estándar. Imprime OK o FALLA y termina con código 1 si algo falla.
La parte interactiva (JavaScript) se prueba aparte en un navegador; aquí se comprueban
los datos incrustados, la tabla fija, los enlaces, el sitemap, la portada y las fichas.
"""
from pathlib import Path
import html
import json
import re
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
import comparador_ciudades as cmp  # noqa: E402
from config import ANIO  # noqa: E402

WEB = BASE / "web"
PAG = WEB / cmp.SLUG / "index.html"
DATOS = BASE / "datos_limpios" / "ciudades_nivel1.json"
REFERENCIA = {"madrid": (868.75, 53213, 19.6), "valencia": (680.83, 42374, 19.3), "valladolid": (530.83, 39685, 16.1)}
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


def bloque(s, id_):
    m = re.search(rf'<script type="application/json" id="{id_}">(.*?)</script>', s, re.S)
    return json.loads(m.group(1).replace("<\\/", "</")) if m else None


if not PAG.exists():
    comprobar("Existe la página del comparador", [f"falta {PAG}"])
    sys.exit(1)
s = PAG.read_text(encoding="utf-8")
t = texto(s)
ciudades = {c["slug"]: c for c in json.loads(DATOS.read_text(encoding="utf-8"))["ciudades"]}
datos, filas, meta = bloque(s, "cmp-datos"), bloque(s, "cmp-filas"), bloque(s, "cmp-meta")
comprobar("Datos, filas y ajustes incrustados en la página", [] if datos and filas and meta else ["falta algún bloque cmp-*"])

# 1. Cada ciudad de los datos tiene ficha y sus cifras coinciden con el JSON
err = []
fichas = {p.parent.name for p in WEB.glob("*/index.html")}
for c in datos:
    o = ciudades.get(c["s"])
    if not o:
        err.append(f"{c['s']}: no está en el JSON")
        continue
    if c["s"] not in fichas:
        err.append(f"{c['n']}: su ficha no existe")
    for k, kj in (("alq", "alquiler_mes"), ("renta", "renta_hogar"), ("pcr", "alquiler_pct_renta"), ("pob", "poblacion")):
        if c["v"][k] is None or abs(c["v"][k] - o[kj]) > 0.01:
            err.append(f"{c['n']}: {k} {c['v'][k]} ≠ {o[kj]}")
    if abs(c["v"]["sueldo"] - o["alquiler_mes"] / 0.3) > 0.01:
        err.append(f"{c['n']}: ingresos para el 30 % mal calculados")
n_fichas = len([x for x in fichas if x in ciudades])
if len(datos) != n_fichas:
    err.append(f"{len(datos)} ciudades en el comparador y {n_fichas} fichas de ciudad")
comprobar("Las ciudades del comparador son las de las fichas y sus cifras coinciden con el JSON", err)

# 2. Valores de referencia
err = []
by = {c["s"]: c for c in datos}
for slug, (alq, renta, pcr) in REFERENCIA.items():
    c = by.get(slug)
    if not c:
        err.append(f"falta {slug}")
    elif (c["v"]["alq"], c["v"]["renta"], c["v"]["pcr"]) != (alq, renta, pcr):
        err.append(f"{slug}: {c['v']['alq']} / {c['v']['renta']} / {c['v']['pcr']}")
for frag in ("869 € al mes", "53.213 € al año", "19,6 %"):     # Madrid está en la comparación por defecto
    if frag not in t:
        err.append(f"no se ve «{frag}» (Madrid) en la tabla fija")
comprobar("Valores de referencia (Madrid, Valencia, Valladolid)", err)

# 3. Cambios calculados igual que el ranking "dónde más sube el alquiler"
err = []
A0 = ANIO - cmp.AÑOS_CAMBIO
for c in datos:
    o = ciudades[c["s"]]
    s0 = next((x["alquiler_mes"] for x in o["serie_alquiler"] if x["anio"] == A0 and x.get("alquiler_mes") is not None), None)
    s1 = next((x["alquiler_mes"] for x in o["serie_alquiler"] if x["anio"] == ANIO and x.get("alquiler_mes") is not None), None)
    esperado = None if not s0 or s1 is None else round((s1 / s0 - 1) * 100, 4)
    if c["v"]["ch5"] != esperado:
        err.append(f"{c['n']}: cambio {A0}-{ANIO} {c['v']['ch5']} ≠ {esperado}")
    if any(p[1] is None for p in c["ser"]):
        err.append(f"{c['n']}: año sin dato en la serie del gráfico")
comprobar(f"Cambio del alquiler {A0}-{ANIO} y series sin huecos", err)

# 4. Distritos: misma regla que la ficha, ancla existente y sin código postal
err = []
for c in datos:
    o = ciudades[c["s"]]
    por_num = {x["numero"]: x for x in o.get("distritos") or []}
    ficha = (WEB / c["s"] / "index.html").read_text(encoding="utf-8") if c["s"] in fichas else ""
    for k in ("dmin", "dmax"):
        x = c[k]
        if not x:
            continue
        d = por_num.get(x[0])
        if not d or d["fiabilidad"] not in ("ok", "pocos_datos") or d.get("alquiler_mes") is None:
            err.append(f"{c['n']} {k}: distrito {x[0]} sin alquiler publicable")
            continue
        if abs(d["alquiler_mes"] - x[2]) > 0.01:
            err.append(f"{c['n']} {k}: alquiler {x[2]} ≠ {d['alquiler_mes']}")
        if f'id="d{x[0]}"' not in ficha:
            err.append(f"{c['n']}: la ficha no tiene el ancla #d{x[0]}")
        if re.search(r"\bCP\b|\b\d{5}\b", x[1]):
            err.append(f"{c['n']}: «{x[1]}» parece llevar un código postal")
        if re.fullmatch(r"Distrito \d+", x[1]):
            err.append(f"{c['n']}: «{x[1]}» solo es un número")
    validos = [x for x in o.get("distritos") or [] if x["fiabilidad"] in ("ok", "pocos_datos") and x.get("alquiler_mes") is not None]
    if c["v"]["nd"] != len(validos):
        err.append(f"{c['n']}: {c['v']['nd']} distritos con dato ≠ {len(validos)}")
    if len(validos) >= 2 and not (c["dmin"] and c["dmax"]):
        err.append(f"{c['n']}: faltan los distritos extremos")
    if len(validos) >= 2 and (c["dmin"][2] != round(min(x["alquiler_mes"] for x in validos), 2)
                              or c["dmax"][2] != round(max(x["alquiler_mes"] for x in validos), 2)):
        err.append(f"{c['n']}: el distrito más barato o el más caro no es el que toca")
if re.search(r"\bCP\s*\d{5}|\bC\.P\.|[Cc][óo]digos? postal", s):
    err.append("la página menciona códigos postales")
comprobar("Distritos más barato y más caro: regla de los 30 inmuebles, ancla en la ficha y sin código postal", err)

# 5. Tabla fija: las 4 ciudades más pobladas, todas las filas y los mismos textos que calcula el JavaScript
err = []
defecto = sorted(datos, key=lambda c: (-c["pob"], c["n"]))[:cmp.N_DEFECTO]
cab = re.search(r'<table class="cmp"><thead>(.*?)</thead>', s, re.S)
for c in defecto:
    if not cab or f'href="../{c["s"]}/"' not in cab.group(1):
        err.append(f"{c['n']} no está en la tabla fija")
for f in filas:
    if html.escape(f[1].replace("'", "’"), quote=True) not in s:
        err.append(f"falta la fila «{f[1]}»")
    if f[0] not in ("dmin", "dmax") and any(f[0] not in c["v"] for c in datos):
        err.append(f"fila «{f[0]}» sin dato en alguna ciudad")


class GW:   # lo mínimo de generar_web para claves_sel()
    import generar_web as _g
    n, d, esc = staticmethod(_g.n), staticmethod(_g.d), staticmethod(_g.esc)


for p in cmp.claves_sel(GW, defecto):
    if html.unescape(GW.esc(p)) not in t:
        err.append(f"no se ve la frase «{p[:60]}…»")
if cmp.claves_sel(GW, defecto[:1]) != ["Elige al menos dos ciudades para ver las diferencias."]:
    err.append("con una sola ciudad no pide elegir otra")
comprobar("Tabla fija con las 4 ciudades más pobladas, todas las filas y las frases de diferencias", err)

# 6. Enlaces de ejemplo, portada, sitemap y fichas
err = []
ej = re.findall(r'href="\./\?c=([^"]+)"', s)
if len(ej) < 3:
    err.append(f"solo {len(ej)} comparaciones de ejemplo")
for q in ej:
    for slug in q.split(","):
        if slug not in by:
            err.append(f"ejemplo con una ciudad que no existe: {slug}")
if f'href="{cmp.SLUG}/"' not in (WEB / "index.html").read_text(encoding="utf-8"):
    err.append("la portada no enlaza al comparador")
mapa = WEB / "sitemap.xml"
if mapa.exists() and f"/{cmp.SLUG}/</loc>" not in mapa.read_text(encoding="utf-8"):
    err.append("no está en el sitemap")
sin = [c["s"] for c in datos if c["s"] in fichas
       and f'../{cmp.SLUG}/?c={c["s"]}"' not in (WEB / c["s"] / "index.html").read_text(encoding="utf-8")]
if sin:
    err.append(f"{len(sin)} fichas sin enlace al comparador: {sin[:5]}")
comprobar("Comparaciones de ejemplo válidas, tarjeta en la portada, sitemap y enlace desde cada ficha", err)

# 7. Metodología, año, aviso turístico y privacidad
err = [f"falta «{x}»" for x in ("Cómo se ha calculado", "Estimación propia", "Ojo con las zonas turísticas",
                                 "No se envía ni se guarda nada", f"datos de {ANIO}") if x not in t]
if meta and meta.get("max") != 4:
    err.append("el máximo de ciudades no es 4")
comprobar("Metodología, año de los datos, aviso de zonas turísticas y privacidad", err)

print(f"Test del comparador: {resultados.count('OK')} OK, {resultados.count('FALLA')} FALLA")
sys.exit(1 if "FALLA" in resultados else 0)
