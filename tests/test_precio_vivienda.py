"""Comprobaciones del módulo de precio de compra (precio_vivienda.py, valor tasado del Ministerio de Transportes).

Uso (desde la carpeta del proyecto):   python tests/test_precio_vivienda.py
Solo usa la biblioteca estándar (y xlrd si está datos_originales/35103500.xls, para cotejar el extracto).
Imprime OK o FALLA y termina con código 1 si algo falla.
"""
from pathlib import Path
import html
import json
import re
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
import precio_vivienda as pv  # noqa: E402

WEB = BASE / "web"
CIUDADES = BASE / "datos_limpios" / "ciudades_nivel1.json"
resultados = []

# Leídos a mano en la pestaña T2A2026 del Excel (28/11/2026): valor tasado total, €/m².
REFERENCIA = {"28079": 5418.4, "46250": 2972.8, "47186": 1946.5}


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
datos = pv.cargar()
ultimo = max(p for s in datos.values() for p in s)

comprobar("Las 151 ciudades tienen fila en el extracto en todos los trimestres",
          [c["nombre"] for c in todas if len(datos.get(c["cod_muni"], {})) != len(datos[todas[0]["cod_muni"]])])


err = []
for cod, v in REFERENCIA.items():
    if v is not None and abs(((por_cod[cod].get("compra") or {}).get("valor_m2") or 0) - v) > 0.05:
        err.append(f"{cod}: {(por_cod[cod].get('compra') or {}).get('valor_m2')} (esperado {v})")
comprobar("Valores de referencia (Madrid, Valencia, Valladolid; segundo trimestre de 2026)", err)

if pv.XLS.exists():
    try:
        xls = pv.leer_xls()
        err = []
        for per, filas in xls.items():
            cas = pv.casar(todas, filas)
            for cod, fila in cas.items():
                v, t = datos[cod].get(per, (None, None))
                if v != fila[2] or t != fila[3]:
                    err.append(f"{cod} {per}: extracto {v}/{t}, Excel {fila[2]}/{fila[3]}")
            usados = [f[1] for f in cas.values()]
            if len(usados) != len(set(usados)):
                err.append(f"{per}: una fila del Excel sirve a dos ciudades")
        comprobar("El extracto coincide con el Excel del Ministerio y ninguna fila se usa dos veces", err)
    except ImportError:
        print("[AVISO] xlrd no está instalado: no se coteja el extracto con el Excel")
else:
    print("[AVISO] Falta datos_originales/35103500.xls: no se coteja el extracto con el Excel")

err = []
for c in todas:
    x = c.get("compra")
    if not x:
        continue
    if not (500 <= x["valor_m2"] <= 8000):
        err.append(f"{c['nombre']}: {x['valor_m2']} €/m²")
    if x["rentabilidad"] is not None and not (1.5 <= x["rentabilidad"] <= 12):
        err.append(f"{c['nombre']}: rentabilidad {x['rentabilidad']} %")
comprobar("Valores en rangos razonables (500-8.000 €/m², rentabilidad 1,5-12 %)", err)

err = []
for c in todas:
    h = (WEB / c["slug"] / "index.html").read_text(encoding="utf-8")
    i = h.find('<section id="compra"')
    if i < 0:
        err.append(f"{c['nombre']}: sin sección #compra")
        continue
    s = texto(h[i:h.index("</section>", i)])
    if c.get("compra"):
        if "Ministerio de Transportes" not in s or pv.PUBLICADO not in s or "No es el precio final de venta" not in s:
            err.append(f"{c['nombre']}: falta la fuente, la fecha o el aviso")
        if f"{pv.n(c['compra']['valor_m2'])} €/m²" not in s:
            err.append(f"{c['nombre']}: la cifra de la ficha no es la del JSON")
    elif "No disponible" not in s:
        err.append(f"{c['nombre']}: sin dato y sin «No disponible»")
    if re.search(r"\b(nan|None)\b", s):
        err.append(f"{c['nombre']}: nan o None visible")
    if 'href="#compra"' not in h:
        err.append(f"{c['nombre']}: sin enlace a #compra")
comprobar("Cada ficha tiene la sección de compra con fuente, fecha y aviso", err)

h = (WEB / "comparar-ciudades" / "index.html").read_text(encoding="utf-8")
comprobar("El comparador tiene las filas de compra", [] if "Valor tasado de la vivienda" in h else ["falta la fila"])

sys.exit(1 if "FALLA" in resultados else 0)
