"""Comprobaciones SEO de la web generada (web/).

Uso (desde la carpeta del proyecto):   python tests/test_seo.py
Solo usa la biblioteca estándar. Imprime OK o FALLA y termina con código 1 si algo falla.
"""
from pathlib import Path
import html
import json
import re
import sys

BASE = Path(__file__).resolve().parent.parent
WEB = BASE / "web"
DATOS = BASE / "datos_limpios" / "ciudades_nivel1.json"
TITULO_MAX = 65      # Google suele cortar hacia los 60 caracteres; margen pequeño
DESC_MAX = 160

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


def campo(patron, s):
    m = re.search(patron, s, re.S)
    return html.unescape(m.group(1)) if m else None


paginas = {}
for f in sorted(WEB.rglob("index.html")):
    ruta = f.parent.relative_to(WEB).as_posix()
    paginas["" if ruta == "." else ruta + "/"] = f.read_text(encoding="utf-8")
datos = json.loads(DATOS.read_text(encoding="utf-8"))
ciudades = {c["slug"] + "/": c for c in datos["ciudades"]}

titulos = {r: campo(r"<title>(.*?)</title>", s) for r, s in paginas.items()}
descs = {r: campo(r'<meta name="description" content="(.*?)"', s) for r, s in paginas.items()}

comprobar("Todas las páginas tienen título y descripción",
          [r or "portada" for r in paginas if not titulos[r] or not descs[r]])
comprobar(f"Títulos de {TITULO_MAX} caracteres o menos",
          [f"{r}: {len(t)} car." for r, t in titulos.items() if t and len(t) > TITULO_MAX])
comprobar(f"Descripciones de {DESC_MAX} caracteres o menos",
          [f"{r}: {len(t)} car." for r, t in descs.items() if t and len(t) > DESC_MAX])
comprobar("Títulos y descripciones sin repetir",
          [f"repetido: {t}" for t in set(titulos.values()) if list(titulos.values()).count(t) > 1]
          + [f"repetida: {t}" for t in set(descs.values()) if list(descs.values()).count(t) > 1])

# la descripción no promete desglose por distrito si la ciudad no lo tiene
comprobar("La descripción solo habla de distritos si la ciudad los tiene",
          [r for r, c in ciudades.items() if r in descs and not c["distritos"] and "distrito" in descs[r].lower()])

# JSON-LD válido y coherente con la página
errores = []
for r, s in paginas.items():
    bloques = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    if not bloques:
        errores.append(f"{r or 'portada'}: sin datos estructurados")
        continue
    for b in bloques:
        try:
            obj = json.loads(b)
        except ValueError as e:
            errores.append(f"{r or 'portada'}: JSON-LD no válido ({e})")
            continue
        if obj.get("@context") != "https://schema.org" or "@type" not in obj:
            errores.append(f"{r or 'portada'}: falta @context o @type")
        if obj.get("@type") == "Dataset":
            for k in ("name", "description", "isBasedOn", "temporalCoverage", "spatialCoverage"):
                if k not in obj:
                    errores.append(f"{r or 'portada'}: Dataset sin {k}")
            if obj.get("description") != descs[r]:
                errores.append(f"{r or 'portada'}: la descripción del Dataset no coincide con la de la página")
        if obj.get("@type") == "BreadcrumbList":
            for it in obj["itemListElement"]:
                if not str(it.get("item", "")).startswith("http"):
                    errores.append(f"{r}: miga de pan sin URL absoluta")
comprobar("Datos estructurados (JSON-LD) en todas las páginas, válidos y coherentes", errores)

# cifras del JSON-LD/descripción = cifras de la ficha (Madrid, Valencia, Valladolid)
REF = {"madrid/": ("869 €", "19,6 %"), "valencia/": ("681 €", "19,3 %"), "valladolid/": ("531 €", "16,1 %")}
comprobar("La descripción de las ciudades de referencia muestra sus valores",
          [f"{r}: {descs.get(r)}" for r, (a, p) in REF.items() if a not in (descs.get(r) or "") or p not in (descs.get(r) or "")])

# favicon e imagen para compartir
comprobar("Favicon como archivo (no incrustado) y presente en web/",
          [r or "portada" for r, s in paginas.items() if 'rel="icon"' not in s or "data:image" in campo(r'<link rel="icon"[^>]*href="([^"]*)"', s)]
          + [f"falta web/{x}" for x in ("favicon.png", "favicon.ico", "og.png") if not (WEB / x).exists()])

# cada ficha enlaza a los 4 rankings y la fila de destino existe
errores = []
for r, c in ciudades.items():
    s = paginas.get(r, "")
    enl = re.findall(r'href="\.\./rankings/([a-z0-9-]+)/#(c-[a-z0-9-]+)"', s)
    if len(enl) != 4:
        errores.append(f"{r}: {len(enl)} enlaces a rankings (se esperaban 4)")
    for rk, ancla in enl:
        if f'id="{ancla}"' not in paginas.get(f"rankings/{rk}/", ""):
            errores.append(f"{r}: no existe la fila #{ancla} en rankings/{rk}/")
comprobar("Cada ciudad enlaza a su fila en los 4 rankings", errores)

# con dominio: canonical, og:url, og:image absolutos; sin dominio: no deben aparecer a medias
con_dominio = (WEB / "sitemap.xml").exists()
if con_dominio:
    comprobar("Con dominio: canonical, og:url y og:image en todas las páginas",
              [r or "portada" for r, s in paginas.items()
               if not all(x in s for x in ('rel="canonical" href="http', 'og:url" content="http', 'og:image" content="http'))])
else:
    comprobar("Sin dominio todavía: no hay canonical ni og:image con dirección relativa",
              [r or "portada" for r, s in paginas.items() if 'rel="canonical"' in s or 'og:image' in s])

# el pie no deja plantillas sin rellenar (p. ej. "{FECHA_SERPAVI}") y cita la fecha de cada fuente
errores = []
for r, s in paginas.items():
    pie_ = campo(r"<footer>(.*?)</footer>", s) or ""
    if "{" in pie_ or "}" in pie_:
        errores.append(f"{r or 'portada'}: llaves sin rellenar en el pie")
    if len(re.findall(r"actualizado el \d{2}/\d{2}/\d{4}", pie_)) < 2:
        errores.append(f"{r or 'portada'}: el pie no da la fecha de las dos fuentes")
comprobar("El pie cita la fecha de actualización de cada fuente, sin llaves sin rellenar", errores)

# licencia propia (CC BY 4.0) en el pie y en cada Dataset
LIC = "https://creativecommons.org/licenses/by/4.0/"
errores = []
for r, s in paginas.items():
    if f'href="{LIC}' not in s or 'rel="license"' not in s:
        errores.append(f"{r or 'portada'}: el pie no enlaza la licencia CC BY 4.0")
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        obj = json.loads(b)
        if obj.get("@type") == "Dataset" and not str(obj.get("license", "")).startswith(LIC):
            errores.append(f"{r or 'portada'}: Dataset sin license CC BY 4.0")
comprobar("Licencia CC BY 4.0 en el pie y en los datos estructurados", errores)

total_falla = resultados.count("FALLA")
print(f"\n{len(resultados) - total_falla} OK, {total_falla} FALLA")
sys.exit(1 if total_falla else 0)
