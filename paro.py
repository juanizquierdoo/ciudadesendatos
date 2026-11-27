"""Módulo de paro registrado (Fase 3, primer módulo de datos nuevos).

Fuente: Servicio Público de Empleo Estatal (SEPE), «Paro registrado por municipio», datos.gob.es
(ea0041513-paro-registrado-por-municipio). Licencia CC BY 4.0 (FUENTES.md, fuente 10).
Es el número de demandantes de empleo parados inscritos en las oficinas de empleo el último día
de cada mes. NO es la tasa de paro de la EPA: no hay tasa oficial por municipio.

Archivos que usa (datos_municipales/sepe_paro/, en git porque son pequeños):
- paro_octubre_2016_2026.csv: paro registrado total en el mismo mes de cada año (el último publicado),
  una fila por ciudad (código INE del municipio).
- paro_detalle_202610.csv: el último mes con el desglose por sexo y edad y por sector.
Son un extracto, sin cambiar ninguna cifra, de los CSV anuales del SEPE para las ciudades de la web.

Para actualizar (cuando el SEPE publique un mes nuevo):
1. Descargar de datos.gob.es los CSV anuales «Paro_por_municipios_<año>_csv.csv» (todos los años de la serie,
   o al menos el último) a datos_originales/sepe/.
2. python paro.py --extraer   (rehace los dos archivos de arriba con el último mes disponible)
3. python actualizar.py --desde 4

Lo usan:
- preparar_json.py: aportar(ciudades) añade c["paro"] a cada ciudad de ciudades_nivel1.json.
- generar_web.py: seccion(c, todas) escribe la sección #empleo de la ficha.
- comparador_ciudades.py: tres filas del grupo «Empleo».
Test: tests/test_paro.py.
"""
import csv
import html
import math
import sys
from pathlib import Path
from statistics import median

from config import ANIO

BASE = Path(__file__).parent
CARPETA = BASE / "datos_municipales" / "sepe_paro"
ORIGEN_SEPE = BASE / "datos_originales" / "sepe"
DESCARGA = "27/11/2026"   # fecha en que se descargaron los CSV del SEPE (cambiar al actualizar)

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
         "octubre", "noviembre", "diciembre"]
COL_DET = ["total", "hombre_menos25", "hombre_25_44", "hombre_45_mas", "mujer_menos25", "mujer_25_44", "mujer_45_mas",
           "agricultura", "industria", "construccion", "servicios", "sin_empleo_anterior"]
SECTORES = [("servicios", "Servicios"), ("industria", "Industria"), ("construccion", "Construcción"),
            ("agricultura", "Agricultura"), ("sin_empleo_anterior", "Sin empleo anterior")]


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


def num(v):
    """El SEPE pone «<5» cuando hay menos de 5 personas (secreto estadístico): eso no es un número, va a None."""
    v = (v or "").strip()
    return int(v) if v.isdigit() else None


def nombre_mes(codigo):
    """'202610' -> 'octubre de 2026'."""
    return f"{MESES[int(codigo[4:]) - 1]} de {codigo[:4]}"


# ------------------------------------------------------------------ extracción (desde los CSV completos del SEPE)
def _leer_sepe(ruta):
    """Filas de un CSV anual del SEPE: (mes 'AAAAMM', código INE de 5 cifras, [12 valores en texto])."""
    texto = ruta.read_bytes().decode("latin-1")
    for linea in texto.splitlines()[2:]:   # 1.ª línea: título; 2.ª: cabecera
        r = linea.split(";")
        if len(r) < 20 or not r[0].strip().isdigit():
            continue
        yield r[0].strip(), r[6].strip().zfill(5), [x.strip() for x in r[8:20]]


def extraer(codigos):
    """Rehace los dos extractos a partir de datos_originales/sepe/Paro_por_municipios_<año>_csv.csv."""
    archivos = sorted(ORIGEN_SEPE.glob("Paro_por_municipios_*_csv.csv"))
    if not archivos:
        sys.exit(f"No hay CSV del SEPE en {ORIGEN_SEPE}")
    por_anio = {}
    for a in archivos:
        anio = int(a.name.split("_")[3])
        por_anio[anio] = [f for f in _leer_sepe(a) if f[1] in codigos]
    ultimo = max(f[0] for f in por_anio[max(por_anio)])
    mes = ultimo[4:]
    anios = sorted(a for a in por_anio if any(f[0] == f"{a}{mes}" for f in por_anio[a]))
    serie = {c: {} for c in codigos}
    for a in anios:
        for m, c, v in por_anio[a]:
            if m == f"{a}{mes}":
                serie[c][a] = v[0]
    CARPETA.mkdir(parents=True, exist_ok=True)
    with open(CARPETA / f"paro_{MESES[int(mes) - 1]}_{anios[0]}_{anios[-1]}.csv", "w", encoding="utf-8", newline="") as f:
        f.write("cod;" + ";".join(map(str, anios)) + "\n")
        for c in sorted(codigos):
            f.write(c + ";" + ";".join(serie[c].get(a, "") for a in anios) + "\n")
    with open(CARPETA / f"paro_detalle_{ultimo}.csv", "w", encoding="utf-8", newline="") as f:
        f.write("cod;" + ";".join(COL_DET) + "\n")
        for m, c, v in por_anio[int(ultimo[:4])]:
            if m == ultimo:
                f.write(c + ";" + ";".join(v) + "\n")
    print(f"Extractos del SEPE rehechos: mes {nombre_mes(ultimo)}, serie {anios[0]}-{anios[-1]}. "
          "Borra a mano los extractos antiguos de datos_municipales/sepe_paro/ si cambia el mes.")


# ------------------------------------------------------------------ carga
def _archivo(patron):
    xs = sorted(CARPETA.glob(patron))
    if not xs:
        raise FileNotFoundError(f"Falta {patron} en {CARPETA}")
    return xs[-1]


def cargar():
    """{cod: {"mes": 'AAAAMM', "serie": {año: total}, "det": {columna: valor o None}}}."""
    det_f = _archivo("paro_detalle_*.csv")
    mes = det_f.stem.split("_")[-1]
    ser_f = _archivo(f"paro_{MESES[int(mes[4:]) - 1]}_*.csv")
    out = {}
    with open(ser_f, encoding="utf-8") as f:
        r = csv.reader(f, delimiter=";")
        cab = next(r)
        anios = [int(a) for a in cab[1:]]
        for fila in r:
            out[fila[0]] = {"mes": mes, "serie": {a: num(v) for a, v in zip(anios, fila[1:])}, "det": None}
    with open(det_f, encoding="utf-8") as f:
        r = csv.reader(f, delimiter=";")
        next(r)
        for fila in r:
            out.setdefault(fila[0], {"mes": mes, "serie": {}, "det": None})["det"] = dict(zip(COL_DET, map(num, fila[1:])))
    return out


def pob_18_64(c):
    """Habitantes de 18 a 64 años = población × (100 − % menores de 18 − % mayores de 65) / 100 (ADRH, INE)."""
    p, m18, m65 = c.get("poblacion"), c.get("pct_menor_18"), c.get("pct_65_mas")
    if not p or m18 is None or m65 is None:
        return None
    return p * (100 - m18 - m65) / 100


def aportar(ciudades):
    """Añade c["paro"] a cada ciudad (o None si el SEPE no tiene el municipio)."""
    datos = cargar()
    for c in ciudades:
        x = datos.get(c["cod_muni"])
        if not x or not x["det"] or x["det"]["total"] is None:
            c["paro"] = None
            continue
        mes = x["mes"]
        anio = int(mes[:4])
        total = x["det"]["total"]
        p = pob_18_64(c)
        c["paro"] = {
            "mes": mes, "mes_texto": nombre_mes(mes), "total": total,
            "anterior": x["serie"].get(anio - 1),
            "por_100": round(total / p * 100, 2) if p else None,
            "serie": [{"anio": a, "total": v} for a, v in sorted(x["serie"].items())],
            "detalle": x["det"],
        }
    return ciudades


# ------------------------------------------------------------------ cálculos para la web
def con_dato(todas):
    return [c for c in todas if c.get("paro") and c["paro"].get("por_100") is not None]


def mediana_por_100(todas):
    xs = [c["paro"]["por_100"] for c in con_dato(todas)]
    return median(xs) if xs else None


def puesto(c, todas):
    """Puesto por parados por cada 100 habitantes de 18 a 64 años (1 = el más alto) y total de ciudades."""
    xs = sorted(con_dato(todas), key=lambda x: (-x["paro"]["por_100"], x["nombre"]))
    for i, x in enumerate(xs, 1):
        if x["cod_muni"] == c["cod_muni"]:
            return i, len(xs)
    return None, len(xs)


def _ticks(mn, mx, k=4):
    raw = (mx - mn) / k or 1
    mag = 10 ** math.floor(math.log10(raw))
    paso = next(m * mag for m in (1, 2, 2.5, 5, 10) if raw <= m * mag)
    t, out = math.floor(mn / paso) * paso, []
    while t <= mx + paso * 0.999 and len(out) < 9:
        out.append(t)
        t += paso
    return out


def grafico(pts, etiqueta, mes):
    """Línea del paro registrado en el mismo mes de cada año (mismo estilo que el gráfico del alquiler)."""
    pts = [(a, v) for a, v in pts if v is not None]
    if len(pts) < 3:
        return ""
    W, H, L, R, T, B = 720, 300, 64, 22, 28, 38
    ys = [v for _, v in pts]
    tk = _ticks(max(0, min(ys) - (max(ys) - min(ys)) * .1), max(ys) + (max(ys) - min(ys)) * .1)
    mn, mx = tk[0], tk[-1]
    a0, a1 = pts[0][0], pts[-1][0]
    X = lambda a: L + (a - a0) / ((a1 - a0) or 1) * (W - L - R)
    Y = lambda v: H - B - (v - mn) / ((mx - mn) or 1) * (H - B - T)
    s = [f'<line class="gl" x1="{L}" x2="{W - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}"/>'
         f'<text x="{L - 8}" y="{Y(t) + 4:.1f}" text-anchor="end">{n(t)}</text>' for t in tk]
    p = " ".join(f"{X(a):.1f},{Y(v):.1f}" for a, v in pts)
    s.append(f'<polygon class="ar" points="{X(a0):.1f},{H - B} {p} {X(a1):.1f},{H - B}"/><polyline class="ln" points="{p}"/>')
    for i, (a, v) in enumerate(pts):
        s.append(f'<circle cx="{X(a):.1f}" cy="{Y(v):.1f}" r="5"><title>{mes} de {a}: {n(v)} personas</title></circle>')
        if i % 2 == 0 or i == len(pts) - 1:
            s.append(f'<text x="{X(a):.1f}" y="{H - 14}" text-anchor="middle">{a}</text>')
    s.append(f'<text x="{X(a0):.1f}" y="{Y(pts[0][1]) - 12:.1f}" text-anchor="start">{n(pts[0][1])}</text>'
             f'<text x="{X(a1):.1f}" y="{Y(pts[-1][1]) - 12:.1f}" text-anchor="end">{n(pts[-1][1])}</text>')
    return (f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(etiqueta)}">' + "".join(s) + "</svg>")


def frases(c, todas):
    """Texto propio de la sección, calculado solo con los datos. Lo usa también el test."""
    x = c["paro"]
    nombre, mes = c["nombre"], x["mes_texto"]
    mes_solo = mes.split(" de ")[0]
    anio = int(x["mes"][:4])
    t = [f"En {mes} había {n(x['total'])} personas inscritas como paradas en las oficinas de empleo de {esc(nombre)}."]
    ch = cambio(x["anterior"], x["total"])
    if ch is not None:
        if abs(ch) < 0.5:
            t.append(f"Es casi la misma cifra que un año antes ({n(x['anterior'])} en {mes_solo} de {anio - 1}).")
        else:
            t.append(f"Son {n(abs(x['total'] - x['anterior']))} {'más' if ch > 0 else 'menos'} que en {mes_solo} de {anio - 1} "
                     f"({signo(ch)}).")
    if x["por_100"] is not None:
        med = mediana_por_100(todas)
        pu, tot = puesto(c, todas)
        comp = ("por encima de" if x["por_100"] > med + 0.05 else "por debajo de" if x["por_100"] < med - 0.05 else "en")
        t.append(f"Equivale a {d(x['por_100'])} parados por cada 100 habitantes de 18 a 64 años, {comp} la mediana de las "
                 f"{tot} ciudades de la web ({d(med)}); {esc(nombre)} ocupa el puesto {pu} de {tot} (en el 1 es donde más pesa el paro).")
    serie = [s for s in x["serie"] if s["total"] is not None]
    if len(serie) >= 3:
        s0, s1 = serie[0], serie[-1]
        ch0 = cambio(s0["total"], s1["total"])
        t.append(f"Desde {mes_solo} de {s0['anio']} el paro registrado ha {'bajado' if ch0 < 0 else 'subido'} un "
                 f"{d(abs(ch0), 0)} % ({n(s0['total'])} personas entonces).")
        smax = max(serie, key=lambda s: (s["total"], s["anio"]))
        if smax["anio"] not in (s0["anio"], s1["anio"]):
            t.append(f"El valor más alto de la serie fue el de {mes_solo} de {smax['anio']}: {n(smax['total'])} personas.")
    det = x["detalle"]
    muj = [det[k] for k in ("mujer_menos25", "mujer_25_44", "mujer_45_mas")]
    m45 = [det["hombre_45_mas"], det["mujer_45_mas"]]
    if None not in muj:
        t.append(f"El {d(sum(muj) / x['total'] * 100, 0)} % son mujeres")
        if None not in m45:
            t[-1] += f" y el {d(sum(m45) / x['total'] * 100, 0)} % tiene 45 años o más."
        else:
            t[-1] += "."
    if det["servicios"] is not None:
        t.append(f"Por el sector de su último empleo, el {d(det['servicios'] / x['total'] * 100, 0)} % viene de los servicios"
                 + (f" y {n(det['sin_empleo_anterior'])} personas no habían trabajado antes." if det["sin_empleo_anterior"] is not None else "."))
    return t


def seccion(c, todas):
    """HTML de la sección #empleo de la ficha. Sin dato del SEPE: no hay sección (no se deja vacía)."""
    x = c.get("paro")
    if not x:
        return ""
    nombre, mes = c["nombre"], x["mes_texto"]
    mes_solo = mes.split(" de ")[0]
    det = x["detalle"]
    pu, tot = puesto(c, todas)
    ch = cambio(x["anterior"], x["total"])
    facts = ('<dl class="facts">'
             f'<div><dt>Paro registrado ({esc(mes)})</dt><dd>{n(x["total"])}<small>personas</small></dd></div>'
             + (f'<div><dt>Cambio en un año</dt><dd>{signo(ch)}<small>{n(x["anterior"])} en {esc(mes_solo)} de {int(x["mes"][:4]) - 1}</small></dd></div>'
                if ch is not None else "")
             + (f'<div><dt>Parados por cada 100 habitantes de 18 a 64 años</dt><dd class="big">{d(x["por_100"])}'
                f'<small>puesto {pu} de {tot} ciudades</small></dd></div>' if x["por_100"] is not None else "")
             + '</dl>')
    svg = grafico([(s["anio"], s["total"]) for s in x["serie"]], f"Paro registrado en {nombre} en {mes_solo} de cada año", mes_solo)
    filas, prev = [], None
    for s in x["serie"]:
        cb = cambio(prev, s["total"]) if prev is not None else None
        filas.append(f'<tr><th scope="row">{esc(mes_solo.capitalize())} de {s["anio"]}</th>'
                     f'<td>{n(s["total"]) if s["total"] is not None else "No disponible"}</td>'
                     f'<td>{signo(cb) if cb is not None else "—"}</td></tr>')
        prev = s["total"]
    v = lambda k: "menos de 5" if det[k] is None else n(det[k])
    sexo = ('<div class="wrap"><table class="evol"><thead><tr><th scope="col">Edad</th><th scope="col">Hombres</th>'
            '<th scope="col">Mujeres</th></tr></thead><tbody>'
            + "".join(f'<tr><th scope="row">{e}</th><td>{v("hombre_" + k)}</td><td>{v("mujer_" + k)}</td></tr>'
                      for e, k in (("Menos de 25 años", "menos25"), ("De 25 a 44 años", "25_44"), ("45 años o más", "45_mas")))
            + '</tbody></table></div>')
    sector = ('<div class="wrap"><table class="evol"><thead><tr><th scope="col">Sector del último empleo</th>'
              '<th scope="col">Personas</th><th scope="col">%</th></tr></thead><tbody>'
              + "".join(f'<tr><th scope="row">{et}</th><td>{v(k)}</td>'
                        f'<td>{d(det[k] / x["total"] * 100) + " %" if det[k] is not None else "—"}</td></tr>' for k, et in SECTORES)
              + '</tbody></table></div>')
    notas = ("Paro registrado: personas inscritas como demandantes de empleo paradas en las oficinas públicas de empleo el último día del mes. "
             "Fuente: Servicio Público de Empleo Estatal (SEPE), «Paro registrado por municipio», datos abiertos con licencia CC BY 4.0 "
             f"(datos de {mes}, descargados el {DESCARGA}). "
             "No es la tasa de paro de la Encuesta de Población Activa: el INE no publica una tasa de paro por municipio. "
             "Parados por cada 100 habitantes de 18 a 64 años: estimación propia que divide el paro registrado entre la población de 18 a 64 años "
             f"del Atlas de Distribución de Renta de los Hogares del INE ({ANIO}); "
             "sirve para comparar ciudades entre sí, no es una tasa oficial. "
             "La serie compara siempre el mismo mes de cada año para evitar el efecto de la temporada. "
             "«Menos de 5»: el SEPE no da la cifra exacta cuando hay menos de 5 personas.")
    return (f'<section id="empleo"><h2>Paro registrado en {esc(nombre)}</h2>{facts}'
            f'<p class="sub" style="margin-top:12px">{" ".join(frases(c, todas))}</p>'
            + (f'<h3 style="margin-top:24px">Evolución del paro en {esc(nombre)} ({esc(mes_solo)} de cada año)</h3>{svg}' if svg else "")
            + f'<div class="two"><div><h3>Por sexo y edad</h3>{sexo}</div><div><h3>Por sector</h3>{sector}</div></div>'
            f'<h3 style="margin-top:24px">El paro en {esc(nombre)}, año a año</h3>'
            '<div class="wrap"><table class="evol" style="white-space:nowrap"><thead><tr><th scope="col">Mes</th>'
            '<th scope="col">Personas en paro</th><th scope="col">Cambio en un año</th></tr></thead>'
            f'<tbody>{"".join(reversed(filas))}</tbody></table></div>'
            f'<p class="sub" style="margin-top:12px;font-size:14px">{esc(notas)}</p></section>')


if __name__ == "__main__":
    if "--extraer" in sys.argv:
        import json
        from config import JSON_NIVEL1
        cods = {c["cod_muni"] for c in json.loads(JSON_NIVEL1.read_text(encoding="utf-8"))["ciudades"]}
        extraer(cods)
    else:
        datos = cargar()
        print(f"Paro registrado (SEPE): {len(datos)} municipios en los extractos.")
