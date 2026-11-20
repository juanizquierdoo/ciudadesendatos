"""Páginas legales (B-04): aviso legal, privacidad y cookies.

Uso: python tests/test_legales.py
- Si faltan los datos del titular en paginas_legales.py: PENDIENTE (no falla), y
  comprueba que no se publica ninguna página legal a medias.
- Si están: cada página existe, muestra todos los datos, está en el sitemap y
  todas las páginas de la web la enlazan desde el pie.
- Siempre: la web no usa cookies, almacenamiento local ni recursos de otros
  sitios, porque la política de cookies y la de privacidad lo afirman.
"""
from pathlib import Path
import re
import sys

BASE = Path(__file__).resolve().parent.parent
WEB = BASE / "web"
sys.path.insert(0, str(BASE))
import paginas_legales as pl  # noqa: E402

fallos = 0


def comprobar(descripcion, errores, pendiente=False):
    global fallos
    errores = list(errores)
    estado = "OK" if not errores else ("PENDIENTE" if pendiente else "FALLA")
    if estado == "FALLA":
        fallos += 1
    print(f"[{estado:9}] {descripcion}")
    for e in errores[:8]:
        print("            -", e)
    if len(errores) > 8:
        print(f"            ... y {len(errores) - 8} más")


paginas = {f: f.read_text(encoding="utf-8") for f in WEB.rglob("*.html")}

# 1. Plantilla con datos de prueba (no se escribe nada en disco)
original = dict(pl.TITULAR)
pl.TITULAR.update(nombre="Nombre Prueba Prueba", nif="00000000T",
                  domicilio="Calle Prueba 1, 00000 Ciudad (Provincia)", email="prueba@example.com")
stub = lambda *a, **k: ""
err = []
salida = pl.paginas(stub, stub, stub, stub, "https://ejemplo.es")
if set(salida) != set(pl.PAGINAS):
    err.append(f"genera {sorted(salida)} en lugar de {sorted(pl.PAGINAS)}")
for c in ("aviso-legal", "privacidad"):
    for v in pl.TITULAR.values():
        if v not in salida.get(c, ""):
            err.append(f"{c}: no muestra «{v}»")
for c, h in salida.items():
    if re.search(r"\{\w+\}|\bNone\b", h):
        err.append(f"{c}: variable sin rellenar")
    if "Última actualización" not in h:
        err.append(f"{c}: sin fecha de actualización")
pl.TITULAR.clear()
pl.TITULAR.update(original)
comprobar("Las páginas legales muestran todos los datos del titular (prueba con datos ficticios)", err)

# 2. Lo publicado en web/
pie_legal = [f'href="../{c}/"' for c in pl.PAGINAS]
if not pl.completo():
    faltan = [k for k, v in pl.TITULAR.items() if not str(v).strip()]
    comprobar("Datos del titular rellenos en paginas_legales.py (LSSI art. 10)",
              [f"falta: {', '.join(faltan)}. Hasta tenerlos, no se publican las páginas legales (B-04)"], pendiente=True)
    err = [str(f.relative_to(WEB)) for f in paginas if f.parent.name in pl.PAGINAS]
    err += [f"{f.relative_to(WEB)}: enlaza a páginas legales que no existen" for f, s in paginas.items() if 'class="legal"' in s]
    comprobar("Sin datos del titular no se publica ninguna página legal a medias", err)
else:
    err = []
    for c in pl.PAGINAS:
        f = WEB / c / "index.html"
        if not f.exists():
            err.append(f"falta web/{c}/index.html")
            continue
        s = f.read_text(encoding="utf-8")
        if c != "cookies":
            for v in pl.TITULAR.values():
                if v.strip() not in s.replace("&#x27;", "'").replace("&amp;", "&"):
                    err.append(f"{c}: no muestra «{v}»")
    comprobar("Aviso legal, privacidad y cookies publicados con los datos del titular", err)

    err = []
    for f, s in paginas.items():
        pie = s[s.find("<footer"):]
        rel = "../" * (len(f.relative_to(WEB).parts) - 1)
        for c in pl.PAGINAS:
            if f'href="{rel}{c}/"' not in pie:
                err.append(f"{f.relative_to(WEB)}: el pie no enlaza a {c}")
    comprobar("Todas las páginas enlazan desde el pie a las tres páginas legales", err)

    sm = WEB / "sitemap.xml"
    if sm.exists():
        texto = sm.read_text(encoding="utf-8")
        comprobar("Las páginas legales están en el sitemap",
                  [c for c in pl.PAGINAS if f"/{c}/</loc>" not in texto])

# 3. Lo que afirman las políticas: sin cookies, almacenamiento local ni recursos externos
err = []
for f in WEB.rglob("*.js"):
    s = f.read_text(encoding="utf-8")
    for k in ("cookie", "localStorage", "sessionStorage", "indexedDB"):
        if k in s:
            err.append(f"{f.relative_to(WEB)} usa {k}")
for f, s in paginas.items():
    if re.search(r'<(script|img|iframe|link|source|video|audio)\b[^>]*\s(src|href)="(https?:)?//', s.replace('rel="canonical"', "")):
        for m in re.finditer(r'<(script|img|iframe|link|source|video|audio)\b[^>]*\s(src|href)="((https?:)?//[^"]+)"', s):
            if 'rel="canonical"' not in m.group(0):
                err.append(f"{f.relative_to(WEB)}: carga {m.group(3)}")
    if "document.cookie" in s or "localStorage" in s:
        err.append(f"{f.relative_to(WEB)}: usa cookies o almacenamiento local")
comprobar("La web no usa cookies, almacenamiento local ni recursos de otros sitios (lo dice la política de cookies)", err[:50])

sys.exit(1 if fallos else 0)
