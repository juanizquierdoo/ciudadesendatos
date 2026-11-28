"""Módulo de precio de compra de la vivienda (Fase 3, módulo 2).

Fuente: «Valor tasado medio de vivienda libre de los municipios mayores de 25.000 habitantes», tabla del
Boletín Estadístico del Ministerio de Transportes (fichero 35103500.xls, una pestaña por trimestre desde 2005).
Reutilización permitida, también comercial, según el aviso legal de transportes.gob.es (citar la fuente,
indicar la fecha de actualización y no desnaturalizar). FUENTES.md, fuente 11.
Es el valor que asignan las sociedades de tasación (sobre todo para hipotecas), en € por m²; NO es el precio
final de venta. «n.r» = dato no representativo o sin observaciones: aquí es None y en la web «no disponible».

El Excel no trae códigos INE: cada ciudad se casa por nombre (con las variantes de ALIAS). El test comprueba
que las 151 ciudades encuentran una fila y que ninguna fila sirve a dos ciudades.

Archivos:
- datos_originales/35103500.xls (lo descarga Juan; fuera de git).
- datos_municipales/mivau_valor_tasado/valor_tasado_trimestres.csv: extracto, sin cambiar ninguna cifra,
  de las 151 ciudades (cod;periodo;valor_m2;tasaciones), desde 2015. Está en git.

Actualizar (cada trimestre): bajar de nuevo el .xls a datos_originales/, `python precio_vivienda.py --extraer`,
cambiar DESCARGA y `python actualizar.py --desde 4`.

Lo usan preparar_json.py (aportar), generar_web.py (seccion, sección #compra de la ficha) y comparador_ciudades.py.
Test: tests/test_precio_vivienda.py.
"""
import csv
import html
import re
import sys
import unicodedata
from pathlib import Path
from statistics import median

from config import ANIO

BASE = Path(__file__).parent
XLS = BASE / "datos_originales" / "35103500.xls"
CARPETA = BASE / "datos_municipales" / "mivau_valor_tasado"
EXTRACTO = CARPETA / "valor_tasado_trimestres.csv"
URL = "https://cdn.transportes.gob.es/estadistica/BoletinOnline2/35103500.xls"
DESCARGA = "28/11/2026"     # fecha de descarga del .xls (cambiar al actualizar)
PUBLICADO = "09/10/2026"    # última modificación del .xls en el servidor del Ministerio
ANIO_DESDE = 2015

TRIM = {1: "primer", 2: "segundo", 3: "tercer", 4: "cuarto"}

# Nombre de la ciudad en la web -> nombre en el Excel, cuando no casan solos (comprobado a mano el 28/11/2026).
ALIAS = {
    "07040": "Palma de Mallorca",
    "01059": "Vitoria",
    "12040": "Castellón de la Plana",
    "38023": "San Cristóbal Laguna",
    "08245": "Santa Coloma Gramanet",
    "11027": "Puerto de Santa María",
    "12135": "Villarreal/Vila-real",
}


# ------------------------------------------------------------------ formato
def esc(s):
    return html.escape(str(s).replace("'", "’"), quote=True)


def n(x):
    return f"{round(x):,}".replace(",", ".")


def d(x, k=1):
    return f"{x:.{k}f}".replace(".", ",")


def signo(x, k=1):
    return ("+" if x > 0 else "−" if x < 0 else "") + d(abs(x), k) + " %"


def cambio(a, b):
    return None if (a is None or b is None or a == 0) else (b / a - 1) * 100


def periodo_texto(p):
    """'2026T2' -> 'segundo trimestre de 2026'."""
    return f"{TRIM[int(p[-1])]} trimestre de {p[:4]}"


# ------------------------------------------------------------------ casar nombres
def claves(nombre):
    """Variantes normalizadas de un nombre: 'Elche/Elx' -> {elche, elx, elcheelx}; 'Ejido (El)' -> {elejido}."""
    out = set()
    for parte in [nombre] + str(nombre).split("/"):
        t = parte.strip()
        m = re.match(r"^(.*?)\s*\(([^)]*)\)$", t)
        if m:
            t = m.group(2) + " " + m.group(1)
        t = unicodedata.normalize("NFD", t.lower())
        t = "".join(ch for ch in t if not unicodedata.combining(ch))
        t = re.sub(r"[^a-z0-9]", "", t)
        if t:
            out.add(t)
    return out


def leer_xls():
    """{periodo 'AAAAT#': [(provincia, municipio, valor o None, tasaciones o None)]} desde ANIO_DESDE."""
    import xlrd
    b = xlrd.open_workbook(str(XLS))
    out = {}
    for hoja in b.sheet_names():
        m = re.match(r"T([1-4])A(\d{4})", hoja.strip())
        if not m or int(m.group(2)) < ANIO_DESDE:
            continue
        s = b.sheet_by_name(hoja)
        cab = next(r for r in range(min(30, s.nrows)) if str(s.cell_value(r, 1)).strip() == "Provincia")
        tot = [c for c in range(s.ncols) if str(s.cell_value(cab + 1, c)).strip() == "Total"]
        if len(tot) != 2:
            raise ValueError(f"Hoja {hoja}: no encuentro las dos columnas «Total»")
        filas, prov = [], ""
        for r in range(cab + 2, s.nrows):
            p, mu = str(s.cell_value(r, 1)).strip(), str(s.cell_value(r, 2)).strip()
            if p.startswith("n.r"):
                break
            if p:
                prov = p
            if not mu:
                continue
            v, t = s.cell_value(r, tot[0]), s.cell_value(r, tot[1])
            filas.append((prov, mu, v if isinstance(v, float) else None, int(t) if isinstance(t, float) else None))
        out[f"{m.group(2)}T{m.group(1)}"] = filas
    return out


def casar(ciudades, filas):
    """{cod_muni: fila} para un trimestre. Error si una ciudad casa con 2 filas."""
    out = {}
    for c in ciudades:
        k = claves(ALIAS.get(c["cod_muni"], c["nombre"]))
        hits = [f for f in filas if claves(f[1]) & k]
        if len(hits) > 1:
            raise ValueError(f"{c['nombre']}: casa con varias filas {[h[1] for h in hits]}")
        if hits:
            out[c["cod_muni"]] = hits[0]
    return out


def extraer(ciudades):
    datos = leer_xls()
    CARPETA.mkdir(parents=True, exist_ok=True)
    sin = set()
    with open(EXTRACTO, "w", encoding="utf-8", newline="") as f:
        f.write("cod;periodo;municipio_xls;valor_m2;tasaciones\n")
        for per in sorted(datos):
            cas = casar(ciudades, datos[per])
            for c in ciudades:
                fila = cas.get(c["cod_muni"])
                if not fila:
                    sin.add((per, c["nombre"]))
                    continue
                f.write(f"{c['cod_muni']};{per};{fila[1]};{'' if fila[2] is None else fila[2]};{'' if fila[3] is None else fila[3]}\n")
    ult = max(datos)
    print(f"Extracto rehecho: {len(datos)} trimestres ({min(datos)}-{ult}).")
    falt = sorted(nm for p, nm in sin if p == ult)
    if falt:
        print("Sin fila en el último trimestre:", falt)


# ------------------------------------------------------------------ carga y aportación al JSON
def cargar():
    """{cod: {periodo: (valor o None, tasaciones o None)}}."""
    out = {}
    with open(EXTRACTO, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            out.setdefault(r["cod"], {})[r["periodo"]] = (float(r["valor_m2"]) if r["valor_m2"] else None,
                                                          int(r["tasaciones"]) if r["tasaciones"] else None)
    return out


def media_anio(series, anio):
    """Media de los 4 trimestres de un año; None si falta alguno (no se estima)."""
    vs = [series.get(f"{anio}T{q}", (None, None))[0] for q in (1, 2, 3, 4)]
    return None if None in vs else sum(vs) / 4


def aportar(ciudades):
    datos = cargar()
    ultimo = max(p for s in datos.values() for p in s)
    q = ultimo[-1]
    for c in ciudades:
        s = datos.get(c["cod_muni"], {})
        v, t = s.get(ultimo, (None, None))
        if v is None:
            c["compra"] = None
            continue
        a = int(ultimo[:4])
        m_anio = media_anio(s, ANIO)   # mismo año que el alquiler y la renta
        c["compra"] = {
            "periodo": ultimo, "periodo_texto": periodo_texto(ultimo), "valor_m2": v, "tasaciones": t,
            "anterior": s.get(f"{a - 1}T{q}", (None, None))[0],
            "v2019": s.get(f"2019T{q}", (None, None))[0],
            "serie": [{"anio": int(p[:4]), "valor_m2": s[p][0]} for p in sorted(s) if p.endswith("T" + q)],
            # Indicadores propios con datos del mismo año (ANIO), para no mezclar años:
            "valor_m2_anio": round(m_anio, 1) if m_anio else None,
            "rentabilidad": round(c["eur_m2"] * 12 / m_anio * 100, 2) if (m_anio and c.get("eur_m2")) else None,
            "anios_renta": round(m_anio * c["superficie_m2"] / c["renta_hogar"], 1)
            if (m_anio and c.get("superficie_m2") and c.get("renta_hogar")) else None,
        }
    return ciudades


# ------------------------------------------------------------------ cálculos para la web
def _con(todas, k):
    return [c for c in todas if c.get("compra") and c["compra"].get(k) is not None]


def mediana(todas, k):
    xs = [c["compra"][k] for c in _con(todas, k)]
    return median(xs) if xs else None


def puesto(c, todas, k):
    xs = sorted(_con(todas, k), key=lambda x: (-x["compra"][k], x["nombre"]))
    for i, x in enumerate(xs, 1):
        if x["cod_muni"] == c["cod_muni"]:
            return i, len(xs)
    return None, len(xs)


def grafico(pts, etiqueta, gw):
    """Reutiliza el estilo del gráfico del alquiler; las etiquetas van en €/m²."""
    pts = [(a, v) for a, v in pts if v is not None]
    return gw.chart_svg(pts, etiqueta) if len(pts) >= 3 else ""


def frases(c, todas):
    x = c["compra"]
    nombre, per = c["nombre"], x["periodo_texto"]
    a = int(x["periodo"][:4])
    trim = per.rsplit(" de ", 1)[0]
    t = [f"En el {per}, las tasaciones de vivienda libre en {esc(nombre)} dieron un valor medio de {n(x['valor_m2'])} € por m²"
         + (f", según {n(x['tasaciones'])} tasaciones." if x["tasaciones"] else ".")]
    if c.get("superficie_m2"):
        t.append(f"A ese precio, un piso de {n(c['superficie_m2'])} m² (la superficie mediana de los pisos alquilados en la ciudad) "
                 f"se tasaría en unos {n(round(x['valor_m2'] * c['superficie_m2'], -3))} €.")
    ch = cambio(x["anterior"], x["valor_m2"])
    if ch is not None:
        t.append(f"Es un {d(abs(ch), 1)} % {'más' if ch >= 0 else 'menos'} que en el {trim} de {a - 1}.")
    ch19 = cambio(x["v2019"], x["valor_m2"])
    if ch19 is not None:
        t.append(f"Desde el {trim} de 2019 ha {'subido' if ch19 >= 0 else 'bajado'} un {d(abs(ch19), 0)} %.")
    med = mediana(todas, "valor_m2")
    pu, tot = puesto(c, todas, "valor_m2")
    t.append(f"La mediana de las {tot} ciudades con dato es de {n(med)} €/m²; {esc(nombre)} ocupa el puesto {pu} (en el 1, la vivienda más cara).")
    if x["rentabilidad"] is not None:
        mr = mediana(todas, "rentabilidad")
        pr, tr = puesto(c, todas, "rentabilidad")
        t.append(f"Con los datos de {ANIO}, alquilar un piso aquí rinde al año un {d(x['rentabilidad'])} % bruto de lo que vale "
                 f"(mediana de las ciudades: {d(mr)} %; puesto {pr} de {tr}, en el 1 la más alta).")
    if x["anios_renta"] is not None:
        t.append(f"Comprar un piso de {n(c['superficie_m2'])} m² costaba en {ANIO} unas {d(x['anios_renta'])} veces la renta neta media "
                 f"de un hogar de {esc(nombre)} en un año.")
    return t


def seccion(c, todas, gw):
    """HTML de la sección #compra. Sin dato representativo en el último trimestre: una línea que lo dice."""
    nombre = c["nombre"]
    x = c.get("compra")
    if not x:
        return (f'<section id="compra"><h2>Precio de la vivienda en venta en {esc(nombre)}</h2>'
                f'<p class="sub">No disponible: el Ministerio no publica un valor tasado representativo de {esc(nombre)} en su último trimestre.</p></section>')
    a = int(x["periodo"][:4])
    trim = x["periodo_texto"].rsplit(" de ", 1)[0]
    ch = cambio(x["anterior"], x["valor_m2"])
    pu, tot = puesto(c, todas, "valor_m2")
    facts = ('<dl class="facts">'
             f'<div><dt>Valor tasado de la vivienda</dt><dd>{n(x["valor_m2"])} €/m²<small>{esc(x["periodo_texto"])}; puesto {pu} de {tot}</small></dd></div>'
             + (f'<div><dt>Cambio en un año</dt><dd>{signo(ch)}<small>{n(x["anterior"])} €/m² en el {esc(trim)} de {a - 1}</small></dd></div>'
                if ch is not None else "")
             + (f'<div><dt>Rentabilidad bruta del alquiler ({ANIO})</dt><dd class="big">{d(x["rentabilidad"])} %<small>alquiler anual ÷ valor de la vivienda</small></dd></div>'
                if x["rentabilidad"] is not None else "")
             + '</dl>')
    svg = grafico([(s["anio"], s["valor_m2"]) for s in x["serie"]], f"Valor tasado de la vivienda en {nombre}, {trim} de cada año", gw)
    filas, prev = [], None
    for s in x["serie"]:
        cb = cambio(prev, s["valor_m2"]) if prev is not None else None
        filas.append(f'<tr><th scope="row">{s["anio"]}</th>'
                     f'<td>{n(s["valor_m2"]) + " €/m²" if s["valor_m2"] is not None else "No disponible"}</td>'
                     f'<td>{signo(cb) if cb is not None else "—"}</td></tr>')
        prev = s["valor_m2"]
    notas = ("Valor tasado: media del valor por m² de las tasaciones de vivienda libre hechas por las sociedades de tasación en el trimestre, "
             "sobre todo para conceder hipotecas. No es el precio final de venta ni el de los anuncios. "
             "Origen de los datos: Ministerio de Transportes y Movilidad Sostenible, Boletín Estadístico, «Valor tasado medio de vivienda libre "
             f"de los municipios mayores de 25.000 habitantes» (actualizado el {PUBLICADO}; descargado el {DESCARGA}). "
             f"Rentabilidad bruta: alquiler mediano por m² de {ANIO} (SERPAVI) × 12 ÷ media del valor tasado por m² de los cuatro trimestres de {ANIO}. "
             f"Veces la renta: valor tasado medio de {ANIO} × superficie mediana alquilada ÷ renta neta media del hogar de {ANIO} (INE). "
             "Son estimaciones propias y orientativas: no incluyen gastos, impuestos ni vacíos, y comparan medianas de alquiler con medias de tasación.")
    return (f'<section id="compra"><h2>Precio de la vivienda en venta en {esc(nombre)}</h2>{facts}'
            f'<p class="sub" style="margin-top:12px">{" ".join(frases(c, todas))}</p>'
            + (f'<h3 style="margin-top:24px">Evolución del valor tasado en {esc(nombre)} ({esc(trim)} de cada año)</h3>{svg}' if svg else "")
            + f'<div class="wrap"><table class="evol" style="white-space:nowrap"><thead><tr><th scope="col">Año ({esc(trim)})</th>'
            '<th scope="col">Valor tasado</th><th scope="col">Cambio en un año</th></tr></thead>'
            f'<tbody>{"".join(reversed(filas))}</tbody></table></div>'
            f'<p class="sub" style="margin-top:12px;font-size:14px">{esc(notas)}</p></section>')


if __name__ == "__main__":
    import json
    from config import JSON_NIVEL1
    ciudades = json.loads(JSON_NIVEL1.read_text(encoding="utf-8"))["ciudades"]
    if "--extraer" in sys.argv:
        extraer(ciudades)
    else:
        aportar(ciudades)
        print("Ciudades con valor tasado:", sum(1 for c in ciudades if c["compra"]))
