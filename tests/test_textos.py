"""Comprobaciones del texto explicativo de las fichas de ciudad (textos_ciudad.py, B-17).

Uso (desde la carpeta del proyecto):   python tests/test_textos.py
Solo usa la biblioteca estándar. Imprime OK o FALLA y termina con código 1 si algo falla.
"""
from pathlib import Path
import html
import json
import re
import statistics
import sys

BASE = Path(__file__).resolve().parent.parent
WEB = BASE / "web"
CIUDADES = BASE / "datos_limpios" / "ciudades_nivel1.json"
MIN_PALABRAS = 150   # texto propio mínimo por ficha
MIN_PARRAFOS = 5

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


ciudades = json.loads(CIUDADES.read_text(encoding="utf-8"))["ciudades"]
textos, parrafos = {}, {}
sin_seccion = []
for c in ciudades:
    f = WEB / c["slug"] / "index.html"
    if not f.exists():
        continue   # ciudades sin página (sin alquiler o renta): las cubren los otros tests
    m = re.search(r'<section id="claves"[^>]*>(.*?)</section>', f.read_text(encoding="utf-8"), re.S)
    if not m:
        sin_seccion.append(c["nombre"])
        continue
    ps = [re.sub(r"<[^>]+>", "", p) for p in re.findall(r"<p>(.*?)</p>", m.group(1), re.S)]
    parrafos[c["slug"]] = ps
    textos[c["slug"]] = html.unescape(" ".join(ps))
con_pagina = [c for c in ciudades if c["slug"] in textos]

comprobar("Todas las fichas de ciudad tienen la sección 'Qué dicen los datos'", sin_seccion)
comprobar(f"Cada texto tiene al menos {MIN_PARRAFOS} párrafos y {MIN_PALABRAS} palabras",
          [f"{s}: {len(parrafos[s])} párrafos, {len(t.split())} palabras" for s, t in textos.items()
           if len(parrafos[s]) < MIN_PARRAFOS or len(t.split()) < MIN_PALABRAS])
comprobar("Ningún 'nan', 'None', 'null' ni llaves sin rellenar en el texto",
          [s for s, t in textos.items() if re.search(r"\b(nan|None|null|inf)\b|[{}]", t)])
comprobar("Cada texto es distinto (ningún párrafo repetido literalmente entre ciudades)",
          [f"párrafo repetido en {len(v)} fichas: {p[:60]}…" for p, v in
           {p: [s for s, ps in parrafos.items() if p in ps] for ps in parrafos.values() for p in ps}.items() if len(v) > 1])

# las cifras del texto salen de los datos
err = []
for c in con_pagina:
    t = textos[c["slug"]]
    for etiqueta, cifra in [("alquiler", f"{n(c['alquiler_mes'])} € al mes"), ("renta", f"{n(c['renta_hogar'])} € al año"),
                            ("peso", f"{d(c['alquiler_pct_renta'])} % de la renta"), ("€/m²", f"{d(c['eur_m2'], 2)} €/m²")]:
        if cifra not in t:
            err.append(f"{c['nombre']}: falta {etiqueta} ({cifra})")
comprobar("Alquiler, renta, peso y €/m² del texto coinciden con el JSON", err)

med = statistics.median(c["alquiler_mes"] for c in con_pagina)
err = [c["nombre"] for c in con_pagina if f"la mediana de las {len(con_pagina)} " not in textos[c["slug"]]
       or f"({n(med)} €)" not in textos[c["slug"]]]
comprobar(f"Mediana de comparación correcta ({n(med)} €, {len(con_pagina)} ciudades)", err)

# valores de referencia
REF = {"madrid": ["869 € al mes", "53.213 € al año", "19,6 % de la renta", "de Madrid subió de 825 a 869 € al mes",
                  "Chamberí (1.175 € al mes)", "Villaverde (688 €)"],
       "valladolid": ["531 € al mes", "39.685 € al año", "16,1 % de la renta", "de Valladolid subió de 500 a 531 € al mes"],
       "valencia": ["681 € al mes", "42.374 € al año", "19,3 % de la renta"]}
comprobar("Valores de referencia en el texto (Madrid, Valencia, Valladolid)",
          [f"{s}: falta «{x}»" for s, xs in REF.items() for x in xs if x not in textos.get(s, "")])

# el texto no afirma más subida que la real: comprueba el signo del cambio interanual
err = []
for c in con_pagina:
    serie = {s["anio"]: s["alquiler_mes"] for s in c["serie_alquiler"] if s.get("alquiler_mes")}
    anios = sorted(serie)
    if len(anios) >= 2 and anios[-2] == anios[-1] - 1:
        a0, a1 = serie[anios[-2]], serie[anios[-1]]
        verbo = "subió" if a1 > a0 else ("bajó" if a1 < a0 else "se mantuvo")
        if f"el alquiler mediano de {c['nombre'].replace(chr(39), '’')} {verbo}" not in textos[c["slug"]]:
            err.append(f"{c['nombre']}: {a0} -> {a1}, se esperaba «{verbo}»")
comprobar("Sentido del cambio del último año coherente con la serie", err)

print(f"\nTest de textos: {resultados.count('OK')} OK, {resultados.count('FALLA')} FALLA")
sys.exit(1 if "FALLA" in resultados else 0)
