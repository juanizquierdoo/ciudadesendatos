"""Comparador de 2 a 4 ciudades, lado a lado (Fase 2, n.º 2 del ranking de INFORME_FASE0.md; B-35).

    /comparar-ciudades/                       (arranca con las 4 ciudades más pobladas)
    /comparar-ciudades/?c=madrid,valladolid   (enlace para compartir: guarda las ciudades elegidas)

Eliges de 2 a 4 ciudades y la página pone lado a lado su alquiler, su renta, su población y sus
distritos más baratos y más caros, con unas frases que resumen las diferencias y un gráfico de la
evolución del alquiler.

Solo usa datos que ya están en ciudades_nivel1.json (alquiler SERPAVI y renta y población INE):
no hay datos nuevos ni estimaciones nuevas. Los cálculos derivados (cambios en %, ingresos para la
regla del 30 %) son los mismos que ya publican los rankings y la calculadora del sueldo.
El cálculo se hace en el navegador con los datos incrustados en la página (sin cookies ni llamadas
a otros sitios). Sin JavaScript se ve la comparación de las 4 ciudades más pobladas, calculada aquí
en Python con las mismas reglas.

No se crea una página por pareja de ciudades: serían miles de páginas casi iguales (regla 8).
Una sola página, y los enlaces de ejemplo usan ?c=..., con canonical a la página principal.

Los distritos siguen la misma regla que la ficha: menos de 30 inmuebles = no se usa su alquiler;
de 30 a 99 se marca con *. Los nombres de distrito nunca llevan código postal (herramienta_sueldo.nombre_distrito).

generar_web.py solo hace tres cosas con este módulo: tarjeta() en la portada, enlace_ficha() en la
sección "Compara con otras ciudades" de cada ficha y generar() en main(), que devuelve la URL para el sitemap.
"""
import json

import herramienta_sueldo as hs

SLUG = "comparar-ciudades"
TITULO = "Comparador de ciudades"
H1 = "Compara ciudades de España"
DESC_TARJETA = "Elige de 2 a 4 ciudades y compara lado a lado su alquiler, su renta, su población y sus distritos."
MAX_CIUDADES = 4
N_DEFECTO = 4                    # sin parámetros, la página compara las 4 ciudades más pobladas
PCT = hs.PCT_DEFECTO             # regla orientativa del 30 %, la misma que la calculadora del sueldo
AÑOS_CAMBIO = 5                  # igual que el ranking "dónde más sube el alquiler"
COLORES = ("#1c4f8f", "#c2410c", "#0f766e", "#8b3fbf")   # una por columna (tabla, leyenda y gráfico)
# Ejemplos de comparación (cód. INE). No son búsquedas medidas: solo atajos. Se omiten las que no tengan ficha.
EJEMPLOS = [("28079", "08019"), ("46250", "41091"), ("29067", "41091", "18087"),
            ("48020", "20069", "01059"), ("47186", "37274", "09059", "24089"), ("03014", "30030", "03065")]


def tarjeta(root):
    return (f'<a class="card" href="{root}{SLUG}/"><strong>{hs._esc(TITULO)}</strong>'
            f'<span>{hs._esc(DESC_TARJETA)}</span></a>')


def enlace_ficha(root, c):
    """Enlace desde la ficha de una ciudad al comparador con esa ciudad ya elegida."""
    return (f'<p><a href="{root}{SLUG}/?c={c["slug"]}">Compara {hs._esc(c["nombre"])} lado a lado con otras ciudades</a>: '
            'alquiler, renta, población y distritos.</p>')


# ------------------------------------------------------------------ datos
def _en(c, anio, lista="serie_alquiler", clave="alquiler_mes"):
    for s in c.get(lista, []):
        if s["anio"] == anio and s.get(clave) is not None:
            return s[clave]
    return None


def _var(a, b):
    return None if a in (None, 0) or b is None else (b / a - 1) * 100


def _r(x, k=4):
    return None if x is None else round(x, k)


def filas(gw):
    """Filas de la tabla: [clave, etiqueta, decimales, unidad, con signo, grupo, ayuda]. Las usan Python y JavaScript."""
    A, A0 = gw.ANIO, gw.ANIO - AÑOS_CAMBIO
    return [
        ["alq", "Alquiler mediano de un piso", 0, " € al mes", False, "Alquiler", ""],
        ["m2", "Alquiler por m²", 2, " €/m²", False, "Alquiler", "Debajo, el rango del 50 % central de los pisos"],
        ["sup", "Superficie mediana del piso alquilado", 0, " m²", False, "Alquiler", ""],
        ["pcr", "Alquiler sobre la renta del hogar", 1, " %", False, "Alquiler", "Estimación propia: alquiler mediano × 12 / renta media del hogar"],
        ["sueldo", f"Ingresos netos al mes para que el alquiler no pase del {PCT} %", 0, " €", False, "Alquiler", "Regla orientativa, no un umbral oficial"],
        ["ch5", f"Cambio del alquiler {A0}-{A}", 1, " %", True, "Alquiler", ""],
        ["ch1", f"Cambio del alquiler {A - 1}-{A}", 1, " %", True, "Alquiler", ""],
        ["renta", "Renta neta media por hogar", 0, " € al año", False, "Renta de los hogares", ""],
        ["rper", "Renta neta media por persona", 0, " € al año", False, "Renta de los hogares", ""],
        ["chr5", f"Cambio de la renta del hogar {A0}-{A}", 1, " %", True, "Renta de los hogares", "Sin descontar la inflación"],
        ["par", "Paro registrado (personas)", 0, "", False, "Empleo", "SEPE, último mes publicado. No es la tasa de paro de la EPA"],
        ["p100", "Parados por cada 100 habitantes de 18 a 64 años", 1, "", False, "Empleo", "Estimación propia: paro registrado / población de 18 a 64 años"],
        ["chpar", "Cambio del paro registrado en un año", 1, " %", True, "Empleo", "Mismo mes del año anterior"],
        ["pob", "Población", 0, "", False, "Población", ""],
        ["edad", "Edad media", 1, " años", False, "Población", ""],
        ["m18", "Menores de 18 años", 1, " %", False, "Población", ""],
        ["m65", "Mayores de 65 años", 1, " %", False, "Población", ""],
        ["uni", "Hogares de una sola persona", 1, " %", False, "Población", ""],
        ["tam", "Tamaño medio del hogar", 2, " personas", False, "Población", ""],
        ["nd", "Distritos con dato de alquiler", 0, "", False, "Distritos", "Con 30 inmuebles o más en la muestra"],
        ["dmin", "Distrito con el alquiler más bajo", 0, " €", False, "Distritos", ""],
        ["dmax", "Distrito con el alquiler más alto", 0, " €", False, "Distritos", ""],
    ]


def _dist(x):
    return [x["numero"], hs.nombre_distrito(x), round(x["alquiler_mes"], 2), int(x["fiabilidad"] == "pocos_datos")]


def ciudad_js(gw, c):
    """Datos de una ciudad para la página (los mismos para Python y para JavaScript)."""
    A, A0 = gw.ANIO, gw.ANIO - AÑOS_CAMBIO
    ds = hs.distritos_validos(c)
    cc = gw.CCAA_INFO.get(gw.PROV_CCAA.get(c["cod_muni"][:2], ""), ("", "", ""))[1]
    v = {"alq": c["alquiler_mes"], "m2": c.get("eur_m2"), "sup": c.get("superficie_m2"), "pcr": c["alquiler_pct_renta"],
         "sueldo": c["alquiler_mes"] / (PCT / 100),
         "ch5": _var(_en(c, A0), _en(c, A)), "ch1": _var(_en(c, A - 1), _en(c, A)),
         "renta": c["renta_hogar"], "rper": c.get("renta_persona"),
         "chr5": _var(_en(c, A0, "serie_renta", "renta_hogar"), _en(c, A, "serie_renta", "renta_hogar")),
         "pob": c.get("poblacion"), "edad": c.get("edad_media"), "m18": c.get("pct_menor_18"), "m65": c.get("pct_65_mas"),
         "uni": c.get("pct_unipersonales"), "tam": c.get("tam_hogar"), "nd": len(ds),
         "par": (c.get("paro") or {}).get("total"), "p100": (c.get("paro") or {}).get("por_100"),
         "chpar": _var((c.get("paro") or {}).get("anterior"), (c.get("paro") or {}).get("total"))}
    out = {"n": c["nombre"], "s": c["slug"], "p": c["provincia"], "cc": cc, "pob": c.get("poblacion") or 0,
           "v": {k: _r(x) for k, x in v.items()},
           "m2r": [c["eur_m2_p25"], c["eur_m2_p75"]] if c.get("eur_m2_p25") is not None and c.get("eur_m2_p75") is not None else None,
           "ser": [[s["anio"], round(s["alquiler_mes"], 2)] for s in c.get("serie_alquiler", []) if s.get("alquiler_mes") is not None],
           "dmin": None, "dmax": None}
    if len(ds) >= 2:
        out["dmin"] = _dist(min(ds, key=lambda x: (x["alquiler_mes"], x["numero"])))
        out["dmax"] = _dist(max(ds, key=lambda x: (x["alquiler_mes"], -x["numero"])))
    return out


def datos_js(gw, todas):
    return [ciudad_js(gw, c) for c in sorted(todas, key=lambda c: c["nombre"])]


def por_defecto(todas):
    return sorted(todas, key=lambda c: (-(c.get("poblacion") or 0), c["nombre"]))[:N_DEFECTO]


# ------------------------------------------------------------------ formato (igual que el JavaScript)
def fmt(gw, v, dec, suf="", signo=False):
    if v is None:
        return "—"
    t = gw.n(v) if dec == 0 else gw.d(v, dec)
    if signo and round(v, dec) > 0:
        t = "+" + t
    return t + suf


def tabla(gw, cs, R):
    """Tabla de comparación (la misma que dibuja el JavaScript)."""
    esc = gw.esc
    th = "".join(f'<th scope="col"><span class="sw" style="background:{COLORES[i]}"></span><a href="../{c["s"]}/">{esc(c["n"])}</a>'
                 f'<span class="prov">{esc(c["p"])}</span></th>' for i, c in enumerate(cs))
    cuerpo, grupo = "", None
    for k, et, dec, suf, signo, g, ayuda in R:
        if g != grupo:
            grupo = g
            cuerpo += f'<tr class="grupo"><th scope="colgroup" colspan="{len(cs) + 1}">{esc(g)}</th></tr>'
        celdas = ""
        if k in ("dmin", "dmax"):
            for c in cs:
                x = c[k]
                celdas += ("<td>—</td>" if not x else
                           f'<td><a href="../{c["s"]}/#d{x[0]}">{esc(x[1])}</a><span class="cifra">{fmt(gw, x[2], 0, " €")}{"*" if x[3] else ""}</span></td>')
        else:
            vals = [c["v"][k] for c in cs]
            ok = [x for x in vals if x is not None]
            mx = max(ok) if len(ok) > 1 and max(ok) != min(ok) else None
            for c, x in zip(cs, vals):
                extra = ""
                if k == "m2" and c["m2r"]:
                    extra = f'<span class="ayuda">entre {fmt(gw, c["m2r"][0], 2)} y {fmt(gw, c["m2r"][1], 2)} €/m²</span>'
                cls = ' class="max"' if mx is not None and x == mx else ""
                celdas += f'<td{cls}>{fmt(gw, x, dec, suf, signo)}{extra}</td>'
        ay = f'<span class="ayuda">{esc(ayuda)}</span>' if ayuda else ""
        cuerpo += f'<tr><th scope="row">{esc(et)}{ay}</th>{celdas}</tr>'
    return (f'<table class="cmp"><thead><tr><th scope="col">Dato</th>{th}</tr></thead><tbody>{cuerpo}</tbody></table>')


def claves_sel(gw, cs):
    """Frases con las diferencias entre las ciudades elegidas (las mismas que el JavaScript)."""
    if len(cs) < 2:
        return ["Elige al menos dos ciudades para ver las diferencias."]
    out = []

    def ext(k):
        con = [c for c in cs if c["v"][k] is not None]
        if len(con) < 2:
            return None, None
        lo = min(con, key=lambda c: c["v"][k])
        hi = max(con, key=lambda c: c["v"][k])
        return (lo, hi) if lo["v"][k] != hi["v"][k] else (None, None)

    lo, hi = ext("alq")
    if lo:
        out.append(f"El alquiler mediano de un piso es un {fmt(gw, (hi['v']['alq'] / lo['v']['alq'] - 1) * 100, 0)} % más alto "
                   f"en {hi['n']} ({fmt(gw, hi['v']['alq'], 0)} € al mes) que en {lo['n']} ({fmt(gw, lo['v']['alq'], 0)} €).")
    lo, hi = ext("renta")
    if lo:
        out.append(f"La renta neta media por hogar va de {fmt(gw, lo['v']['renta'], 0)} € al año en {lo['n']} "
                   f"a {fmt(gw, hi['v']['renta'], 0)} € en {hi['n']}.")
    lo, hi = ext("pcr")
    if lo:
        out.append(f"El alquiler pesa menos sobre la renta del hogar en {lo['n']} ({fmt(gw, lo['v']['pcr'], 1)} %) "
                   f"y más en {hi['n']} ({fmt(gw, hi['v']['pcr'], 1)} %).")
    lo, hi = ext("sueldo")
    if lo:
        out.append(f"Para que el alquiler mediano no pase del {PCT} % de los ingresos, hacen falta unos {fmt(gw, lo['v']['sueldo'], 0)} € "
                   f"netos al mes en {lo['n']} y unos {fmt(gw, hi['v']['sueldo'], 0)} € en {hi['n']}.")
    lo, hi = ext("edad")
    if lo:
        out.append(f"La población más joven es la de {lo['n']} (edad media de {fmt(gw, lo['v']['edad'], 1)} años) "
                   f"y la de más edad, la de {hi['n']} ({fmt(gw, hi['v']['edad'], 1)} años).")
    return out


# ------------------------------------------------------------------ texto fijo para Google
def _claves_generales(gw, todas):
    """Párrafos calculados con todas las ciudades: qué cambia al comparar (no dependen de la selección)."""
    esc, out = gw.esc, []
    grandes = sorted(todas, key=lambda c: (-(c.get("poblacion") or 0), c["nombre"]))[:10]
    lo = min(grandes, key=lambda c: c["alquiler_mes"])
    hi = max(grandes, key=lambda c: c["alquiler_mes"])
    out.append(f"Entre las 10 ciudades más pobladas, el alquiler mediano de un piso va de {gw.n(lo['alquiler_mes'])} € al mes en "
               f"{esc(lo['nombre'])} a {gw.n(hi['alquiler_mes'])} € en {esc(hi['nombre'])}, y la renta neta media por hogar, de "
               f"{gw.n(min(c['renta_hogar'] for c in grandes))} € a {gw.n(max(c['renta_hogar'] for c in grandes))} € al año.")
    cod = {c["cod_muni"]: c for c in todas}
    m, b = cod.get("28079"), cod.get("08019")
    if m and b:
        caro, barato = (m, b) if m["alquiler_mes"] >= b["alquiler_mes"] else (b, m)
        out.append(f"Madrid y Barcelona: el alquiler mediano es de {gw.n(m['alquiler_mes'])} € en Madrid y de {gw.n(b['alquiler_mes'])} € en Barcelona "
                   f"({gw.d((caro['alquiler_mes'] / barato['alquiler_mes'] - 1) * 100, 0)} % más en {esc(caro['nombre'])}). "
                   f"Sobre la renta del hogar, el alquiler pesa un {gw.pc(m['alquiler_pct_renta'])} en Madrid y un {gw.pc(b['alquiler_pct_renta'])} en Barcelona.")
    # dentro de una ciudad, la diferencia entre distritos puede ser mayor que entre ciudades
    mejor = None
    for c in grandes:
        ds = hs.distritos_validos(c)
        if len(ds) >= 4:
            a, z = min(ds, key=lambda x: x["alquiler_mes"]), max(ds, key=lambda x: x["alquiler_mes"])
            r = z["alquiler_mes"] / a["alquiler_mes"]
            if mejor is None or r > mejor[0]:
                mejor = (r, c, a, z)
    if mejor:
        r, c, a, z = mejor
        out.append(f"Dentro de una misma ciudad la diferencia puede ser mayor que entre ciudades. En {esc(c['nombre'])}, el alquiler mediano va de "
                   f"{gw.n(a['alquiler_mes'])} € en {esc(hs.nombre_distrito(a))} a {gw.n(z['alquiler_mes'])} € en {esc(hs.nombre_distrito(z))}. "
                   "Por eso el comparador muestra también el distrito más barato y el más caro de cada ciudad.")
    out.append("Compara alquileres sabiendo qué son: contratos vigentes declarados a Hacienda, no anuncios. Un piso que se alquile hoy suele costar más, "
               "pero la comparación entre ciudades es coherente porque todas se miden con la misma fuente y el mismo método.")
    return out


def _ejemplos(gw, todas):
    cod = {c["cod_muni"]: c for c in todas}
    lis = ""
    for e in EJEMPLOS:
        cs = [cod[x] for x in e if x in cod]
        if len(cs) >= 2:
            lis += (f'<li><a href="./?c={",".join(c["slug"] for c in cs)}">'
                    f'{gw.esc(hs._y([c["nombre"] for c in cs]))}</a></li>')
    return lis


CSS_PAGINA = """<style>
.cmp-sel{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:18px 0 8px}
@media (max-width:760px){.cmp-sel{grid-template-columns:repeat(2,minmax(0,1fr))}}
.cmp-sel label{display:flex;flex-direction:column;gap:6px;font-weight:600;font-size:15px}
.cmp-sel label .sw{margin-right:6px}
.cmp-sel select{font:inherit;font-weight:400;padding:10px 12px;border:1px solid var(--line);border-radius:6px;background:#fff;color:var(--ink);width:100%}
.cmp-sel select:focus{outline:2px solid var(--acc);outline-offset:1px}
.cmp-acc{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:4px 0 16px}
.cmp-acc button{font:inherit;padding:8px 14px;border:1px solid var(--acc);color:var(--acc);background:#fff;border-radius:6px;cursor:pointer}
.cmp-acc .sub{margin:0}
.sw{display:inline-block;width:11px;height:11px;border-radius:50%;vertical-align:baseline}
.cmp-wrap{overflow-x:auto;border-top:3px solid var(--ink)}
table.cmp{border-collapse:collapse;width:100%;min-width:0;font-variant-numeric:tabular-nums}
table.cmp th,table.cmp td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top;min-width:120px}
table.cmp thead th{text-align:right;font-size:15px;line-height:1.3}
table.cmp thead th a{font-weight:700;color:var(--ink);text-decoration:none}
table.cmp thead th a::after{content:" ›";color:var(--acc)}
table.cmp thead th .sw{margin-right:6px}
table.cmp .prov{display:block;color:var(--muted);font-weight:400;font-size:13px}
table.cmp th:first-child{text-align:left;position:sticky;left:0;background:#fff;z-index:1;min-width:150px;max-width:240px;font-weight:600;font-size:15px}
table.cmp tr.grupo th{background:var(--surface);text-align:left;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);position:static}
table.cmp td.max{font-weight:700}
table.cmp .ayuda{display:block;color:var(--muted);font-weight:400;font-size:12.5px;line-height:1.35;margin-top:2px}
table.cmp td a{color:var(--ink)}
table.cmp td .cifra{display:block;font-weight:600}
@media (max-width:640px){table.cmp th,table.cmp td{min-width:100px;padding:8px 6px;font-size:14px}table.cmp th:first-child{min-width:112px;max-width:130px;font-size:14px}table.cmp thead th{font-size:14px}}
.cmp-leg{list-style:none;padding:0;margin:0 0 6px;display:flex;flex-wrap:wrap;gap:6px 18px;font-size:15px}
.cmp-leg .sw{margin-right:6px}
#cmp-graf svg{width:100%;height:auto;display:block}
#cmp-graf .gl{stroke:var(--line)}
#cmp-graf text{font-size:12px;fill:var(--muted)}
</style>"""


JS_PAGINA = r"""<script>(function(){
var D=JSON.parse(document.getElementById("cmp-datos").textContent),R=JSON.parse(document.getElementById("cmp-filas").textContent),
    M=JSON.parse(document.getElementById("cmp-meta").textContent),BY={},
    sels=[].slice.call(document.querySelectorAll("#cmp-form select")),tab=document.getElementById("cmp-tabla"),
    cla=document.getElementById("cmp-claves"),graf=document.getElementById("cmp-graf"),leg=document.getElementById("cmp-leg"),
    cop=document.getElementById("cmp-copiar"),aviso=document.getElementById("cmp-aviso"),SVG="http://www.w3.org/2000/svg";
D.forEach(function(c){BY[c.s]=c});
var grp={};D.forEach(function(c){var g=c.cc||"Otras";(grp[g]=grp[g]||[]).push(c)});
var gk=Object.keys(grp).sort(function(a,b){return a.localeCompare(b,"es")});
sels.forEach(function(s){var cur=s.value;s.innerHTML="";var o=el("option",null,"Elige una ciudad");o.value="";s.appendChild(o);
  gk.forEach(function(g){var og=document.createElement("optgroup");og.label=g;
    grp[g].slice().sort(function(a,b){return a.n.localeCompare(b.n,"es")}).forEach(function(c){var o=el("option",null,c.n);o.value=c.s;og.appendChild(o)});
    s.appendChild(og)});s.value=cur});
function rnd(x,dec){var p=Math.pow(10,dec),y=x*p,f=Math.floor(y);return (Math.abs(y-f-0.5)<1e-9?(f%2===0?f:f+1):Math.round(y))/p}
function nf(x,dec,suf,signo){if(x==null)return "—";var v=rnd(x,dec),s=Math.abs(v).toFixed(dec).split(".");
  s[0]=s[0].replace(/\B(?=(\d{3})+(?!\d))/g,".");return (v<0?"-":(signo&&v>0?"+":""))+s.join(",")+(suf||"")}
function el(t,c,txt){var e=document.createElement(t);if(c)e.className=c;if(txt!=null)e.textContent=txt;return e}
function sw(i){var s=el("span","sw");s.style.background=M.colores[i];return s}
function elegidas(){var vis={},out=[];sels.forEach(function(s){var c=BY[s.value];if(c&&!vis[c.s]){vis[c.s]=1;out.push(c)}});return out}
function ext(cs,k){var con=cs.filter(function(c){return c.v[k]!=null});if(con.length<2)return null;
  var lo=con[0],hi=con[0];con.forEach(function(c){if(c.v[k]<lo.v[k])lo=c;if(c.v[k]>hi.v[k])hi=c});return lo.v[k]===hi.v[k]?null:[lo,hi]}
function claves(cs){
  if(cs.length<2)return ["Elige al menos dos ciudades para ver las diferencias."];
  var o=[],e;
  if(e=ext(cs,"alq"))o.push("El alquiler mediano de un piso es un "+nf((e[1].v.alq/e[0].v.alq-1)*100,0)+" % más alto en "+e[1].n+" ("+nf(e[1].v.alq,0)+" € al mes) que en "+e[0].n+" ("+nf(e[0].v.alq,0)+" €).");
  if(e=ext(cs,"renta"))o.push("La renta neta media por hogar va de "+nf(e[0].v.renta,0)+" € al año en "+e[0].n+" a "+nf(e[1].v.renta,0)+" € en "+e[1].n+".");
  if(e=ext(cs,"pcr"))o.push("El alquiler pesa menos sobre la renta del hogar en "+e[0].n+" ("+nf(e[0].v.pcr,1)+" %) y más en "+e[1].n+" ("+nf(e[1].v.pcr,1)+" %).");
  if(e=ext(cs,"sueldo"))o.push("Para que el alquiler mediano no pase del "+M.pct+" % de los ingresos, hacen falta unos "+nf(e[0].v.sueldo,0)+" € netos al mes en "+e[0].n+" y unos "+nf(e[1].v.sueldo,0)+" € en "+e[1].n+".");
  if(e=ext(cs,"edad"))o.push("La población más joven es la de "+e[0].n+" (edad media de "+nf(e[0].v.edad,1)+" años) y la de más edad, la de "+e[1].n+" ("+nf(e[1].v.edad,1)+" años).");
  return o}
function tabla(cs){
  var t=el("table","cmp"),th=el("thead"),tr=el("tr"),h=el("th",null,"Dato");h.scope="col";tr.appendChild(h);
  cs.forEach(function(c,i){var h=el("th"),a=el("a",null,c.n);h.scope="col";a.href="../"+c.s+"/";h.appendChild(sw(i));h.appendChild(a);h.appendChild(el("span","prov",c.p));tr.appendChild(h)});
  th.appendChild(tr);t.appendChild(th);var tb=el("tbody"),g=null;
  R.forEach(function(r){var k=r[0];
    if(r[5]!==g){g=r[5];var gr=el("tr","grupo"),gh=el("th",null,g);gh.scope="colgroup";gh.colSpan=cs.length+1;gr.appendChild(gh);tb.appendChild(gr)}
    var row=el("tr"),lh=el("th",null,r[1]);lh.scope="row";if(r[6])lh.appendChild(el("span","ayuda",r[6]));row.appendChild(lh);
    if(k==="dmin"||k==="dmax"){cs.forEach(function(c){var td=el("td"),x=c[k];
      if(!x)td.textContent="—";else{var a=el("a",null,x[1]);a.href="../"+c.s+"/#d"+x[0];td.appendChild(a);td.appendChild(el("span","cifra",nf(x[2],0," €")+(x[3]?"*":"")))}
      row.appendChild(td)})}
    else{var vals=cs.map(function(c){return c.v[k]}),ok=vals.filter(function(v){return v!=null}),
      mx=ok.length>1&&Math.max.apply(null,ok)!==Math.min.apply(null,ok)?Math.max.apply(null,ok):null;
      cs.forEach(function(c,i){var td=el("td",mx!==null&&vals[i]===mx?"max":null,nf(vals[i],r[2],r[3],r[4]));
        if(k==="m2"&&c.m2r)td.appendChild(el("span","ayuda","entre "+nf(c.m2r[0],2)+" y "+nf(c.m2r[1],2)+" €/m²"));row.appendChild(td)})}
    tb.appendChild(row)});
  t.appendChild(tb);return t}
function paso(raw){var m=Math.pow(10,Math.floor(Math.log10(raw)));for(var i=0,f=[1,2,2.5,5,10];i<f.length;i++)if(raw<=f[i]*m)return f[i]*m;return 10*m}
function sv(t,a,txt){var e=document.createElementNS(SVG,t);for(var k in a)e.setAttribute(k,a[k]);if(txt!=null)e.textContent=txt;return e}
function grafico(cs){
  graf.innerHTML="";leg.innerHTML="";
  var ss=cs.filter(function(c){return c.ser.length>=2});
  if(!ss.length){graf.appendChild(el("p","sub","No hay serie histórica suficiente para estas ciudades."));return}
  cs.forEach(function(c,i){var li=el("li");li.appendChild(sw(i));li.appendChild(document.createTextNode(c.n));leg.appendChild(li)});
  var W=720,H=300,L=52,Rm=16,T=16,B=34,xs=[],ys=[];
  ss.forEach(function(c){c.ser.forEach(function(p){xs.push(p[0]);ys.push(p[1])})});
  var x0=Math.min.apply(null,xs),x1=Math.max.apply(null,xs),lo=Math.min.apply(null,ys),hi=Math.max.apply(null,ys),
      st=paso((hi-lo)/4||50),y0=Math.floor(lo/st)*st,y1=Math.ceil(hi/st)*st;if(y1===y0)y1=y0+st;
  function X(a){return L+(a-x0)/((x1-x0)||1)*(W-L-Rm)}function Y(v){return H-B-(v-y0)/(y1-y0)*(H-B-T)}
  var s=sv("svg",{viewBox:"0 0 "+W+" "+H,role:"img","aria-label":"Evolución del alquiler mediano de un piso, en euros al mes: "+cs.map(function(c){return c.n}).join(", ")});
  for(var v=y0;v<=y1+st/1000;v+=st){s.appendChild(sv("line",{"class":"gl",x1:L,x2:W-Rm,y1:Y(v).toFixed(1),y2:Y(v).toFixed(1)}));
    s.appendChild(sv("text",{x:L-8,y:(Y(v)+4).toFixed(1),"text-anchor":"end"},nf(v,0)+" €"))}
  var cada=(x1-x0)>8?2:1;for(var a=x0;a<=x1;a++)if((a-x0)%cada===0||a===x1)s.appendChild(sv("text",{x:X(a).toFixed(1),y:H-12,"text-anchor":"middle"},String(a)));
  cs.forEach(function(c,i){if(c.ser.length<2)return;var col=M.colores[i];
    s.appendChild(sv("polyline",{points:c.ser.map(function(p){return X(p[0]).toFixed(1)+","+Y(p[1]).toFixed(1)}).join(" "),fill:"none",stroke:col,"stroke-width":2.5,"stroke-linejoin":"round"}));
    c.ser.forEach(function(p){var ci=sv("circle",{cx:X(p[0]).toFixed(1),cy:Y(p[1]).toFixed(1),r:3.5,fill:col});ci.appendChild(sv("title",{},c.n+", "+p[0]+": "+nf(p[1],0)+" € al mes"));s.appendChild(ci)})});
  graf.appendChild(s)}
function pintar(cambio){
  var cs=elegidas();
  if(cambio){try{history.replaceState(null,"",location.pathname+(cs.length?"?c="+cs.map(function(c){return c.s}).join(","):""))}catch(e){}}
  aviso.textContent=cs.length<2?"Elige al menos dos ciudades.":"";
  tab.innerHTML="";if(cs.length)tab.appendChild(tabla(cs));
  cla.innerHTML="";claves(cs).forEach(function(p){cla.appendChild(el("p",null,p))});
  grafico(cs)}
var q=new URLSearchParams(location.search),ini=[];
(q.get("c")||"").split(",").forEach(function(x){x=x.trim();if(BY[x]&&ini.indexOf(x)<0&&ini.length<M.max)ini.push(x)});
if(ini.length===1){var c0=BY[ini[0]],sug=null;D.forEach(function(c){if(c.s!==c0.s&&c.cc===c0.cc&&(!sug||c.pob>sug.pob))sug=c});
  if(!sug)D.forEach(function(c){if(c.s!==c0.s&&(!sug||c.pob>sug.pob))sug=c});if(sug)ini.push(sug.s)}
if(ini.length){sels.forEach(function(s,i){s.value=ini[i]||""})}
sels.forEach(function(s){s.addEventListener("change",function(){pintar(true)})});
document.getElementById("cmp-form").addEventListener("submit",function(e){e.preventDefault()});
cop.hidden=false;cop.addEventListener("click",function(){var u=location.href;
  function ok(){cop.textContent="Enlace copiado"}function no(){cop.textContent="Copia la dirección de la barra del navegador"}
  try{navigator.clipboard.writeText(u).then(ok,no)}catch(e){no()}});
pintar(false);
})();</script>"""


def pagina(gw, todas):
    root = "../"
    esc = gw.esc
    N = len(todas)
    R = filas(gw)
    datos = datos_js(gw, todas)
    by = {c["s"]: c for c in datos}
    defecto = [by[c["slug"]] for c in por_defecto(todas)]
    meta = {"max": MAX_CIUDADES, "colores": list(COLORES), "pct": PCT}
    js_bloque = lambda id_, obj: (f'<script type="application/json" id="{id_}">'
                                  + json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>")
    # Desplegables: en el HTML solo va la ciudad elegida por defecto; el JavaScript añade la lista completa
    # (151 ciudades agrupadas por comunidad). Así la página no repite 4 veces la lista entera.
    def opciones(sel):
        o = f'<option value=""{"" if sel else " selected"}>Elige una ciudad</option>'
        if sel:
            o += f'<option value="{sel}" selected>{esc(by[sel]["n"])}</option>'
        return o
    selects = "".join(
        f'<label for="cmp-c{i + 1}"><span><span class="sw" style="background:{COLORES[i]}"></span>Ciudad {i + 1}'
        f'{" (opcional)" if i >= 2 else ""}</span><select id="cmp-c{i + 1}">{opciones(defecto[i]["s"] if i < len(defecto) else "")}</select></label>'
        for i in range(MAX_CIUDADES))
    form = (f'<form id="cmp-form" class="cmp-sel" aria-label="Elige las ciudades que quieres comparar">{selects}</form>'
            '<div class="cmp-acc"><button type="button" id="cmp-copiar" hidden>Copiar enlace para compartir</button>'
            '<p class="sub" id="cmp-aviso" aria-live="polite"></p></div>'
            '<noscript><p class="sub">Activa JavaScript para elegir otras ciudades. Abajo tienes la comparación de las cuatro más pobladas.</p></noscript>')
    sel_txt = "".join(f"<p>{esc(p)}</p>" for p in claves_sel(gw, defecto))
    comparador = (f'<section id="comparador"><h2>Elige de 2 a {MAX_CIUDADES} ciudades</h2>{form}'
                  f'<h3>Diferencias principales</h3><div id="cmp-claves" aria-live="polite">{sel_txt}</div>'
                  f'<h3>Datos lado a lado</h3><p class="sub">En negrita, el valor más alto de cada fila. «—» = dato no disponible. '
                  'Pulsa el nombre de una ciudad o de un distrito para ver su ficha.</p>'
                  f'<div class="cmp-wrap" id="cmp-tabla">{tabla(gw, defecto, R)}</div>'
                  '<p class="sub" style="margin-top:10px">* Pocos inmuebles en la muestra (entre 30 y 99): interpreta la cifra con cuidado. '
                  'Los distritos con menos de 30 no se tienen en cuenta.</p>'
                  f'<h3>Cómo ha cambiado el alquiler</h3><p class="sub">Alquiler mediano de un piso, en euros al mes, {gw.ANIO_INICIO_ALQUILER}-{gw.ANIO}.</p>'
                  '<ul class="cmp-leg" id="cmp-leg"></ul><div id="cmp-graf"><noscript><p class="sub">El gráfico necesita JavaScript. '
                  'La evolución de cada ciudad está también en su ficha.</p></noscript></div>'
                  f'{gw.aviso_turistico()}'
                  + js_bloque("cmp-datos", datos) + js_bloque("cmp-filas", R) + js_bloque("cmp-meta", meta) + "</section>")
    lead = (f"Elige de 2 a {MAX_CIUDADES} de las {N} ciudades españolas de más de {gw.MIN_POB} habitantes y compáralas lado a lado: "
            "alquiler, renta de los hogares, población y sus distritos más baratos y más caros. "
            f"Con datos oficiales del Ministerio de Vivienda (SERPAVI) y del INE de {gw.ANIO}.")
    A, A0 = gw.ANIO, gw.ANIO - AÑOS_CAMBIO
    met = ('<section id="metodologia"><h2>Cómo se ha calculado</h2><ul class="notes">'
           "<li><strong>Alquiler:</strong> mediana de los alquileres de vivienda habitual declarados en el IRPF (SERPAVI, Ministerio de Vivienda), "
           f"solo pisos, datos de {A}. Son contratos vigentes, no anuncios: por eso suele ser más bajo que lo que piden hoy los portales inmobiliarios. "
           "El rango de €/m² es el del 50 % central de los pisos (percentiles 25 y 75).</li>"
           f"<li><strong>Renta:</strong> renta neta media por hogar y por persona del Atlas de Distribución de Renta de los Hogares del INE ({A}).</li>"
           "<li><strong>Alquiler sobre la renta:</strong> alquiler mediano × 12 / renta neta media del hogar. Es una estimación propia y aproximada: "
           "compara la mediana de los inquilinos con la media de todos los hogares.</li>"
           f"<li><strong>Ingresos para el {PCT} %:</strong> alquiler mediano / 0,{PCT}. La regla del {PCT} % es orientativa, no un umbral oficial.</li>"
           f"<li><strong>Cambios:</strong> diferencia en % entre {A0} (o {A - 1}) y {A}, sin descontar la inflación. Si una ciudad no tiene dato fiable en alguno de los dos años, sale «—».</li>"
           "<li><strong>Población y hogares:</strong> INE (Atlas de Distribución de Renta de los Hogares, indicadores demográficos).</li>"
           "<li><strong>Distritos:</strong> divisiones del INE dentro de cada ciudad. Solo se usan los que tienen 30 inmuebles o más en la muestra "
           "(de 30 a 99, marcados con *). Los nombres y barrios de cada distrito vienen de la ficha de la ciudad, con su fuente.</li>"
           "<li><strong>Privacidad:</strong> la comparación se hace en tu navegador. No se envía ni se guarda nada; el enlace para compartir solo lleva las ciudades elegidas.</li>"
           "</ul></section>")
    cuerpo = (gw.cabecera(root, [("#comparador", "Comparador"), ("#claves", "Claves"), ("#metodologia", "Metodología")]) +
              f'<div class="hero"><div>{gw.migas_html(root, [("Inicio", "")], TITULO)}<h1>{esc(H1)}</h1>'
              f'<p class="lead">{lead}</p></div></div><main>{CSS_PAGINA}{comparador}'
              f'<section id="claves"><h2>Qué dicen los datos al comparar</h2>{"".join(f"<p>{p}</p>" for p in _claves_generales(gw, todas))}'
              f'<h3>Algunas comparaciones</h3><ul class="lnk">{_ejemplos(gw, todas)}</ul></section>{met}'
              f'<section><h2>Relacionado</h2><ul class="lnk"><li><a href="{root}{hs.SLUG}/">{esc(hs.TITULO)}</a></li>'
              f'<li><a href="{root}rankings/sueldo-para-vivir-de-alquiler/">Sueldo necesario para alquilar en cada ciudad</a></li>'
              f'<li><a href="{root}rankings/donde-mas-sube-el-alquiler/">Ciudades donde más ha subido el alquiler</a></li>'
              f'<li><a href="{root}comunidades/">Alquiler por comunidad autónoma</a></li></ul></section>{gw.pie(root)}</main>')
    titulo_a = f"Comparador de ciudades de España: alquiler y renta ({gw.ANIO})"
    desc = (f"Compara de 2 a {MAX_CIUDADES} ciudades españolas lado a lado: alquiler, renta, población y distritos más baratos. "
            f"Datos oficiales de {gw.ANIO}.")
    ld = [gw.dataset(f"{TITULO} ({gw.ANIO})", desc, f"{SLUG}/", "España",
                     ["Alquiler mensual mediano", "Renta neta media del hogar", "Población", "Alquiler mensual mediano por distrito"]),
          gw.migas([("Inicio", ""), (TITULO, f"{SLUG}/")])]
    return gw.head(titulo_a, desc, root, f"{SLUG}/", ld) + cuerpo + gw.fin(root, JS_PAGINA)


def generar(gw, todas):
    """Escribe web/<SLUG>/index.html y devuelve su URL para el sitemap."""
    gw.escribir(gw.WEB / SLUG / "index.html", pagina(gw, todas))
    return [f"{SLUG}/"]
