"""Comprobaciones de la evolución de precios en las fichas de ciudad (evolucion_precios.py).

Uso (desde la carpeta del proyecto):   python tests/test_evolucion.py
Solo usa la biblioteca estándar. Imprime OK o FALLA y termina con código 1 si algo falla.
"""
from pathlib import Path
import html
import json
import re
import sys

BASE = Path(__file__).resolve().parent.parent
WEB = BASE / "web"
CIUDADES = BASE / "datos_limpios" / "ciudades_nivel1.json"
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


def n(x):
    return f"{round(x):,}".replace(",", ".")


def d(x, k=1):
    return f"{x:.{k}f}".replace(".", ",")


def texto(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


ciudades = json.loads(CIUDADES.read_text(encoding="utf-8"))["ciudades"]
secciones, tablas = {}, {}
for c in ciudades:
    f = WEB / c["slug"] / "index.html"
    if not f.exists():
        continue
    m = re.search(r'<section id="evolucion">(.*?)</section>', f.read_text(encoding="utf-8"), re.S)
    secciones[c["slug"]] = m.group(1) if m else None
    if m:
        filas = re.findall(r'<tr><th scope="row">(\d{4})</th>(.*?)</tr>', m.group(1), re.S)
        tablas[c["slug"]] = {int(a): [texto(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)] for a, r in filas}
con_pagina = [c for c in ciudades if c["slug"] in secciones
              and sum(1 for s in c["serie_alquiler"] if s["eur_m2"] is not None) >= 3]
sin_serie = [c for c in ciudades if c["slug"] in secciones and c not in con_pagina]
comprobar(f"Las {len(sin_serie)} fichas sin serie de alquiler (menos de 3 años) lo explican",
          [c["nombre"] for c in sin_serie if not secciones[c["slug"]] or "solo tiene datos" not in secciones[c["slug"]]])

comprobar("Todas las fichas tienen la sección de evolución con la tabla año a año",
          [c["nombre"] for c in con_pagina if not secciones[c["slug"]] or c["slug"] not in tablas or not tablas[c["slug"]]])

err = []
for c in con_pagina:
    t = tablas.get(c["slug"], {})
    anios = [s["anio"] for s in c["serie_alquiler"]]
    while anios and next(s for s in c["serie_alquiler"] if s["anio"] == anios[0])["alquiler_mes"] is None:
        anios.pop(0)   # los años sin dato anteriores al primero con dato no se muestran
    if sorted(t) != sorted(anios):
        err.append(f"{c['nombre']}: años {sorted(t)} frente a {anios}")
comprobar("Una fila por cada año de la serie del SERPAVI (desde el primero con dato)", err)

# Valores: alquiler, €/m² y alquiler sobre renta de cada año, recalculados desde el JSON
err = []
for c in con_pagina:
    t = tablas.get(c["slug"], {})
    renta = {s["anio"]: s["renta_hogar"] for s in c["serie_renta"] if s.get("renta_hogar")}
    for s in c["serie_alquiler"]:
        celdas = t.get(s["anio"])
        if celdas is None:
            continue
        if s["alquiler_mes"] is None:
            if not celdas[0].startswith("No disponible") or ("menos de 30" in celdas[0]) != (s["inmuebles"] is not None and s["inmuebles"] < 30):
                err.append(f"{c['nombre']} {s['anio']}: sin dato fiable pero muestra {celdas[0]}")
            continue
        esperado = n(s["alquiler_mes"]) + " €" + ("*" if (s["inmuebles"] or 0) < 100 else "")
        if celdas[0] != esperado:
            err.append(f"{c['nombre']} {s['anio']}: alquiler {celdas[0]} (esperado {esperado})")
        if celdas[1] != d(s["eur_m2"], 2) + " €":
            err.append(f"{c['nombre']} {s['anio']}: €/m² {celdas[2]}")
        r = renta.get(s["anio"])
        pct = d(s["alquiler_mes"] * 12 / r * 100) + " %" if r else "—"
        if celdas[-1] != pct:
            err.append(f"{c['nombre']} {s['anio']}: alquiler sobre renta {celdas[-1]} (esperado {pct})")
comprobar("Alquiler, €/m², * de pocos datos y alquiler sobre renta coinciden con el JSON en cada año", err)

# Valores de referencia del último año
REF = {"madrid": ("869 €", "53.213 €", "19,6 %"), "valencia": ("681 €", "42.374 €", "19,3 %"),
       "valladolid": ("531 €", "39.685 €", "16,1 %")}
err = []
for slug, (alq, renta, pct) in REF.items():
    t = tablas.get(slug, {})
    ult = t.get(max(t)) if t else None
    if not ult or ult[0] != alq or ult[-2] != renta or ult[-1] != pct:
        err.append(f"{slug}: {ult}")
comprobar("Valores de referencia en la fila del último año (Madrid, Valencia, Valladolid)", err)

err = []
for c in con_pagina:
    slug, s = c["slug"], secciones[c["slug"]]
    if not s:
        continue
    t = texto(re.sub(r"<svg.*?</svg>", "", s, flags=re.S))
    for mala in ("nan", "None", "inf"):
        if re.search(rf"\b{mala}\b", t):
            err.append(f"{slug}: aparece '{mala}'")
    if "Ministerio de Vivienda y Agenda Urbana" not in t or "www.ine.es" not in t:
        err.append(f"{slug}: falta la cita de las fuentes bajo la tabla")
comprobar("Sin nan/None y con la cita del Ministerio y del INE bajo la tabla", err)

print()
sys.exit(1 if "FALLA" in resultados else 0)
