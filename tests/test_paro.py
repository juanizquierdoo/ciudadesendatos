"""Comprobaciones del módulo de paro registrado (paro.py, SEPE).

Uso (desde la carpeta del proyecto):   python tests/test_paro.py
Solo usa la biblioteca estándar. Imprime OK o FALLA y termina con código 1 si algo falla.
"""
from pathlib import Path
import csv
import html
import json
import re
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
import paro  # noqa: E402

WEB = BASE / "web"
CIUDADES = BASE / "datos_limpios" / "ciudades_nivel1.json"
resultados = []

# Valores de referencia leídos a mano en los CSV del SEPE (27/11/2026): octubre de 2026 y octubre de 2025.
REFERENCIA = {"28079": (138652, 134318), "46250": (44133, 42634), "47186": (14365, 13656)}


def comprobar(descripcion, errores):
    errores = list(errores)
    estado = "OK" if not errores else "FALLA"
    resultados.append(estado)
    print(f"[{estado:5}] {descripcion}")
    for e in errores[:8]:
        print("        -", e)
    if len(errores) > 8:
        print(f"        ... y {len(errores) - 8} más")


def texto(h):
    return html.unescape(re.sub(r"<[^>]+>", " ", h))


todas = json.loads(CIUDADES.read_text(encoding="utf-8"))["ciudades"]
por_cod = {c["cod_muni"]: c for c in todas}

comprobar("Las 151 ciudades tienen paro registrado",
          [c["nombre"] for c in todas if not c.get("paro")] + ([] if len(todas) == 151 else [f"{len(todas)} ciudades"]))

err = []
for cod, (tot, ant) in REFERENCIA.items():
    p = (por_cod.get(cod) or {}).get("paro") or {}
    if p.get("total") != tot or p.get("anterior") != ant:
        err.append(f"{cod}: {p.get('total')} / {p.get('anterior')} (esperado {tot} / {ant})")
comprobar("Valores de referencia del SEPE (Madrid, Valencia, Valladolid)", err)

err = []
for c in todas:
    p = c.get("paro")
    if not p:
        continue
    det = p["detalle"]
    sexo = [det[k] for k in paro.COL_DET[1:7]]
    sect = [det[k] for k in paro.COL_DET[7:]]
    if None not in sexo and sum(sexo) != p["total"]:
        err.append(f"{c['nombre']}: sexo y edad suman {sum(sexo)}, total {p['total']}")
    if None not in sect and sum(sect) != p["total"]:
        err.append(f"{c['nombre']}: sectores suman {sum(sect)}, total {p['total']}")
    ult = [s["total"] for s in p["serie"] if s["anio"] == int(p["mes"][:4])]
    if ult != [p["total"]]:
        err.append(f"{c['nombre']}: la serie no acaba en el total del último mes")
comprobar("El desglose suma el total y la serie acaba en el último mes", err)

err = []
for c in todas:
    p = c.get("paro")
    if p and p["por_100"] is not None and not (1 <= p["por_100"] <= 25):
        err.append(f"{c['nombre']}: {p['por_100']} parados por 100 habitantes de 18 a 64")
comprobar("Parados por cada 100 habitantes de 18 a 64 años en un rango razonable (1-25)", err)

err = []
for c in todas:
    ruta = WEB / c["slug"] / "index.html"
    if not ruta.exists():
        err.append(f"falta {ruta}")
        continue
    h = ruta.read_text(encoding="utf-8")
    i = h.find('<section id="empleo"')
    if i < 0:
        err.append(f"{c['nombre']}: sin sección #empleo")
        continue
    s = texto(h[i:h.index("</section>", i)])
    if "SEPE" not in s or "CC BY 4.0" not in s or paro.DESCARGA not in s:
        err.append(f"{c['nombre']}: falta la fuente, la licencia o la fecha")
    if "No es la tasa de paro" not in s:
        err.append(f"{c['nombre']}: falta el aviso de que no es la tasa de paro")
    if f"{paro.n(c['paro']['total'])} personas" not in s:
        err.append(f"{c['nombre']}: la cifra de la ficha no es la del JSON")
    if re.search(r"\b(nan|None)\b", s):
        err.append(f"{c['nombre']}: nan o None visible")
    if 'href="#empleo"' not in h:
        err.append(f"{c['nombre']}: sin enlace a #empleo en «En esta página»")
comprobar("Cada ficha tiene la sección de paro con fuente, licencia, fecha y aviso", err)

# el extracto es idéntico al detalle del JSON (ninguna cifra cambiada)
err = []
with open(sorted(paro.CARPETA.glob("paro_detalle_*.csv"))[-1], encoding="utf-8") as f:
    for fila in csv.DictReader(f, delimiter=";"):
        p = (por_cod.get(fila["cod"]) or {}).get("paro")
        if p and any(p["detalle"][k] != paro.num(fila[k]) for k in paro.COL_DET):
            err.append(fila["cod"])
comprobar("El JSON reproduce el extracto del SEPE sin cambios", err)

h = (WEB / "comparar-ciudades" / "index.html").read_text(encoding="utf-8")
comprobar("El comparador tiene las filas de paro", [] if "Parados por cada 100 habitantes" in h else ["falta la fila"])

sys.exit(1 if "FALLA" in resultados else 0)
