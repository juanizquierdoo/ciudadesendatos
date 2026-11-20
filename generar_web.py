"""Genera la web estática de ciudadesendatos a partir de datos_limpios/ciudades_nivel1.json.

Uso:  python generar_web.py
Resultado: carpeta web/ con la portada, una página por ciudad, rankings, sitemap y robots.
"""
from pathlib import Path
import html
import json
import math
import re
import shutil
import unicodedata

from config import ANIO, ANIO_INICIO_ALQUILER
from textos_ciudad import seccion_claves

base = Path(__file__).parent
DATOS = base / "datos_limpios" / "ciudades_nivel1.json"
WEB = base / "web"

BASE_URL = "https://ciudadesendatos.es"   # sin barra final. Vacío = sin sitemap ni canonical.
SITIO = "ciudadesendatos"
MIN_POB = "50.000"
# Fecha de actualización de cada fuente (la piden sus licencias). Cambiarla al cargar datos nuevos.
FECHA_SERPAVI = "08/07/2026"   # metadatos corregidos de la BD SERPAVI 2011-2024
FECHA_ADRH = "19/10/2026"      # nota de prensa del ADRH 2024 (INE)
RECURSOS = base / "recursos"   # og.png, favicon.png, favicon.ico (se crean con crear_imagenes.py)
FECHA_GEN = ""                 # se rellena en main() con el campo "generado" del JSON

# Nombre que más se usa al buscar, para el título de la página. El H1 mantiene el nombre oficial del INE.
# Por defecto, en los nombres oficiales con barra se usa la forma en castellano (la segunda).
NOMBRE_COMUN = {"Pamplona/Iruña": "Pamplona", "Eivissa": "Ibiza"}

# ---- Comunidades autónomas (B-18). Datos: datos_limpios/comunidades.json (preparar_comunidades.py, SERPAVI)
DATOS_CCAA = base / "datos_limpios" / "comunidades.json"
MIN_CIUDADES_CCAA = 3   # solo hay página de comunidad si tiene al menos 3 ciudades (regla 8: nada de páginas flojas)
# código INE -> (slug de la URL, nombre que más se usa al buscar, forma con "en")
CCAA_INFO = {
    "01": ("andalucia", "Andalucía", "en Andalucía"),
    "02": ("aragon", "Aragón", "en Aragón"),
    "03": ("asturias", "Asturias", "en Asturias"),
    "04": ("islas-baleares", "Baleares", "en Baleares"),
    "05": ("canarias", "Canarias", "en Canarias"),
    "06": ("cantabria", "Cantabria", "en Cantabria"),
    "07": ("castilla-y-leon", "Castilla y León", "en Castilla y León"),
    "08": ("castilla-la-mancha", "Castilla-La Mancha", "en Castilla-La Mancha"),
    "09": ("cataluna", "Cataluña", "en Cataluña"),
    "10": ("comunidad-valenciana", "Comunidad Valenciana", "en la Comunidad Valenciana"),
    "11": ("extremadura", "Extremadura", "en Extremadura"),
    "12": ("galicia", "Galicia", "en Galicia"),
    "13": ("comunidad-de-madrid", "Comunidad de Madrid", "en la Comunidad de Madrid"),
    "14": ("region-de-murcia", "Región de Murcia", "en la Región de Murcia"),
    "15": ("navarra", "Navarra", "en Navarra"),
    "16": ("pais-vasco", "País Vasco", "en el País Vasco"),
    "17": ("la-rioja", "La Rioja", "en La Rioja"),
    "18": ("ceuta", "Ceuta", "en Ceuta"),
    "19": ("melilla", "Melilla", "en Melilla"),
}
CCAA_COSTA = {"01", "03", "04", "05", "06", "09", "10", "12", "14", "16", "18", "19"}   # llevan el aviso turístico
COMUNIDADES = {}     # se rellena en main(): código -> datos del JSON + ciudades + si tiene página
PROV_CCAA = {}       # código de provincia -> código de comunidad

# Fuentes de los datos (para los datos estructurados)
FUENTES_LD = [
    {"@type": "Dataset", "name": "Sistema Estatal de Referencia del Precio del Alquiler de Vivienda (SERPAVI)",
     "creator": {"@type": "GovernmentOrganization", "name": "Ministerio de Vivienda y Agenda Urbana"}},
    {"@type": "Dataset", "name": "Atlas de Distribución de Renta de los Hogares (ADRH)",
     "creator": {"@type": "GovernmentOrganization", "name": "Instituto Nacional de Estadística (INE)"}, "url": "https://www.ine.es"},
]

# Posición aproximada de cada distrito en el mapa esquemático (columna, fila). Solo Madrid por ahora.
TILE = {"28079": {1: (2, 3), 2: (2, 4), 3: (3, 3), 4: (3, 2), 5: (3, 1), 6: (2, 1), 7: (2, 2), 8: (2, 0),
                  9: (1, 1), 10: (0, 2), 11: (1, 3), 12: (1, 4), 13: (4, 3), 14: (4, 2), 15: (4, 1),
                  16: (4, 0), 17: (2, 5), 18: (5, 3), 19: (5, 2), 20: (5, 1), 21: (6, 0)}}

# ------------------------------------------------------------------ utilidades
def esc(s):
    return html.escape(str(s).replace("'", "’"), quote=True)


def n(x):
    return "—" if x is None else f"{round(x):,}".replace(",", ".")


def d(x, k=1):
    return "—" if x is None else f"{x:.{k}f}".replace(".", ",")


def pc(x):
    return "—" if x is None else d(x, 1) + " %"


def norm(s):
    t = unicodedata.normalize("NFKD", s)
    return "".join(c for c in t if not unicodedata.combining(c)).lower().replace("'", "")


def cambio(a, b):
    return None if (a is None or b is None or a == 0) else (b / a - 1) * 100


def artículo(c):
    return c["nombre"]


def nombre_comun(c):
    nom = c["nombre"]
    if nom in NOMBRE_COMUN:
        return NOMBRE_COMUN[nom]
    return nom.split("/")[-1] if "/" in nom else nom


def url_abs(ruta):
    return f"{BASE_URL}/{ruta}" if BASE_URL else None


def de_(en):
    """'en la Comunidad de Madrid' -> 'de la Comunidad de Madrid'; 'en el País Vasco' -> 'del País Vasco'."""
    return "del " + en[6:] if en.startswith("en el ") else "de " + en[3:]


def ccaa_de(c):
    """Comunidad de una ciudad (o None si no hay datos de comunidades)."""
    return COMUNIDADES.get(PROV_CCAA.get(c["cod_muni"][:2]))


def migas_html(root, pasos, actual):
    """Miga de pan visible: pasos = [(texto, ruta relativa a la raíz)]."""
    enl = "".join(f'<a href="{root}{r}">{esc(t)}</a> › ' for t, r in pasos)
    return f'<nav class="migas" aria-label="Miga de pan">{enl}<span aria-current="page">{esc(actual)}</span></nav>'


def cambio_19(serie):
    """Cambio del €/m² entre 2019 y ANIO, en %, o None si falta alguno de los dos años."""
    m2 = {s["anio"]: s["eur_m2"] for s in serie if s.get("eur_m2") is not None}
    return cambio(m2.get(2019), m2.get(ANIO))


def pc_signo(x):
    return "—" if x is None else ("+" if x > 0 else "") + d(x, 1) + " %"


def jsonld(obj):
    """Bloque JSON-LD. Quita las claves vacías (p. ej. url cuando todavía no hay dominio)."""
    def limpia(x):
        if isinstance(x, dict):
            return {k: limpia(v) for k, v in x.items() if v not in (None, "", [], {})}
        if isinstance(x, list):
            return [limpia(v) for v in x]
        return x
    texto = json.dumps(limpia(obj), ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/ld+json">{texto}</script>'


def migas(items):
    """BreadcrumbList. Google exige URL absoluta en cada paso, así que solo se crea con BASE_URL."""
    if not BASE_URL:
        return None
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i, "name": nom, "item": url_abs(ruta)}
                                for i, (nom, ruta) in enumerate(items, 1)]}


def dataset(nombre, desc, ruta, lugar, variables, periodo=f"{ANIO_INICIO_ALQUILER}/{ANIO}"):
    return {"@context": "https://schema.org", "@type": "Dataset", "name": nombre.replace("'", "’"), "description": desc.replace("'", "’"),
            "url": url_abs(ruta), "inLanguage": "es", "temporalCoverage": periodo,
            "spatialCoverage": {"@type": "Place", "name": lugar},
            "variableMeasured": variables, "dateModified": FECHA_GEN, "isBasedOn": FUENTES_LD,
            "creator": {"@type": "Organization", "name": SITIO, "url": url_abs("")}, "license": LICENCIA_URL}


# ------------------------------------------------------------------ gráfico SVG
def ticks(mn, mx, k=4):
    raw = (mx - mn) / k or 1
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if raw <= m * mag)
    t = math.floor(mn / step) * step
    out = []
    while t <= mx + step * 0.999:
        out.append(round(t, 6))
        t += step
        if len(out) > 8:
            break
    return out, step


def chart_svg(pts, etiqueta):
    if len(pts) < 3:
        return ""
    W, H, L, R, T, B = 720, 300, 52, 22, 28, 38
    ys = [v for _, v in pts]
    tk, paso = ticks(min(ys) - (max(ys) - min(ys)) * .1, max(ys) + (max(ys) - min(ys)) * .1)
    mn, mx = tk[0], tk[-1]
    dec_t = 0 if paso >= 1 else 1 if paso >= 0.1 else 2
    y0, y1 = pts[0][0], pts[-1][0]

    def X(a):
        return L + (a - y0) / ((y1 - y0) or 1) * (W - L - R)

    def Y(v):
        return H - B - (v - mn) / ((mx - mn) or 1) * (H - B - T)

    s = []
    for t in tk:
        s.append(f'<line class="gl" x1="{L}" x2="{W - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}"/>'
                 f'<text x="{L - 8}" y="{Y(t) + 4:.1f}" text-anchor="end">{d(t, dec_t)}</text>')
    p = " ".join(f"{X(a):.1f},{Y(v):.1f}" for a, v in pts)
    s.append(f'<polygon class="ar" points="{X(y0):.1f},{H - B} {p} {X(y1):.1f},{H - B}"/><polyline class="ln" points="{p}"/>')
    for i, (a, v) in enumerate(pts):
        s.append(f'<circle cx="{X(a):.1f}" cy="{Y(v):.1f}" r="5"><title>{a}: {d(v, 2)} €/m²</title></circle>')
        if i % 3 == 0 or i == len(pts) - 1:
            s.append(f'<text x="{X(a):.1f}" y="{H - 14}" text-anchor="middle">{a}</text>')
    s.append(f'<text x="{X(y0):.1f}" y="{Y(pts[0][1]) - 12:.1f}" text-anchor="start">{d(pts[0][1], 2)}</text>'
             f'<text x="{X(y1):.1f}" y="{Y(pts[-1][1]) - 12:.1f}" text-anchor="end">{d(pts[-1][1], 2)} €/m²</text>')
    return (f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(etiqueta)}">'
            + "".join(s) + "</svg>")


# ------------------------------------------------------------------ piezas HTML comunes
def cabecera(root, extra):
    enl = "".join(f'<a href="{h}">{esc(t)}</a>' for h, t in extra)
    return (f'<header class="top"><nav aria-label="Principal"><a class="brand" href="{root}">ciudades<b>en</b>datos</a>'
            f'{enl}<a href="{root}rankings/peso-del-alquiler/">Rankings</a><a href="{root}comunidades/">Comunidades</a>'
            f'<a href="{root}#ciudades">Ciudades</a></nav></header>')


LICENCIA = "CC BY 4.0"
LICENCIA_URL = "https://creativecommons.org/licenses/by/4.0/deed.es"


def pie(root):
    return (f"<footer>Alquiler: Origen de los datos: Ministerio de Vivienda y Agenda Urbana (SERPAVI, datos de {ANIO}; actualizado el {FECHA_SERPAVI}). "
            "Renta y población: Elaboración propia con datos extraídos del sitio web del INE: www.ine.es "
            f"(Atlas de Distribución de Renta de los Hogares, {ANIO}; actualizado el {FECHA_ADRH}). "
            "Los indicadores combinados, como el alquiler sobre la renta, son estimaciones propias de "
            f"{SITIO}. Esta web no está vinculada al INE ni al Ministerio de Vivienda. "
            f'Los datos elaborados y los textos de {SITIO} se publican con licencia '
            f'<a href="{LICENCIA_URL}" rel="license">{LICENCIA}</a>: puedes reutilizarlos citando {SITIO} con un enlace a esta web.'
            " Los datos de origen mantienen la licencia de sus fuentes."
            + (f" Página generada el {fecha_es(FECHA_GEN)}." if FECHA_GEN else "") + "</footer>")


def fecha_es(iso):
    a, m, d_ = iso.split("-")
    return f"{d_}/{m}/{a}"


def head(titulo, desc, root, ruta, ld=()):
    # canonical, og:url y og:image necesitan la dirección completa: solo se escriben cuando BASE_URL tiene valor
    extra = ""
    if BASE_URL:
        extra += f'<link rel="canonical" href="{BASE_URL}/{ruta}"><meta property="og:url" content="{BASE_URL}/{ruta}">'
        if (RECURSOS / "og.png").exists():
            extra += (f'<meta property="og:image" content="{BASE_URL}/og.png"><meta property="og:image:width" content="1200">'
                      f'<meta property="og:image:height" content="630"><meta property="og:image:alt" content="{esc(SITIO)}: alquiler y renta en las ciudades de España">'
                      f'<meta name="twitter:card" content="summary_large_image">')
    icono = (f'<link rel="icon" type="image/png" sizes="48x48" href="{root}favicon.png">'
             if (RECURSOS / "favicon.png").exists() else "")
    bloques = "".join(jsonld(x) for x in ld if x)
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            f'<title>{esc(titulo)}</title><meta name="description" content="{esc(desc)}">'
            f'<meta property="og:title" content="{esc(titulo)}"><meta property="og:description" content="{esc(desc)}">'
            f'<meta property="og:type" content="website"><meta property="og:locale" content="es_ES">'
            f'<meta property="og:site_name" content="{esc(SITIO)}">{extra}{icono}'
            f'<link rel="stylesheet" href="{root}assets/estilo.css">{bloques}</head><body>')


def fin(root, extra_js=""):
    return f'{extra_js}<script src="{root}assets/app.js"></script></body></html>'


FECHA_CALLEJERO = ""  # se rellena en main() con la fecha del callejero del INE (ciudades_nivel1.json)


def zona_html(x):
    """Segunda línea bajo 'Distrito N (CP ...)': núcleos de población o calles principales del distrito."""
    z = x.get("zona") or {}
    partes = []
    if x.get("barrios"):
        if len(x["barrios"]) > 3:          # con 3 o menos ya están todos en el nombre
            partes.append("Barrios: " + y_lista(x["barrios"]))
        if z.get("cps"):
            partes.append("CP " + ", ".join(z["cps"]))
        return f'<span class="zona">{esc(". ".join(partes))}</span>'
    if not z:
        return ""
    if z.get("nucleos"):
        partes.append("Incluye " + y_lista(z["nucleos"]))
    if z.get("calles"):
        partes.append("Calles principales: " + ", ".join(z["calles"]))
    if not partes:
        return ""
    return f'<span class="zona">{esc(". ".join(partes))}</span>'


def y_lista(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


def th_orden(i, texto, tipo="num"):
    return f'<th><button type="button" data-col="{i}" data-type="{tipo}">{esc(texto)}</button></th>'


# ------------------------------------------------------------------ página de ciudad
def pagina_ciudad(c, todas, rank_n):
    root = "../"
    nombre = c["nombre"]
    r = c["rank"]
    dist = c["distritos"]
    dist_ok = [x for x in dist if x["fiabilidad"] in ("ok", "pocos_datos") and x["alquiler_pct_renta"] is not None]
    ser = [(s["anio"], s["eur_m2"]) for s in c["serie_alquiler"] if s["eur_m2"] is not None]
    rent = {s["anio"]: s["renta_hogar"] for s in c["serie_renta"] if s["renta_hogar"] is not None}
    m2 = dict(ser)

    corto = nombre_comun(c)
    titulo = (f"Precio del alquiler en {corto} por distrito ({ANIO})" if dist
              else f"Precio del alquiler y renta en {corto} ({ANIO})")
    if len(titulo) > 60:   # nombres largos: versión corta para que Google no corte el título
        titulo = f"Alquiler en {corto} por distrito ({ANIO})" if dist else f"Alquiler y renta en {corto} ({ANIO})"
    desc = (f"El alquiler mediano en {corto} es de {n(c['alquiler_mes'])} € al mes y equivale al "
            f"{d(c['alquiler_pct_renta'])} % de la renta del hogar. "
            + ("Datos oficiales por distrito." if dist else "Elaboración propia con datos oficiales."))

    lead = (f"La mitad de los pisos alquilados en {esc(nombre)} cuesta menos de {n(c['alquiler_mes'])} € al mes. "
            f"Al año, ese alquiler equivale al {d(c['alquiler_pct_renta'])} % de la renta media de un hogar "
            f"({n(c['renta_hogar'])} €), lo que coloca a {esc(nombre)} en el puesto {r['alquiler_pct_renta']} de {rank_n['alquiler_pct_renta']} "
            f"ciudades de más de {MIN_POB} habitantes por peso del alquiler (en el puesto 1 es donde más pesa).")
    if len(dist_ok) >= 2:
        lo = min(x["alquiler_pct_renta"] for x in dist_ok)
        hi = max(x["alquiler_pct_renta"] for x in dist_ok)
        lead += f" Entre sus distritos, el peso va del {d(lo)} % al {d(hi)} %."

    sup = f", superficie mediana {n(c['superficie_m2'])} m²" if c.get("superficie_m2") else ""
    facts = (f'<dl class="facts">'
             f'<div><dt>Alquiler mediano de un piso</dt><dd>{n(c["alquiler_mes"])} €/mes<small>{d(c["eur_m2"], 2)} €/m²{sup}</small></dd></div>'
             f'<div><dt>Renta neta media del hogar</dt><dd>{n(c["renta_hogar"])} €/año<small>{n(c["renta_persona"])} € por persona</small></dd></div>'
             f'<div><dt>Alquiler sobre la renta</dt><dd class="big">{pc(c["alquiler_pct_renta"])}<small>puesto {r["alquiler_pct_renta"]} de {rank_n["alquiler_pct_renta"]} ciudades</small></dd></div></dl>')

    sec = []
    nav = [("#resumen", "Resumen"), ("#claves", "Claves"), ("#evolucion", "Evolución")]

    # texto explicativo generado desde los datos (textos_ciudad.py, B-17)
    sec.append(seccion_claves(c, todas, ANIO, f"ciudades de más de {MIN_POB} habitantes"))

    # evolución
    svg = chart_svg(ser, f"Evolución del alquiler mediano por m² en {nombre}")
    if svg:
        txt = []
        a0, v0 = ser[0]
        ch = cambio(v0, ser[-1][1])
        if ch is not None and a0 < ser[-1][0]:
            txt.append(f"En {ser[-1][0]} el alquiler por m² es un {d(abs(ch), 0)} % {'mayor' if ch >= 0 else 'menor'} que en {a0}.")
        if 2019 in m2 and ANIO in m2 and a0 < 2019:
            ch19 = cambio(m2[2019], m2[ANIO])
            txt.append(f"Desde 2019 ha {'subido' if ch19 >= 0 else 'bajado'} un {d(abs(ch19), 0)} %.")
        if 2015 in m2 and ANIO in m2 and 2015 in rent and ANIO in rent:
            ca, cr = cambio(m2[2015], m2[ANIO]), cambio(rent[2015], rent[ANIO])
            if ca is not None and cr is not None:
                rel = ("más rápido" if ca > cr else "más despacio")
                txt.append(f"Entre 2015 y {ANIO} el alquiler por m² ha cambiado un {d(ca, 0)} % y la renta del hogar un {d(cr, 0)} %: "
                           f"el alquiler ha crecido {rel} que los ingresos.")
        sec.append(f'<section id="evolucion"><h2>Cómo ha cambiado el alquiler en {esc(nombre)}</h2>'
                   f'<p class="sub">Alquiler mediano de un piso, en euros por m² al mes.</p>{svg}'
                   f'<p class="sub" style="margin-top:12px">{" ".join(txt)}</p></section>')
    else:
        sec.append(f'<section id="evolucion"><h2>Evolución</h2><p class="sub">No hay serie histórica suficiente para {esc(nombre)}.</p></section>')

    # distritos
    mapa_js = ""
    if dist:
        nav.append(("#distritos", "Distritos"))
        filas = []
        hay_pocos = hay_ocultos = False
        for x in dist:
            ver = x["fiabilidad"] in ("ok", "pocos_datos") and x["alquiler_mes"] is not None
            ast = ""
            if x["fiabilidad"] == "pocos_datos":
                ast = "*"
                hay_pocos = True
            if not ver:
                hay_ocultos = True
            a_mes = x["alquiler_mes"] if ver else None
            a_m2 = x["eur_m2"] if ver else None
            a_pc = x["alquiler_pct_renta"] if ver else None
            barra = (f'<div class="meter"><span class="track"><span class="fill" style="--w:{min(a_pc / 30 * 100, 100):.1f}%"></span></span>'
                     f'<span>{d(a_pc)} %{ast}</span></div>') if a_pc is not None else "—"
            fv = lambda v: "" if v is None else f"{v:.2f}"
            filas.append(f'<tr><th scope="row" data-v="{esc(x["nombre"])}">{esc(x["nombre"])}{zona_html(x)}</th>'
                         f'<td data-v="{fv(a_mes)}">{n(a_mes)}{" €" if a_mes else ""}{ast if a_mes else ""}</td>'
                         f'<td data-v="{fv(a_m2)}">{d(a_m2, 2) if a_m2 else "—"}</td>'
                         f'<td data-v="{fv(x["renta_hogar"])}">{n(x["renta_hogar"])}{" €" if x["renta_hogar"] else ""}</td>'
                         f'<td data-v="{fv(a_pc)}">{barra}</td></tr>')
        notas = []
        if hay_pocos:
            notas.append("* Pocos inmuebles en la muestra (entre 30 y 99): interpreta la cifra con cuidado.")
        if hay_ocultos:
            notas.append("— Distritos con menos de 30 inmuebles en alquiler: no se muestra el alquiler para no dar un dato poco fiable.")
        top = sorted(dist_ok, key=lambda x: -x["alquiler_pct_renta"])
        extremos = ""
        if len(top) >= 6:
            li = lambda arr: "".join(f'<li><span>{esc(x["nombre"])}</span><strong>{pc(x["alquiler_pct_renta"])}</strong></li>' for x in arr)
            extremos = (f'<div class="two"><div><h3>Más peso sobre la renta</h3><ol>{li(top[:3])}</ol></div>'
                        f'<div><h3>Menos peso sobre la renta</h3><ol>{li(top[-3:][::-1])}</ol></div></div>')
        mapa = ""
        pos = TILE.get(c["cod_muni"])
        if pos:
            md = []
            for x in dist_ok:
                if x["numero"] in pos and x["fiabilidad"] == "ok":
                    cx, cy = pos[x["numero"]]
                    md.append({"n": x["numero"], "nombre": x["nombre"], "col": cx, "fila": cy,
                               "pct": x["alquiler_pct_renta"], "alq": x["alquiler_mes"], "renta": x["renta_hogar"],
                               "m2": x["eur_m2"], "sup": x["superficie_m2"], "inm": x["inmuebles"]})
            avg = {"nombre": f"{nombre} (media de la ciudad)", "pct": c["alquiler_pct_renta"], "alq": c["alquiler_mes"],
                   "renta": c["renta_hogar"], "m2": c["eur_m2"], "sup": c["superficie_m2"], "inm": c["inmuebles"]}
            nav.insert(1, ("#mapa", "Mapa"))
            mapa = ('<section id="mapa"><h2>Mapa de distritos</h2><p class="sub">Elige qué comparar y pasa el cursor (o toca) un distrito.</p>'
                    '<div class="ctl" id="mctl" role="group" aria-label="Dato del mapa"><span>Colorear por</span></div>'
                    '<div class="mapbox"><div><div class="grid" id="grid"></div>'
                    '<div class="legend"><span id="lmin"></span><i></i><span id="lmax"></span></div>'
                    '<p class="sub" style="margin-top:12px;font-size:14px">Mapa esquemático: cada casilla es un distrito en su posición aproximada, no sus límites reales.</p></div>'
                    '<aside class="panel" aria-live="polite" id="panel"></aside></div></section>')
            mapa_js = ('<script type="application/json" id="mapa-datos">'
                       + json.dumps({"distritos": md, "media": avg}, ensure_ascii=False).replace("</", "<\\/") + "</script>")
        sec.append(mapa + f'<section id="distritos"><h2>Los {len(dist)} distritos de {esc(nombre)}</h2>{extremos}'
                   f'<div class="wrap"><table class="sortable" data-sort="4"><thead><tr>{th_orden(0, "Distrito", "text")}{th_orden(1, "Alquiler al mes")}'
                   f'{th_orden(2, "€/m²")}{th_orden(3, "Renta del hogar")}{th_orden(4, "Alquiler sobre renta")}</tr></thead>'
                   f'<tbody>{"".join(filas)}</tbody></table></div>'
                   + "".join(f'<p class="proto">{esc(t)}</p>' for t in notas)
                   + (f'<p class="proto">Distritos sin nombre oficial: se identifican por sus códigos postales y por las calles que pasan '
                      f'por más secciones censales del distrito, según el Callejero del Censo Electoral del INE (situación a {esc(FECHA_CALLEJERO)}). '
                      f'Los nombres de las calles se escriben como los da el INE, sin tildes.</p>'
                      if any(x.get("zona") and not x.get("barrios") for x in dist) else '')
                   + (f'<p class="proto">Barrios de los distritos: {esc(c["cita_barrios"])}. Solo se indican cuando las zonas del Ayuntamiento '
                      f'forman el distrito completo (la suma de su población coincide exactamente con la del distrito).</p>'
                      if c.get("cita_barrios") else '')
                   + (f'<p class="proto">Nombres de los distritos: {esc(c["cita_nombres_distritos"])}.</p>'
                      if c.get("cita_nombres_distritos") else '')
                   + ('' if any(x["con_nombre_oficial"] or x.get("zona") for x in dist) else
                      '<p class="proto">Los distritos se identifican con el número del INE. Los nombres de barrio todavía no están incorporados.</p>')
                   + '</section>')
    else:
        sec.append(f'<section id="distritos"><h2>Distritos</h2><p class="sub">{esc(nombre)} tiene un único distrito censal en los datos del INE, '
                   f'así que no hay desglose interno.</p></section>')

    # perfil
    perfil = [("Población", n(c["poblacion"])), ("Edad media", d(c.get("edad_media")) + " años" if c.get("edad_media") else None),
              ("Hogares de una sola persona", pc(c.get("pct_unipersonales")) if c.get("pct_unipersonales") is not None else None),
              ("Mayores de 65 años", pc(c.get("pct_65_mas")) if c.get("pct_65_mas") is not None else None),
              ("Menores de 18 años", pc(c.get("pct_menor_18")) if c.get("pct_menor_18") is not None else None),
              ("Tamaño medio del hogar", d(c.get("tam_hogar"), 2) + " personas" if c.get("tam_hogar") else None)]
    items = "".join(f"<div><dt>{esc(a)}</dt><dd>{esc(b)}</dd></div>" for a, b in perfil if b)
    sec.append(f'<section id="perfil"><h2>Quién vive en {esc(nombre)}</h2><dl class="perfil">{items}</dl>'
               f'<p class="sub" style="margin-top:12px;font-size:14px">Datos de {ANIO} del INE.</p></section>')

    # enlaces internos
    prov = [x for x in todas if x["provincia"] == c["provincia"] and x["slug"] != c["slug"]][:8]
    ordenadas = sorted(todas, key=lambda x: x["rank"]["alquiler_pct_renta"])
    i = ordenadas.index(c)
    cerca = ordenadas[max(0, i - 3):i] + ordenadas[i + 1:i + 4]
    lnk = lambda arr: "".join(f'<li><a href="{root}{x["slug"]}/">{esc(x["nombre"])}</a><span>{pc(x["alquiler_pct_renta"])}</span></li>' for x in arr)
    rel = ""
    cc = ccaa_de(c)
    comp_ccaa = ""
    if cc and cc.get("alquiler_mes"):
        comp_ccaa = (f'<p class="sub">En el conjunto {de_(cc["en"])} (todos sus municipios, no solo las ciudades), el alquiler mediano de un piso '
                     f'es de {n(cc["alquiler_mes"])} € al mes ({d(cc["eur_m2"], 2)} €/m²). En {esc(nombre)} es de {n(c["alquiler_mes"])} € '
                     f'({d(c["eur_m2"], 2)} €/m²).'
                     + (f' <a href="{root}comunidades/{cc["slug"]}/">Compara las {len(cc["ciudades"])} ciudades {de_(cc["en"])}</a>.' if cc["pagina"] else "")
                     + '</p>')
    if prov:
        rel += f'<div><h3>Otras ciudades de {esc(c["provincia"])}</h3><ul class="lnk">{lnk(prov)}</ul></div>'
    rel += f'<div><h3>Ciudades con un peso del alquiler parecido</h3><ul class="lnk">{lnk(cerca)}</ul></div>'
    sec.append(f'<section id="comparar"><h2>Compara con otras ciudades</h2>{comp_ccaa}<div class="two">{rel}</div></section>')

    # puesto en cada ranking, con enlace a la fila de la ciudad
    lis = "".join(
        f'<li><a href="{root}rankings/{s}/#c-{c["slug"]}">{esc({"eur_m2": "Alquiler por m²"}.get(k, ETIQ[k]))}: {FMT[k](c[k])}</a>'
        f'<span>puesto {r[k]} de {rank_n[k]}</span></li>' for s, k, t, _ in RANKINGS)
    sec.append(f'<section id="rankings"><h2>{esc(nombre)} en los rankings</h2>'
               f'<p class="sub">El puesto 1 es la ciudad con el valor más alto.</p><ul class="lnk">{lis}</ul></section>')

    # metodología
    nav.append(("#metodologia", "Metodología"))
    sec.append('<section id="metodologia"><h2>Cómo leer estos datos</h2><ul class="notes">'
               f'<li><strong>Alquiler:</strong> mediana de los alquileres de vivienda habitual declarados en el IRPF de {ANIO}, solo pisos. '
               'Son contratos vigentes, no anuncios, así que suelen ser más bajos que los precios de los portales inmobiliarios.</li>'
               '<li><strong>Renta:</strong> renta neta media por hogar de todos los hogares, también los que no alquilan.</li>'
               '<li><strong>Alquiler sobre renta:</strong> alquiler mediano × 12 ÷ renta neta media del hogar. Sirve para comparar zonas entre sí; '
               'no es lo que gasta un inquilino típico.</li>'
               '<li><strong>Zonas turísticas:</strong> donde hay mucha segunda residencia o alquiler turístico, la renta de los residentes y el alquiler '
               'de vivienda habitual pueden no reflejar lo que paga quien llega de fuera.</li></ul></section>')

    pasos = [("Inicio", "")] + ([(cc["comun"], f'comunidades/{cc["slug"]}/')] if cc and cc["pagina"] else [])
    cuerpo = (cabecera(root, nav) +
              f'<div class="hero"><div id="resumen">{migas_html(root, pasos, nombre)}<h1>{"Alquiler y renta por distrito en " if dist else "Alquiler y renta en "}{esc(nombre)}</h1>'
              f'<p class="lead">{lead}</p>{facts}</div></div><main>{"".join(sec)}{pie(root)}</main>')
    ruta = f"{c['slug']}/"
    ld = [dataset(f"Alquiler y renta en {nombre}", desc, ruta, f"{nombre}, {c['provincia']}, España",
                  ["Alquiler mensual mediano", "Alquiler mediano por m²", "Renta neta media del hogar", "Alquiler sobre renta"]
                  + (["Desglose por distrito censal"] if dist else []),
                  f"{ser[0][0]}/{ser[-1][0]}" if ser else str(ANIO)),
          migas([(t, r) for t, r in pasos] + [(nombre, ruta)])]
    return head(titulo, desc, root, ruta, ld) + cuerpo + fin(root, mapa_js)


# ------------------------------------------------------------------ rankings
RANKINGS = [
    ("peso-del-alquiler", "alquiler_pct_renta", "Ciudades donde más pesa el alquiler sobre la renta",
     "Alquiler anual mediano dividido entre la renta neta media del hogar, en las ciudades de más de 50.000 habitantes."),
    ("alquiler-mediano", "alquiler_mes", "Ciudades con el alquiler más caro y más barato",
     "Alquiler mensual mediano de un piso, en euros, en las ciudades de más de 50.000 habitantes."),
    ("alquiler-por-m2", "eur_m2", "Alquiler por metro cuadrado por ciudad",
     "Alquiler mensual mediano por m² de un piso, en las ciudades de más de 50.000 habitantes."),
    ("renta-del-hogar", "renta_hogar", "Ciudades con mayor y menor renta por hogar",
     "Renta neta media anual por hogar, en las ciudades de más de 50.000 habitantes."),
]
ETIQ = {"alquiler_pct_renta": "Alquiler sobre renta", "alquiler_mes": "Alquiler al mes", "eur_m2": "€/m²", "renta_hogar": "Renta del hogar"}
FMT = {"alquiler_pct_renta": pc, "alquiler_mes": lambda v: n(v) + " €", "eur_m2": lambda v: d(v, 2) + " €", "renta_hogar": lambda v: n(v) + " €"}


def pagina_ranking(slug, clave, titulo, def_, todas, rank_n):
    root = "../../"
    orden = sorted(todas, key=lambda c: c["rank"][clave])
    f = FMT[clave]
    filas = "".join(
        f'<tr id="c-{c["slug"]}"><td data-v="{i}">{i}</td><th scope="row" data-v="{esc(c["nombre"])}"><a href="{root}{c["slug"]}/">{esc(c["nombre"])}</a></th>'
        f'<td data-v="{esc(c["provincia"])}">{esc(c["provincia"])}</td><td data-v="{c["poblacion"] or ""}">{n(c["poblacion"])}</td>'
        f'<td data-v="{c["alquiler_mes"] or ""}">{n(c["alquiler_mes"])} €</td><td data-v="{c["eur_m2"] or ""}">{d(c["eur_m2"], 2)}</td>'
        f'<td data-v="{c["renta_hogar"] or ""}">{n(c["renta_hogar"])} €</td>'
        f'<td data-v="{c["alquiler_pct_renta"] or ""}">{pc(c["alquiler_pct_renta"])}</td></tr>'
        for i, c in enumerate(orden, 1))
    top = ", ".join(f'{esc(c["nombre"])} ({f(c[clave])})' for c in orden[:5])
    bot = ", ".join(f'{esc(c["nombre"])} ({f(c[clave])})' for c in orden[:-6:-1])
    otros = "".join(f'<li><a href="{root}rankings/{s}/">{esc(t)}</a></li>' for s, k, t, _ in RANKINGS if s != slug)
    desc = f"{titulo} en {ANIO}, con datos oficiales de las {len(todas)} ciudades españolas de más de {MIN_POB} habitantes."
    cuerpo = (cabecera(root, [("#tabla", "Tabla")]) +
              f'<div class="hero"><div><h1>{esc(titulo)} ({ANIO})</h1><p class="lead">{esc(def_)}</p>'
              f'<p class="sub"><strong>Mayor:</strong> {top}.<br><strong>Menor:</strong> {bot}.</p>{aviso_turistico()}</div></div>'
              f'<main><section id="tabla"><div class="wrap"><table class="sortable numbered" data-sort="{ {"alquiler_pct_renta": 7, "alquiler_mes": 4, "eur_m2": 5, "renta_hogar": 6}[clave] }">'
              f'<thead><tr><th>#</th>{th_orden(1, "Ciudad", "text")}{th_orden(2, "Provincia", "text")}{th_orden(3, "Población")}'
              f'{th_orden(4, "Alquiler al mes")}{th_orden(5, "€/m²")}{th_orden(6, "Renta del hogar")}{th_orden(7, "Alquiler sobre renta")}</tr></thead>'
              f'<tbody>{filas}</tbody></table></div></section>'
              f'<section><h2>Otros rankings</h2><ul class="lnk">{otros}</ul></section>'
              f'{pie(root)}</main>')
    ruta = f"rankings/{slug}/"
    ld = [dataset(f"{titulo} ({ANIO})", desc, ruta, "España", [ETIQ[clave]]),
          migas([("Inicio", ""), (titulo, ruta)])]
    return head(f"{titulo} ({ANIO})", desc, root, ruta, ld) + cuerpo + fin(root)


# ------------------------------------------------------------------ aviso de zonas turísticas (B-13)
def aviso_turistico():
    return ('<p class="aviso" role="note"><strong>Ojo con las zonas turísticas.</strong> En la costa y las islas, '
            'muchos de los que alquilan o compran no viven allí todo el año. Estos datos miden el alquiler de vivienda habitual y la renta '
            'de los residentes, así que un peso del alquiler alto puede reflejar sobre todo una renta baja de los residentes, '
            'y el alquiler que paga quien llega de fuera puede ser bastante mayor.</p>')


# ------------------------------------------------------------------ portada
def comunidades_portada():
    cs = sorted([x for x in COMUNIDADES.values() if x["pagina"]], key=lambda x: norm(x["comun"]))
    if not cs:
        return ""
    lis = "".join(f'<li><a href="comunidades/{x["slug"]}/">{esc(x["comun"])}</a><span>{len(x["ciudades"])} ciudades · {n(x.get("alquiler_mes"))} €/mes</span></li>' for x in cs)
    return (f'<section id="comunidades"><h2>Por comunidad autónoma</h2><p class="sub">Alquiler mediano de toda la comunidad y número de ciudades. '
            f'<a href="comunidades/">Ver la tabla de todas las comunidades</a>.</p><ul class="lnk cols">{lis}</ul></section>')


def pagina_indice(todas, rank_n):
    root = ""
    N = len(todas)
    orden = sorted(todas, key=lambda c: c["rank"]["alquiler_pct_renta"])
    li = lambda arr: "".join(f'<li><a href="{c["slug"]}/">{esc(c["nombre"])}</a><strong>{pc(c["alquiler_pct_renta"])}</strong></li>' for c in arr)
    tarjetas = "".join(f'<a class="card" href="rankings/{s}/"><strong>{esc(t)}</strong><span>{esc(df)}</span></a>' for s, k, t, df in RANKINGS)
    lista = "".join(f'<li data-b="{esc(norm(c["nombre"] + " " + c["provincia"]))}"><a href="{c["slug"]}/">{esc(c["nombre"])}</a>'
                    f'<span>{esc(c["provincia"])}</span><strong>{pc(c["alquiler_pct_renta"])}</strong></li>'
                    for c in sorted(todas, key=lambda c: norm(c["nombre"])))
    desc = (f"Alquiler, renta de los hogares y peso del alquiler en {N} ciudades de España, con datos oficiales de {ANIO} "
            "y desglose por distrito.")
    cuerpo = (cabecera(root, [("#rankings", "Más datos")]) +
              f'<div class="hero"><div><h1>Alquiler, renta y coste de vida en las ciudades de España</h1>'
              f'<p class="lead">Datos oficiales de {ANIO} para {N} ciudades de más de {MIN_POB} habitantes: cuánto cuesta alquilar, '
              f'cuánto ingresan los hogares y qué parte de esos ingresos se lleva el alquiler, también por distrito.</p>'
              f'<label class="busca"><span>Busca tu ciudad</span><input id="buscador" type="search" placeholder="Madrid, Valladolid, Sevilla…" autocomplete="off"></label>'
              f'</div></div><main>'
              f'<section id="rankings"><h2>Rankings</h2><div class="cards">{tarjetas}</div></section>'
              f'<section><h2>Dónde pesa más y menos el alquiler</h2><div class="two">'
              f'<div><h3>Más peso sobre la renta</h3><ol class="lnk">{li(orden[:5])}</ol></div>'
              f'<div><h3>Menos peso sobre la renta</h3><ol class="lnk">{li(orden[:-6:-1])}</ol></div></div>{aviso_turistico()}</section>'
              + comunidades_portada() +
              f'<section id="ciudades"><h2>Todas las ciudades</h2><p class="sub" id="cuenta">{N} ciudades</p>'
              f'<ul class="todas" id="lista">{lista}</ul></section>{pie(root)}</main>')
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": SITIO, "url": url_abs(""), "inLanguage": "es"},
          dataset(f"Alquiler y renta en {N} ciudades de España", desc, "", "España",
                  ["Alquiler mensual mediano", "Alquiler mediano por m²", "Renta neta media del hogar", "Alquiler sobre renta"])]
    return head(f"Alquiler y renta por ciudad en España ({ANIO}) | {SITIO}", desc, root, "", ld) + cuerpo + fin(root)


# ------------------------------------------------------------------ comunidades autónomas (B-18)
def metodologia_ccaa():
    return ('<section id="metodologia"><h2>Cómo leer estos datos</h2><ul class="notes">'
            f'<li><strong>Alquiler de la comunidad:</strong> mediana de los alquileres de vivienda habitual declarados en el IRPF de {ANIO} '
            'en todos los municipios de la comunidad, solo pisos (SERPAVI). Incluye pueblos y ciudades pequeñas, así que suele ser más bajo '
            'que el de las ciudades grandes. Son contratos vigentes, no anuncios.</li>'
            f'<li><strong>Ciudades:</strong> solo las de más de {MIN_POB} habitantes con alquiler fiable (100 inmuebles o más).</li>'
            '<li><strong>Renta:</strong> renta neta media por hogar del INE, por ciudad. No damos una renta de toda la comunidad porque '
            'nuestro dato del INE es municipal.</li>'
            '<li><strong>Alquiler sobre renta:</strong> alquiler mediano × 12 ÷ renta neta media del hogar. Estimación propia y aproximada, '
            'útil para comparar ciudades entre sí.</li>'
            '<li><strong>Navarra y País Vasco</strong> tienen régimen fiscal propio y su serie del SERPAVI empieza más tarde que la del resto.</li>'
            '</ul></section>')


def pagina_comunidad(cc, todas, rank_n):
    root = "../../"
    ciu = sorted(cc["ciudades"], key=lambda c: -c["alquiler_pct_renta"])
    N = len(ciu)
    nom, en = cc["comun"], cc["en"]
    ruta = f'comunidades/{cc["slug"]}/'
    alq = cc.get("alquiler_mes")
    ch19 = cambio_19(cc["serie_alquiler"])

    titulo = f"Precio del alquiler {en} por ciudad ({ANIO})"
    if len(titulo) > 60:
        titulo = f"Alquiler {en} por ciudad ({ANIO})"
    desc = ((f"El alquiler mediano {en} es de {n(alq)} € al mes. " if alq else "")
            + f"Alquiler, renta y peso del alquiler en sus {N} ciudades de más de {MIN_POB} habitantes ({ANIO}).")

    por_alq = sorted(ciu, key=lambda c: -c["alquiler_mes"])
    lead = (f"La mitad de los pisos alquilados como vivienda habitual {en} cuesta menos de {n(alq)} € al mes "
            f"({d(cc['eur_m2'], 2)} €/m²), según los datos de toda la comunidad. " if alq else
            f"No hay dato oficial fiable del alquiler de toda la comunidad. ")
    lead += (f"Entre sus {N} ciudades de más de {MIN_POB} habitantes, el alquiler más alto está en {esc(por_alq[0]['nombre'])} "
             f"({n(por_alq[0]['alquiler_mes'])} €) y el más bajo en {esc(por_alq[-1]['nombre'])} ({n(por_alq[-1]['alquiler_mes'])} €). "
             f"El peso del alquiler sobre la renta va del {d(ciu[-1]['alquiler_pct_renta'])} % de {esc(ciu[-1]['nombre'])} "
             f"al {d(ciu[0]['alquiler_pct_renta'])} % de {esc(ciu[0]['nombre'])}.")

    rango = (f"de {d(cc['eur_m2_p25'], 2)} a {d(cc['eur_m2_p75'], 2)} €/m² la mitad central"
             if cc.get("eur_m2_p25") and cc.get("eur_m2_p75") else "")
    facts = (f'<dl class="facts">'
             f'<div><dt>Alquiler mediano en toda la comunidad</dt><dd>{n(alq)} €/mes<small>{d(cc.get("eur_m2"), 2)} €/m²'
             f'{", " + rango if rango else ""}</small></dd></div>'
             f'<div><dt>Cambio del €/m² desde 2019</dt><dd class="big">{pc_signo(ch19)}<small>'
             f'{"de " + d({s_["anio"]: s_["eur_m2"] for s_ in cc["serie_alquiler"]}[2019], 2) + " a " + d(cc["eur_m2"], 2) + " €/m²" if ch19 is not None else "no hay dato de 2019"}'
             f'</small></dd></div>'
             f'<div><dt>Ciudades de más de {MIN_POB} habitantes</dt><dd>{N}<small>{n(sum(c["poblacion"] for c in ciu))} habitantes en total</small></dd></div></dl>')

    sec = []
    nav = [("#ciudades", "Tabla"), ("#evolucion", "Evolución"), ("#metodologia", "Metodología")]

    fv = lambda v: "" if v is None else f"{v:.2f}"
    con_19 = any(cambio_19(c["serie_alquiler"]) is not None for c in ciu)
    filas = []
    for c in ciu:
        ch = cambio_19(c["serie_alquiler"])
        filas.append(f'<tr id="c-{c["slug"]}"><th scope="row" data-v="{esc(c["nombre"])}"><a href="{root}{c["slug"]}/">{esc(c["nombre"])}</a></th>'
                     f'<td data-v="{esc(c["provincia"])}">{esc(c["provincia"])}</td>'
                     f'<td data-v="{fv(c["alquiler_mes"])}">{n(c["alquiler_mes"])} €</td>'
                     f'<td data-v="{fv(c["eur_m2"])}">{d(c["eur_m2"], 2)}</td>'
                     + (f'<td data-v="{fv(ch)}">{pc_signo(ch)}</td>' if con_19 else "")
                     + f'<td data-v="{fv(c["renta_hogar"])}">{n(c["renta_hogar"])} €</td>'
                     f'<td data-v="{fv(c["alquiler_pct_renta"])}">{pc(c["alquiler_pct_renta"])}</td></tr>')
    sec.append(f'<section id="ciudades"><h2>Las {N} ciudades {de_(en)}</h2>'
               f'<p class="sub">Pulsa en una columna para ordenar.'
               + (f' El cambio es el del alquiler por m² entre 2019 y {ANIO}.' if con_19 else "") + '</p>'
               f'<div class="wrap"><table class="sortable ccaa" data-sort="{6 if con_19 else 5}"><thead><tr>{th_orden(0, "Ciudad", "text")}{th_orden(1, "Provincia", "text")}'
               f'{th_orden(2, "Alquiler al mes")}{th_orden(3, "€/m²")}'
               + (th_orden(4, "Cambio €/m² desde 2019") if con_19 else "")
               + f'{th_orden(4 + con_19, "Renta del hogar")}{th_orden(5 + con_19, "Alquiler sobre renta")}</tr></thead>'
               f'<tbody>{"".join(filas)}</tbody></table></div>'
               + (aviso_turistico() if cc["cod_ccaa"] in CCAA_COSTA else "") + '</section>')

    ser = [(s_["anio"], s_["eur_m2"]) for s_ in cc["serie_alquiler"]]
    svg = chart_svg(ser, f"Evolución del alquiler mediano por m² {en}")
    txt = []
    if ch19 is not None:
        txt.append(f"Desde 2019, el alquiler por m² {en} ha {'subido' if ch19 >= 0 else 'bajado'} un {d(abs(ch19), 0)} %.")
    con_ch = [(cambio_19(c["serie_alquiler"]), c) for c in ciu]
    con_ch = sorted([x for x in con_ch if x[0] is not None], key=lambda x: -x[0])
    if len(con_ch) >= 2:
        txt.append(f"Entre sus ciudades, donde más ha subido es {esc(con_ch[0][1]['nombre'])} ({pc_signo(con_ch[0][0])}) "
                   f"y donde menos, {esc(con_ch[-1][1]['nombre'])} ({pc_signo(con_ch[-1][0])}).")
    if svg:
        sec.append(f'<section id="evolucion"><h2>Cómo ha cambiado el alquiler {en}</h2>'
                   f'<p class="sub">Alquiler mediano de un piso en toda la comunidad, en euros por m² al mes.</p>{svg}'
                   f'<p class="sub" style="margin-top:12px">{" ".join(txt)}</p></section>')
    else:
        sec.append(f'<section id="evolucion"><h2>Evolución</h2><p class="sub">La serie del SERPAVI {en} es demasiado corta para un gráfico. '
                   f'{" ".join(txt)}</p></section>')

    otras = sorted([x for x in COMUNIDADES.values() if x["pagina"] and x["cod_ccaa"] != cc["cod_ccaa"]], key=lambda x: norm(x["comun"]))
    lis = "".join(f'<li><a href="{root}comunidades/{x["slug"]}/">{esc(x["comun"])}</a><span>{n(x.get("alquiler_mes"))} €/mes</span></li>' for x in otras)
    sec.append(f'<section id="otras"><h2>Otras comunidades</h2><p class="sub">Alquiler mediano de toda la comunidad. '
               f'<a href="{root}comunidades/">Ver la tabla de las 17 comunidades y 2 ciudades autónomas</a>.</p><ul class="lnk">{lis}</ul></section>')
    sec.append(metodologia_ccaa())

    pasos = [("Inicio", ""), ("Comunidades autónomas", "comunidades/")]
    cuerpo = (cabecera(root, nav) +
              f'<div class="hero"><div id="resumen">{migas_html(root, pasos, nom)}<h1>Alquiler y renta en las ciudades {de_(en)}</h1>'
              f'<p class="lead">{lead}</p>{facts}</div></div><main>{"".join(sec)}{pie(root)}</main>')
    ld = [dataset(f"Alquiler y renta {en} ({ANIO})", desc, ruta, f"{cc['nombre']}, España",
                  ["Alquiler mensual mediano", "Alquiler mediano por m²", "Renta neta media del hogar", "Alquiler sobre renta"],
                  f"{ser[0][0]}/{ser[-1][0]}" if ser else str(ANIO)),
          migas(pasos + [(nom, ruta)])]
    return head(titulo, desc, root, ruta, ld) + cuerpo + fin(root)


def pagina_comunidades(todas):
    root = "../"
    ruta = "comunidades/"
    cs = [x for x in COMUNIDADES.values() if x.get("alquiler_mes")]
    orden = sorted(cs, key=lambda x: -x["alquiler_mes"])
    fv = lambda v: "" if v is None else f"{v:.2f}"
    filas = []
    for x in orden:
        ch = cambio_19(x["serie_alquiler"])
        nomb = (f'<a href="{root}comunidades/{x["slug"]}/">{esc(x["comun"])}</a>' if x["pagina"] else esc(x["comun"]))
        if x["pagina"]:
            ciud = f'<a href="{root}comunidades/{x["slug"]}/#ciudades">{len(x["ciudades"])}</a>'
        else:
            ciud = ", ".join(f'<a href="{root}{c["slug"]}/">{esc(c["nombre"])}</a>' for c in x["ciudades"]) or "—"
        filas.append(f'<tr id="cc-{x["slug"]}"><th scope="row" data-v="{esc(x["comun"])}">{nomb}</th>'
                     f'<td data-v="{fv(x["alquiler_mes"])}">{n(x["alquiler_mes"])} €</td>'
                     f'<td data-v="{fv(x["eur_m2"])}">{d(x["eur_m2"], 2)}</td>'
                     f'<td data-v="{fv(ch)}">{pc_signo(ch)}</td>'
                     f'<td data-v="{len(x["ciudades"])}">{ciud}</td></tr>')
    sube = sorted([(cambio_19(x["serie_alquiler"]), x) for x in cs if cambio_19(x["serie_alquiler"]) is not None], key=lambda t: -t[0])
    desc = (f"Alquiler mediano de un piso en cada comunidad autónoma en {ANIO}, con datos oficiales del SERPAVI: "
            f"de {n(orden[-1]['alquiler_mes'])} € {orden[-1]['en']} a {n(orden[0]['alquiler_mes'])} € {orden[0]['en']}.")
    lead = (f"La mitad de los pisos alquilados como vivienda habitual cuesta menos de {n(orden[0]['alquiler_mes'])} € al mes {orden[0]['en']}, "
            f"la comunidad más cara, y menos de {n(orden[-1]['alquiler_mes'])} € {orden[-1]['en']}, la más barata. "
            + (f"Desde 2019, donde más ha subido el alquiler por m² es {sube[0][1]['en'][3:]} ({pc_signo(sube[0][0])}) "
               f"y donde menos, {sube[-1][1]['en'][3:]} ({pc_signo(sube[-1][0])})." if len(sube) >= 2 else ""))
    sin_pag = [x for x in COMUNIDADES.values() if not x["pagina"]]
    nota = (f'<p class="proto">Solo tienen página propia las comunidades con {MIN_CIUDADES_CCAA} o más ciudades de más de {MIN_POB} habitantes. '
            f'En el resto ({", ".join(x["comun"] for x in sorted(sin_pag, key=lambda x: norm(x["comun"])))}) enlazamos directamente sus ciudades.</p>'
            if sin_pag else "")
    cuerpo = (cabecera(root, [("#tabla", "Tabla")]) +
              f'<div class="hero"><div>{migas_html(root, [("Inicio", "")], "Comunidades autónomas")}'
              f'<h1>Alquiler por comunidad autónoma ({ANIO})</h1><p class="lead">{lead}</p>{aviso_turistico()}</div></div>'
              f'<main><section id="tabla"><div class="wrap"><table class="sortable" data-sort="1"><thead><tr>'
              f'{th_orden(0, "Comunidad", "text")}{th_orden(1, "Alquiler al mes")}{th_orden(2, "€/m²")}{th_orden(3, "Cambio €/m² desde 2019")}'
              f'{th_orden(4, f"Ciudades de más de {MIN_POB} hab.")}</tr></thead><tbody>{"".join(filas)}</tbody></table></div>{nota}</section>'
              f'{metodologia_ccaa()}{pie(root)}</main>')
    ld = [dataset(f"Alquiler por comunidad autónoma ({ANIO})", desc, ruta, "España", ["Alquiler mensual mediano", "Alquiler mediano por m²"]),
          migas([("Inicio", ""), ("Comunidades autónomas", ruta)])]
    return head(f"Alquiler por comunidad autónoma en España ({ANIO})", desc, root, ruta, ld) + cuerpo + fin(root)


# ------------------------------------------------------------------ recursos estáticos
CSS = r""".zona{display:block;font-weight:400;font-size:13px;color:var(--muted);margin-top:2px;max-width:34ch}
:root{--bg:#f3f5f6;--surface:#fff;--ink:#1f2933;--muted:#5b6672;--line:#dbe1e5;--acc:#0f7a5b;--on-acc:#fff;--tint:#e3f6ee;--lo:#e3f6ee;--hi:#0f7a5b;--nav-bg:#1f2933;--nav-fg:#fff;--nav-hi:#5fe0b0;--track:#e1e7ea;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#11181f;--surface:#1a232c;--ink:#e7ecef;--muted:#9ba7b0;--line:#2a3640;--acc:#4fcf9f;--on-acc:#0b1f1a;--tint:#17302a;--lo:#1d3a33;--hi:#4fcf9f;--nav-bg:#0b1117;--track:#26323c;color-scheme:dark}}
:root{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
html{scroll-padding-top:calc(env(safe-area-inset-top,0px) + 64px)}
@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
*,*::before,*::after{box-sizing:inherit}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);background:var(--nav-bg);z-index:30}
a{color:var(--acc)}
.top{position:sticky;top:env(safe-area-inset-top,0px);z-index:20;background:var(--nav-bg);color:var(--nav-fg)}
.top nav{max-width:980px;margin:0 auto;padding:0 20px;display:flex;align-items:center;gap:22px;height:56px;overflow-x:auto;white-space:nowrap}
.brand{font-weight:700;font-size:18px;margin-right:auto}
.top a{color:var(--nav-fg);text-decoration:none;font-size:15px;opacity:.85}
.top a.brand{opacity:1}
.top a.brand b,.top a:hover,.top a:focus-visible{color:var(--nav-hi);opacity:1}
.hero{background:linear-gradient(180deg,var(--tint),var(--bg));padding:44px 0 8px}
main,.hero>div{max-width:980px;margin:0 auto;padding:0 20px}
main{padding-bottom:56px}
h1{font:700 clamp(30px,6vw,46px)/1.12 Georgia,"Times New Roman",serif;margin:0 0 18px;letter-spacing:-.01em}
h2{font:700 26px/1.25 Georgia,"Times New Roman",serif;margin:56px 0 8px}
h3{font-size:17px;margin:0 0 8px}
section{scroll-margin-top:70px}
.sub{color:var(--muted);margin:0 0 20px;max-width:68ch}
.lead{font-size:19px;max-width:68ch;margin:0 0 26px}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));margin:0;border-top:3px solid var(--acc)}
.facts div{padding:14px 18px 14px 0}
.facts dt,.perfil dt{color:var(--muted);font-size:15px}
.facts dd{margin:2px 0 0;font-size:28px;font-weight:700;font-variant-numeric:tabular-nums}
.facts .big{color:var(--acc)}
.facts small{display:block;color:var(--muted);font-size:14px;font-weight:400}
.perfil{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:4px 18px;margin:0;border-top:1px solid var(--line)}
.perfil div{padding:10px 0;border-bottom:1px solid var(--line)}
.perfil dd{margin:0;font-weight:700;font-size:20px;font-variant-numeric:tabular-nums}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px;margin-bottom:20px}
.two ol,.lnk{list-style:none;margin:0;padding:0;border-top:1px solid var(--line)}
.two li,.lnk li{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}
.lnk span{color:var(--muted)}
.ctl{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 16px}
.ctl span{color:var(--muted);font-size:15px}
.ctl button{font:inherit;font-size:15px;padding:6px 14px;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:20px;cursor:pointer}
.ctl button[aria-pressed="true"]{background:var(--acc);color:var(--on-acc);border-color:var(--acc)}
button:focus-visible,input:focus-visible,a:focus-visible{outline:3px solid var(--acc);outline-offset:2px}
.mapbox{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(250px,1fr);gap:24px;align-items:start}
@media (max-width:760px){.mapbox{grid-template-columns:1fr}}
.grid{display:grid;grid-template-columns:repeat(7,1fr);grid-template-rows:repeat(6,1fr);gap:5px}
.tile{aspect-ratio:1/.85;border:0;border-radius:8px;padding:4px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;font:inherit;line-height:1.15;cursor:pointer;background:color-mix(in srgb,var(--hi) calc(var(--t)*100%),var(--lo));color:var(--c);transition:transform .12s}
.tile b{font-size:15px}
.tile span{font-size:11.5px;margin-top:2px}
.tile:hover,.tile:focus-visible,.tile[aria-pressed="true"]{transform:scale(1.08);outline:3px solid var(--ink);position:relative;z-index:2}
@media (max-width:640px){.tile span{display:none}.tile b{font-size:14px}}
.legend{display:flex;align-items:center;gap:10px;margin-top:14px;font-size:14px;color:var(--muted)}
.legend i{flex:1;max-width:240px;height:10px;border-radius:5px;background:linear-gradient(90deg,var(--lo),var(--hi))}
.panel{background:var(--surface);border:1px solid var(--line);border-top:3px solid var(--acc);border-radius:10px;padding:18px 20px}
.panel h3{font:700 22px/1.2 Georgia,serif;margin:0 0 2px}
.panel p{margin:0 0 12px;color:var(--muted);font-size:15px}
.panel dl{margin:0;display:grid;grid-template-columns:1fr auto;gap:6px 14px;font-variant-numeric:tabular-nums}
.panel dt{color:var(--muted);font-size:15px}
.panel dd{margin:0;font-weight:700;text-align:right}
.wrap{overflow-x:auto;border-top:3px solid var(--acc)}
table{width:100%;min-width:620px;border-collapse:collapse;font-variant-numeric:tabular-nums}
th,td{padding:9px 10px;text-align:right;border-bottom:1px solid var(--line);font-size:16px}
th:first-child,td:first-child{text-align:left;padding-left:0}
thead th{font-size:14px;color:var(--muted);font-weight:600;vertical-align:bottom}
thead button{font:inherit;color:inherit;background:none;border:0;cursor:pointer;padding:0;font-weight:inherit}
thead th[aria-sort] button{color:var(--ink)}
thead th[aria-sort="ascending"] button::after{content:" ▲";font-size:11px}
thead th[aria-sort="descending"] button::after{content:" ▼";font-size:11px}
tbody th{font-weight:600}
.numbered th:nth-child(2),.numbered td:nth-child(3){text-align:left}
.meter{display:grid;grid-template-columns:1fr 62px;gap:10px;align-items:center;min-width:170px}
.track{height:9px;background:var(--track);border-radius:5px;overflow:hidden}
.fill{display:block;height:100%;width:var(--w);background:var(--acc)}
.chart{width:100%;height:auto;display:block}
.chart text{fill:var(--muted);font:12px system-ui,sans-serif}
.chart .ln{fill:none;stroke:var(--acc);stroke-width:3;stroke-linejoin:round}
.chart .ar{fill:var(--tint)}
.chart .gl{stroke:var(--line)}
.chart circle{fill:var(--surface);stroke:var(--acc);stroke-width:2.5}
.chart circle:hover{fill:var(--acc)}
.notes{padding-left:20px}
.notes li{margin:0 0 10px;max-width:72ch}
.aviso{margin:16px 0 0;padding:12px 16px;border-left:4px solid #b7791f;background:var(--surface);font-size:15px;max-width:72ch}
.proto{margin:12px 0 0;padding:10px 14px;border-left:4px solid var(--acc);background:var(--surface);font-size:15px;color:var(--muted)}
.busca{display:block;max-width:520px;margin:6px 0 24px}
.busca span{display:block;font-size:15px;color:var(--muted);margin-bottom:4px}
.busca input{width:100%;font:inherit;font-size:18px;padding:12px 16px;border:2px solid var(--line);border-radius:10px;background:var(--surface);color:var(--ink)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.card{display:block;background:var(--surface);border:1px solid var(--line);border-top:3px solid var(--acc);border-radius:10px;padding:16px 18px;text-decoration:none;color:var(--ink)}
.card strong{display:block;margin-bottom:6px}
.card span{color:var(--muted);font-size:15px}
.card:hover{border-color:var(--acc)}
.todas{list-style:none;margin:0;padding:0;columns:3 260px;column-gap:28px}
.todas li{display:grid;grid-template-columns:1fr auto;gap:0 10px;padding:7px 0;border-bottom:1px solid var(--line);break-inside:avoid}
.todas span{grid-column:1;color:var(--muted);font-size:14px}
.todas strong{grid-row:1/3;grid-column:2;align-self:center;font-variant-numeric:tabular-nums}
.ccaa td:nth-child(2){text-align:left}
.migas{font-size:14px;color:var(--muted);margin:0 0 12px}
.migas a{color:var(--muted)}
.lnk.cols{columns:2 300px;column-gap:28px;border-top:0}
.lnk.cols li{break-inside:avoid}
footer{margin-top:48px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted);font-size:14px;max-width:76ch}
"""

JS = r"""(function(){
function nf(x){return x==null?"—":String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g,".")}
function df(x,k){return x==null?"—":x.toFixed(k).replace(".",",")}
function norm(s){return s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[’']/g,"")}
// tablas ordenables
document.querySelectorAll("table.sortable").forEach(function(t){
  var tb=t.tBodies[0],numbered=t.classList.contains("numbered");
  function sort(col,type,dir){
    var rows=Array.prototype.slice.call(tb.rows);
    function val(r){var c=r.cells[col],v=c.dataset.v;return type==="text"?(v||"").toLowerCase():(v===""||v==null?NaN:parseFloat(v))}
    rows.sort(function(a,b){var x=val(a),y=val(b);
      if(type==="text")return dir*x.localeCompare(y,"es");
      var nx=isNaN(x),ny=isNaN(y);if(nx&&ny)return 0;if(nx)return 1;if(ny)return -1;return dir*(x-y)});
    rows.forEach(function(r,i){tb.appendChild(r);if(numbered)r.cells[0].textContent=i+1});
    t.querySelectorAll("thead th").forEach(function(h){h.removeAttribute("aria-sort")});
    var th=t.querySelectorAll("thead th")[col];th.setAttribute("aria-sort",dir===1?"ascending":"descending");
  }
  t.querySelectorAll("thead button").forEach(function(b){
    b.addEventListener("click",function(){
      var col=+b.dataset.col,type=b.dataset.type,th=b.parentNode,cur=th.getAttribute("aria-sort");
      var dir=cur?(cur==="ascending"?-1:1):(type==="text"?1:-1);sort(col,type,dir)})});
  if(t.dataset.sort){var c=+t.dataset.sort;var b=t.querySelector('thead button[data-col="'+c+'"]');if(b&&!numbered)sort(c,b.dataset.type,-1);else if(b){var th=b.parentNode;th.setAttribute("aria-sort","descending")}}
});
// buscador de la portada
var q=document.getElementById("buscador");
if(q){var li=document.querySelectorAll("#lista li"),cu=document.getElementById("cuenta");
  q.addEventListener("input",function(){var s=norm(q.value.trim()),k=0;
    li.forEach(function(e){var ok=!s||e.dataset.b.indexOf(s)>-1;e.style.display=ok?"":"none";if(ok)k++});
    cu.textContent=k+(k===1?" ciudad":" ciudades")})}
// mapa esquemático
var el=document.getElementById("mapa-datos");
if(el){
  var M=JSON.parse(el.textContent),D=M.distritos,grid=document.getElementById("grid"),panel=document.getElementById("panel"),mctl=document.getElementById("mctl");
  var MET=[["pct","Peso del alquiler",function(v){return df(v,1)+" %"}],["alq","Alquiler al mes",function(v){return nf(v)+" €"}],["renta","Renta del hogar",function(v){return nf(v)+" €"}]];
  var mk="pct",tiles=[];
  function show(r,i){
    var dif=r.pct-M.media.pct,t=i<0?"Pasa el cursor por un distrito.":(Math.abs(dif)<0.05?"En la media de la ciudad.":df(Math.abs(dif),1)+" puntos "+(dif>0?"por encima":"por debajo")+" de la media de la ciudad.");
    panel.innerHTML="<h3>"+r.nombre+"</h3><p>"+t+"</p><dl><dt>Alquiler mediano</dt><dd>"+nf(r.alq)+" €/mes</dd><dt>Por m²</dt><dd>"+df(r.m2,2)+" €</dd><dt>Superficie mediana</dt><dd>"+nf(r.sup)+" m²</dd><dt>Renta del hogar</dt><dd>"+nf(r.renta)+" €/año</dd><dt>Alquiler sobre renta</dt><dd>"+df(r.pct,1)+" %</dd><dt>Inmuebles en la muestra</dt><dd>"+nf(r.inm)+"</dd></dl>";
  }
  D.forEach(function(r,i){
    var b=document.createElement("button");b.type="button";b.className="tile";
    b.style.gridColumn=r.col+1;b.style.gridRow=r.fila+1;b.setAttribute("aria-label","Distrito "+r.n+", "+r.nombre);
    b.innerHTML="<b>"+(r.n<10?"0":"")+r.n+"</b><span>"+r.nombre+"</span>";
    b.onmouseenter=b.onfocus=b.onclick=function(){tiles.forEach(function(t,j){t.setAttribute("aria-pressed",String(j===i))});show(r,i)};
    grid.appendChild(b);tiles.push(b)});
  function paint(){
    var vals=D.map(function(r){return r[mk]}),mn=Math.min.apply(null,vals),mx=Math.max.apply(null,vals),f=MET.filter(function(m){return m[0]===mk})[0][2];
    tiles.forEach(function(b,i){var t=(D[i][mk]-mn)/((mx-mn)||1);b.style.setProperty("--t",t.toFixed(3));b.style.setProperty("--c",t>.5?"var(--on-acc)":"var(--ink)")});
    document.getElementById("lmin").textContent=f(mn);document.getElementById("lmax").textContent=f(mx);
    mctl.querySelectorAll("button").forEach(function(b){b.setAttribute("aria-pressed",String(b.dataset.k===mk))});
  }
  MET.forEach(function(m){var b=document.createElement("button");b.type="button";b.textContent=m[1];b.dataset.k=m[0];b.onclick=function(){mk=m[0];paint()};mctl.appendChild(b)});
  paint();show(M.media,-1);
}
})();
"""


# ------------------------------------------------------------------ principal
def escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def main():
    global FECHA_GEN, FECHA_CALLEJERO
    datos = json.loads(DATOS.read_text(encoding="utf-8"))
    FECHA_GEN = datos.get("generado", "")
    FECHA_CALLEJERO = datos.get("fecha_callejero", "")
    todas = [c for c in datos["ciudades"] if c.get("alquiler_pct_renta") is not None and c.get("renta_hogar") and c.get("alquiler_mes")]
    omitidas = len(datos["ciudades"]) - len(todas)
    # rankings (1 = valor más alto)
    rank_n = {}
    for k in ("alquiler_pct_renta", "alquiler_mes", "eur_m2", "renta_hogar"):
        validas = sorted([c for c in todas if c.get(k) is not None], key=lambda c: -c[k])
        rank_n[k] = len(validas)
        for i, c in enumerate(validas, 1):
            c.setdefault("rank", {})[k] = i
    todas = [c for c in todas if all(k in c["rank"] for k in rank_n)]

    # comunidades autónomas (B-18)
    COMUNIDADES.clear()
    PROV_CCAA.clear()
    if DATOS_CCAA.exists():
        for x in json.loads(DATOS_CCAA.read_text(encoding="utf-8"))["comunidades"]:
            slug, comun, en = CCAA_INFO[x["cod_ccaa"]]
            x.update(slug=slug, comun=comun, en=en, ciudades=[])
            COMUNIDADES[x["cod_ccaa"]] = x
            PROV_CCAA.update({p_: x["cod_ccaa"] for p_ in x["provincias"]})
        for c in todas:
            COMUNIDADES[PROV_CCAA[c["cod_muni"][:2]]]["ciudades"].append(c)
        for x in COMUNIDADES.values():
            x["pagina"] = len(x["ciudades"]) >= MIN_CIUDADES_CCAA and bool(x.get("alquiler_mes"))
    else:
        print("AVISO: falta datos_limpios/comunidades.json (python preparar_comunidades.py). Sin páginas de comunidad.")
    con_pagina = sorted([x for x in COMUNIDADES.values() if x["pagina"]], key=lambda x: x["cod_ccaa"])

    if WEB.exists():
        shutil.rmtree(WEB)
    escribir(WEB / "assets" / "estilo.css", CSS)
    escribir(WEB / "assets" / "app.js", JS)
    for nombre_rec in ("og.png", "favicon.png", "favicon.ico"):
        if (RECURSOS / nombre_rec).exists():
            shutil.copy(RECURSOS / nombre_rec, WEB / nombre_rec)
    escribir(WEB / "index.html", pagina_indice(todas, rank_n))
    for slug, clave, titulo, df in RANKINGS:
        escribir(WEB / "rankings" / slug / "index.html", pagina_ranking(slug, clave, titulo, df, todas, rank_n))
    for c in todas:
        escribir(WEB / c["slug"] / "index.html", pagina_ciudad(c, todas, rank_n))
    if COMUNIDADES:
        escribir(WEB / "comunidades" / "index.html", pagina_comunidades(todas))
    for x in con_pagina:
        escribir(WEB / "comunidades" / x["slug"] / "index.html", pagina_comunidad(x, todas, rank_n))

    urls = ([""] + [f"rankings/{s}/" for s, *_ in RANKINGS]
            + (["comunidades/"] if COMUNIDADES else []) + [f"comunidades/{x['slug']}/" for x in con_pagina]
            + [f"{c['slug']}/" for c in todas])
    robots = "User-agent: *\nAllow: /\n"
    if BASE_URL:
        mapa = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + "".join(f"<url><loc>{BASE_URL}/{u}</loc>" + (f"<lastmod>{FECHA_GEN}</lastmod>" if FECHA_GEN else "") + "</url>\n" for u in urls) + "</urlset>\n")
        escribir(WEB / "sitemap.xml", mapa)
        robots += f"Sitemap: {BASE_URL}/sitemap.xml\n"
    escribir(WEB / "robots.txt", robots)
    if BASE_URL:
        # GitHub Pages: dominio propio (sin https:// ni barra)
        escribir(WEB / "CNAME", BASE_URL.split("://", 1)[1] + "\n")

    print(f"Web generada en: {WEB}")
    print(f"  Páginas de ciudad: {len(todas)} (omitidas por falta de datos: {omitidas})")
    print(f"  Rankings: {len(RANKINGS)} | Comunidades: {len(con_pagina)} + índice | Portada: 1 | Total de páginas: {len(urls)}")
    print("  Con mapa esquemático:", sum(1 for c in todas if c["cod_muni"] in TILE))
    print("  Sitemap:", "sí" if BASE_URL else "no (BASE_URL vacío; se creará cuando tengas dirección web)")
    print("\nPara verla en tu ordenador:  cd web   y luego   python -m http.server 8000")
    print("y abre http://localhost:8000 en el navegador.")


if __name__ == "__main__":
    main()
