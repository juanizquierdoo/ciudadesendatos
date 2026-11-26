"""Rankings temáticos pensados para búsquedas reales (B-29).

Cada página responde a una pregunta concreta que la gente busca y que los 4
rankings generales no responden por sí solos:

    /rankings/donde-mas-sube-el-alquiler/       ciudades donde más ha subido el alquiler (últimos 5 años)
    /rankings/sueldo-para-vivir-de-alquiler/    ingresos necesarios para que el alquiler no pase del 30 %
    /rankings/barrios-con-mas-renta/            distritos con más y menos renta de España
    /rankings/barrios-con-el-alquiler-mas-caro/ distritos con el alquiler más caro y más barato de España
    /rankings/ciudades-mas-jovenes/             edad media y envejecimiento por ciudad

Cada página lleva su tabla ordenable, un texto propio calculado solo con los datos
de ciudades_nivel1.json (si falta un dato, la frase no se escribe), enlaces a las
fichas de ciudad, metodología, aviso de zonas turísticas y entrada en el sitemap.

generar_web.py solo hace dos cosas con este módulo: añade las tarjetas a la portada
(tarjetas()) y llama a generar() en main(). Las piezas comunes (cabecera, pie,
head, JSON-LD) se toman de generar_web, así que los cambios en el pie o en la
cabecera llegan también a estas páginas.
"""
import statistics

# Umbral orientativo para "alquiler asequible": que no pase del 30 % de los ingresos netos.
UMBRAL_ASEQUIBLE = 30
AÑOS_SUBIDA = 5          # la subida se mide entre ANIO - 5 y ANIO
MIN_DISTRITOS_BRECHA = 4  # para comparar el distrito más rico y el más pobre de una ciudad

# slug, título (sin año), descripción corta para las tarjetas
TEMAS = [
    ("donde-mas-sube-el-alquiler", "Ciudades donde más ha subido el alquiler",
     "Subida del alquiler mediano en los últimos cinco años y en el último año, comparada con la renta."),
    ("sueldo-para-vivir-de-alquiler", "Sueldo necesario para alquilar en cada ciudad",
     "Ingresos netos al mes para que el alquiler mediano no pase del 30 %."),
    ("barrios-con-mas-renta", "Barrios y distritos con más renta de España",
     "Renta neta media por hogar en los distritos de las ciudades de más de 50.000 habitantes."),
    ("barrios-con-el-alquiler-mas-caro", "Barrios y distritos con el alquiler más caro de España",
     "Alquiler mediano de un piso en cada distrito, del más caro al más barato."),
    ("ciudades-mas-jovenes", "Ciudades más jóvenes y más envejecidas de España",
     "Edad media, menores de 18 años y mayores de 65 en cada ciudad."),
]



def corto(x):
    """Nombre breve de un distrito para la meta description (máx. 160 caracteres): su primer barrio si lo tiene."""
    if " · " in x["nombre"] and x.get("barrios"):
        return x["barrios"][0]
    return x["nombre"]

def tarjetas(root):
    """Tarjetas para la portada (mismo formato que las de los rankings generales)."""
    return "".join(f'<a class="card" href="{root}rankings/{s}/"><strong>{_esc(t)}</strong><span>{_esc(df)}</span></a>'
                   for s, t, df in TEMAS)


def _esc(s):
    import html
    return html.escape(str(s).replace("'", "’"), quote=True)


# ------------------------------------------------------------------ utilidades
def serie(c, anio, clave="alquiler_mes"):
    for s in c.get("serie_alquiler", []):
        if s["anio"] == anio and s.get(clave) is not None:
            return s[clave]
    return None


def renta_en(c, anio):
    for s in c.get("serie_renta", []):
        if s["anio"] == anio and s.get("renta_hogar"):
            return s["renta_hogar"]
    return None


def dv(v, k=2):
    """Valor para el atributo data-v (ordenación): vacío si no hay dato."""
    return "" if v is None else f"{v:.{k}f}"


def var(a, b):
    return None if a in (None, 0) or b is None else (b / a - 1) * 100


def y_lista(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


def distritos(todas):
    """Todos los distritos con su ciudad. 'ver_alquiler' sigue la misma regla que la ficha (30 inmuebles o más)."""
    out = []
    for c in todas:
        for x in c.get("distritos") or []:
            ver = x["fiabilidad"] in ("ok", "pocos_datos") and x.get("alquiler_mes") is not None
            out.append({**x, "ciudad": c, "ver_alquiler": ver, "pocos": x["fiabilidad"] == "pocos_datos"})
    return out


# ------------------------------------------------------------------ piezas HTML
def _pagina(gw, slug, titulo, desc, lead, claves, aviso, tabla, metodologia, variables, todas_rutas):
    root = "../../"
    titulo_a = f"{titulo} ({gw.ANIO})"
    otros = "".join(f'<li><a href="{root}rankings/{s}/">{gw.esc(t)}</a></li>' for s, t in todas_rutas if s != slug)
    cuerpo = (gw.cabecera(root, [("#claves", "Claves"), ("#tabla", "Tabla")]) +
              f'<div class="hero"><div>{gw.migas_html(root, [("Inicio", "")], titulo)}<h1>{gw.esc(titulo_a)}</h1>'
              f'<p class="lead">{lead}</p>{aviso}</div></div><main>'
              f'<section id="claves"><h2>Qué dicen los datos</h2>{"".join(f"<p>{p}</p>" for p in claves)}</section>'
              f'<section id="tabla">{tabla}</section>{metodologia}'
              f'<section><h2>Más rankings</h2><ul class="lnk">{otros}</ul></section>{gw.pie(root)}</main>')
    ruta = f"rankings/{slug}/"
    ld = [gw.dataset(titulo_a, desc, ruta, "España", variables), gw.migas([("Inicio", ""), (titulo, ruta)])]
    return gw.head(titulo_a, desc, root, ruta, ld) + cuerpo + gw.fin(root)


def _enl_ciudad(gw, c, root="../../", ancla=""):
    return f'<a href="{root}{c["slug"]}/{ancla}">{gw.esc(c["nombre"])}</a>'


def _metodologia(gw, items):
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f'<section id="metodologia"><h2>Cómo se ha calculado</h2><ul class="notes">{lis}</ul></section>'


NOTA_ALQUILER = ("<strong>Alquiler:</strong> mediana de los alquileres de vivienda habitual declarados en el IRPF (SERPAVI), solo pisos. "
                 "Son contratos vigentes, no anuncios: por eso suele ser más bajo que lo que piden los portales inmobiliarios.")
NOTA_RENTA = ("<strong>Renta:</strong> renta neta media por hogar del Atlas de Distribución de Renta de los Hogares del INE "
              "(todos los hogares, también los que no alquilan).")


# ------------------------------------------------------------------ 1. dónde más sube el alquiler
def pagina_subida(gw, todas, rutas):
    A, A0, A1 = gw.ANIO, gw.ANIO - AÑOS_SUBIDA, gw.ANIO - 1
    filas_d = []
    sin = []
    for c in todas:
        v0, v1, v = serie(c, A0), serie(c, A1), serie(c, A)
        ch = var(v0, v)
        if ch is None:
            sin.append(c["nombre"])
            continue
        filas_d.append({"c": c, "v0": v0, "v": v, "ch": ch, "ch1": var(v1, v), "chr": var(renta_en(c, A0), renta_en(c, A))})
    filas_d.sort(key=lambda r: (-r["ch"], r["c"]["nombre"]))
    N = len(filas_d)
    med = statistics.median(r["ch"] for r in filas_d)
    f = lambda r: f'{gw.esc(r["c"]["nombre"])} ({gw.pc_signo(r["ch"])})'
    top, bot = filas_d[:5], filas_d[-5:][::-1]
    suben = N - sum(1 for r in filas_d if r["ch"] <= 0)
    cuantas = f"las {N} ciudades" if suben == N else f"{suben} de las {N} ciudades"
    claves = [f"Entre {A0} y {A} el alquiler mediano de un piso ha subido en {cuantas} "
              f"con datos de los dos años. La subida típica (la mediana) es del {gw.d(med)} %: en la mitad de las ciudades subió más y en la otra mitad, menos.",
              f"Donde más ha subido: {y_lista(f(r) for r in top)}.",
              f"Donde menos: {y_lista(f(r) for r in bot)}."]
    mas30 = sum(1 for r in filas_d if r["ch"] >= 30)
    if mas30:
        claves.append(f"En {mas30} ciudades el alquiler mediano es al menos un 30 % más alto que en {A0}.")
    con_r = [r for r in filas_d if r["chr"] is not None]
    if con_r:
        rapido = sum(1 for r in con_r if r["ch"] > r["chr"])
        med_r = statistics.median(r["chr"] for r in con_r)
        claves.append(f"La renta media de los hogares subió en el mismo periodo un {gw.d(med_r)} % en la ciudad típica. "
                      f"En {rapido} de {len(con_r)} ciudades el alquiler ha crecido más deprisa que la renta, "
                      f"y en {len(con_r) - rapido} ha ocurrido lo contrario.")
    ult = sorted([r for r in filas_d if r["ch1"] is not None], key=lambda r: (-r["ch1"], r["c"]["nombre"]))
    if ult:
        claves.append(f"Solo en el último año ({A1}-{A}), la subida típica fue del {gw.d(statistics.median(r['ch1'] for r in ult))} %. "
                      f"La mayor, en {gw.esc(ult[0]['c']['nombre'])} ({gw.pc_signo(ult[0]['ch1'])}), "
                      f"y la menor, en {gw.esc(ult[-1]['c']['nombre'])} ({gw.pc_signo(ult[-1]['ch1'])}).")
    if sin:
        claves.append(f"No aparecen {len(sin)} ciudades sin dato de alquiler fiable en {A0}: {gw.esc(y_lista(sorted(sin)))}.")

    filas = "".join(
        f'<tr id="c-{r["c"]["slug"]}"><td data-v="{i}">{i}</td><th scope="row" data-v="{gw.esc(r["c"]["nombre"])}">{_enl_ciudad(gw, r["c"], ancla="#evolucion")}</th>'
        f'<td data-v="{gw.esc(r["c"]["provincia"])}">{gw.esc(r["c"]["provincia"])}</td>'
        f'<td data-v="{r["v0"]:.2f}">{gw.n(r["v0"])} €</td><td data-v="{r["v"]:.2f}">{gw.n(r["v"])} €</td>'
        f'<td data-v="{r["ch"]:.3f}">{gw.pc_signo(r["ch"])}</td>'
        f'<td data-v="{dv(r["ch1"], 3)}">{gw.pc_signo(r["ch1"])}</td>'
        f'<td data-v="{dv(r["chr"], 3)}">{gw.pc_signo(r["chr"])}</td></tr>'
        for i, r in enumerate(filas_d, 1))
    th = gw.th_orden
    tabla = (f'<h2>Subida del alquiler por ciudad</h2><p class="sub">Alquiler mensual mediano de un piso. Pulsa una columna para ordenar.</p>'
             f'<div class="wrap"><table class="sortable numbered"><thead><tr><th>#</th>{th(1, "Ciudad", "text")}{th(2, "Provincia", "text")}'
             f'{th(3, f"Alquiler {A0}")}{th(4, f"Alquiler {A}")}{th(5, f"Cambio {A0}-{A}")}{th(6, f"Cambio {A1}-{A}")}'
             f'{th(7, f"Renta del hogar {A0}-{A}")}</tr></thead><tbody>{filas}</tbody></table></div>')
    lead = (f"Cuánto ha cambiado el alquiler mediano de un piso entre {A0} y {A} en las {N} ciudades españolas de más de {gw.MIN_POB} habitantes "
            f"con datos de ambos años, y si ha subido más o menos que la renta de los hogares.")
    desc = f"Ranking de las ciudades donde más ha subido el alquiler entre {A0} y {A}: subida típica del {gw.d(med)} %. Datos oficiales del SERPAVI y del INE."
    met = _metodologia(gw, [NOTA_ALQUILER,
                            f"<strong>Cambio:</strong> diferencia en % entre el alquiler mediano mensual de {A0} (o {A1}) y el de {A}. "
                            "Como incluye contratos firmados años atrás, puede subir más despacio que el precio de los pisos que salen ahora al mercado.",
                            f"<strong>Renta del hogar {A0}-{A}:</strong> cambio en % de la renta neta media por hogar del INE en los mismos años, sin descontar la inflación.",
                            "<strong>Ciudades:</strong> solo las que tienen alquiler fiable (100 inmuebles o más) en los dos años comparados."])
    return _pagina(gw, "donde-mas-sube-el-alquiler", "Ciudades donde más ha subido el alquiler", desc, lead, claves,
                   gw.aviso_turistico(), tabla, met, ["Cambio del alquiler mensual mediano", "Cambio de la renta neta media del hogar"], rutas)


# ------------------------------------------------------------------ 2. sueldo necesario
def pagina_sueldo(gw, todas, rutas):
    u = UMBRAL_ASEQUIBLE / 100
    orden = sorted(todas, key=lambda c: (c["alquiler_mes"], c["nombre"]))
    nec = lambda c: c["alquiler_mes"] / u
    N = len(orden)
    f = lambda c: f'{gw.esc(c["nombre"])} ({gw.n(nec(c))} €)'
    pasan = [c for c in orden if c["alquiler_pct_renta"] > UMBRAL_ASEQUIBLE]
    med = statistics.median(nec(c) for c in orden)
    claves = [f"Para que el alquiler mediano de un piso no se lleve más del {UMBRAL_ASEQUIBLE} % de lo que entra en casa, "
              f"en la ciudad típica de las {N} hacen falta unos {gw.n(med)} € netos al mes.",
              f"Donde menos ingresos hacen falta: {y_lista(f(c) for c in orden[:5])}.",
              f"Donde más: {y_lista(f(c) for c in orden[:-6:-1])}."]
    if pasan:
        claves.append(f"En {len(pasan)} ciudades ni siquiera la renta media de los hogares llega: el alquiler mediano supera el {UMBRAL_ASEQUIBLE} % "
                      f"de esa renta. Son {gw.esc(y_lista(c['nombre'] for c in sorted(pasan, key=lambda c: -c['alquiler_pct_renta'])))}.")
    else:
        claves.append(f"En ninguna de las {N} ciudades el alquiler mediano supera el {UMBRAL_ASEQUIBLE} % de la renta media de los hogares. "
                      "Pero la renta media incluye a los hogares con más ingresos y a los que tienen dos sueldos: para un hogar con un solo sueldo, "
                      "la cuenta puede ser muy distinta.")
    holgadas = sorted(todas, key=lambda c: (c["alquiler_pct_renta"], c["nombre"]))[:5]
    claves.append("Donde el alquiler mediano pesa menos sobre la renta media de los hogares: "
                  f"{y_lista(gw.esc(c['nombre']) + ' (' + gw.pc(c['alquiler_pct_renta']) + ')' for c in holgadas)}.")
    filas = "".join(
        f'<tr id="c-{c["slug"]}"><td data-v="{i}">{i}</td><th scope="row" data-v="{gw.esc(c["nombre"])}">{_enl_ciudad(gw, c)}</th>'
        f'<td data-v="{gw.esc(c["provincia"])}">{gw.esc(c["provincia"])}</td>'
        f'<td data-v="{c["alquiler_mes"]:.2f}">{gw.n(c["alquiler_mes"])} €</td>'
        f'<td data-v="{nec(c):.2f}">{gw.n(nec(c))} €</td>'
        f'<td data-v="{c["renta_hogar"] / 12:.2f}">{gw.n(c["renta_hogar"] / 12)} €</td>'
        f'<td data-v="{c["alquiler_pct_renta"]}">{gw.pc(c["alquiler_pct_renta"])}</td></tr>'
        for i, c in enumerate(orden, 1))
    th = gw.th_orden
    tabla = (f'<h2>Ingresos necesarios por ciudad</h2><p class="sub">De la ciudad donde menos hace falta a la que más. Pulsa una columna para ordenar.</p>'
             f'<div class="wrap"><table class="sortable numbered"><thead><tr><th>#</th>{th(1, "Ciudad", "text")}{th(2, "Provincia", "text")}'
             f'{th(3, "Alquiler al mes")}{th(4, f"Ingresos netos al mes para el {UMBRAL_ASEQUIBLE} %")}{th(5, "Renta media del hogar al mes")}'
             f'{th(6, "Alquiler sobre renta")}</tr></thead><tbody>{filas}</tbody></table></div>')
    lead = (f"Cuánto hay que ingresar al mes, en neto, para pagar el alquiler mediano de un piso sin dedicarle más del {UMBRAL_ASEQUIBLE} % "
            f"de los ingresos, en {N} ciudades de España. Y cómo se compara con la renta media de los hogares de cada ciudad.")
    desc = (f"Ingresos netos al mes para que el alquiler no pase del {UMBRAL_ASEQUIBLE} % en {N} ciudades: "
            f"desde {gw.n(nec(orden[0]))} € en {orden[0]['nombre']} hasta {gw.n(nec(orden[-1]))} € en {orden[-1]['nombre']}.")
    met = _metodologia(gw, [NOTA_ALQUILER, NOTA_RENTA,
                            f"<strong>Ingresos necesarios:</strong> alquiler mediano mensual ÷ {gw.d(u, 2)}. Es un cálculo propio con la regla orientativa "
                            f"de no dedicar al alquiler más del {UMBRAL_ASEQUIBLE} % de los ingresos netos. No es un umbral oficial ni tiene en cuenta "
                            "gastos de comunidad, suministros ni fianza.",
                            "<strong>Renta media del hogar al mes:</strong> renta neta media anual por hogar ÷ 12. Es la renta del hogar entero "
                            "(puede haber más de un sueldo), no el salario de una persona.",
                            "<strong>Alquiler sobre renta:</strong> alquiler mediano × 12 ÷ renta neta media del hogar. Estimación propia y aproximada."])
    return _pagina(gw, "sueldo-para-vivir-de-alquiler", "Sueldo necesario para alquilar en cada ciudad", desc, lead, claves,
                   gw.aviso_turistico(), tabla, met, ["Ingresos netos necesarios para el alquiler mediano", "Renta neta media del hogar"], rutas)


# ------------------------------------------------------------------ 3. distritos con más renta
def _nombre_d(gw, x):
    return gw.esc(x["nombre"])


def _brechas(todas):
    out = []
    for c in todas:
        ds = [x for x in c.get("distritos") or [] if x.get("renta_hogar")]
        if len(ds) >= MIN_DISTRITOS_BRECHA:
            hi = max(ds, key=lambda x: x["renta_hogar"])
            lo = min(ds, key=lambda x: x["renta_hogar"])
            out.append((hi["renta_hogar"] / lo["renta_hogar"], c, hi, lo))
    return sorted(out, key=lambda t: (-t[0], t[1]["nombre"]))


def pagina_renta_distritos(gw, todas, rutas):
    ds = sorted([x for x in distritos(todas) if x.get("renta_hogar")], key=lambda x: (-x["renta_hogar"], x["ciudad"]["nombre"], x["numero"]))
    N, NC = len(ds), len({x["ciudad"]["slug"] for x in ds})
    lab = lambda x: f'{_nombre_d(gw, x)} ({gw.esc(x["ciudad"]["nombre"])}, {gw.n(x["renta_hogar"])} €)'
    claves = [f"El distrito con más renta de las {NC} ciudades con desglose es {lab(ds[0])}. "
              f"Le siguen {y_lista(lab(x) for x in ds[1:5])}.",
              f"En el otro extremo están {y_lista(lab(x) for x in ds[:-6:-1])}. "
              f"Entre el primero y el último, la renta media por hogar se multiplica por {gw.d(ds[0]['renta_hogar'] / ds[-1]['renta_hogar'])}."]
    top20 = {}
    for x in ds[:20]:
        top20[x["ciudad"]["nombre"]] = top20.get(x["ciudad"]["nombre"], 0) + 1
    reparto = sorted(top20.items(), key=lambda t: (-t[1], t[0]))
    claves.append("Los 20 distritos con más renta están en " +
                  y_lista(f"{gw.esc(k)} ({v})" for k, v in reparto) + ".")
    med = statistics.median(x["renta_hogar"] for x in ds)
    claves.append(f"La renta típica de un distrito (la mediana de los {N}) es de {gw.n(med)} € por hogar y año; "
                  f"{sum(1 for x in ds if x['renta_hogar'] >= 2 * med)} distritos la duplican.")
    br = _brechas(todas)
    if br:
        claves.append(f"Dentro de una misma ciudad, la mayor distancia entre el distrito más rico y el más pobre está en " +
                      y_lista(f"{gw.esc(c['nombre'])} (×{gw.d(r)})" for r, c, hi, lo in br[:5]) +
                      f". Solo se comparan ciudades con {MIN_DISTRITOS_BRECHA} distritos o más.")
    filas = "".join(
        f'<tr><td data-v="{i}">{i}</td><th scope="row" data-v="{gw.esc(x["nombre"])}">{_nombre_d(gw, x)}</th>'
        f'<td data-v="{gw.esc(x["ciudad"]["nombre"])}">{_enl_ciudad(gw, x["ciudad"], ancla="#distritos")}</td>'
        f'<td data-v="{x["renta_hogar"]:.0f}">{gw.n(x["renta_hogar"])} €</td>'
        f'<td data-v="{dv(x.get("renta_persona"), 0)}">{gw.n(x.get("renta_persona"))}{" €" if x.get("renta_persona") else ""}</td>'
        + _celdas_alquiler(gw, x, ("alquiler_mes", "alquiler_pct_renta")) + '</tr>'
        for i, x in enumerate(ds, 1))
    th = gw.th_orden
    tabla = (f'<h2>Renta por distrito</h2><p class="sub">Los {N} distritos censales de las {NC} ciudades con desglose, del de más renta al de menos. '
             f'Pulsa una columna para ordenar.</p>'
             f'<div class="wrap"><table class="sortable numbered"><thead><tr><th>#</th>{th(1, "Distrito", "text")}{th(2, "Ciudad", "text")}'
             f'{th(3, "Renta del hogar")}{th(4, "Renta por persona")}{th(5, "Alquiler al mes")}{th(6, "Alquiler sobre renta")}</tr></thead>'
             f'<tbody>{filas}</tbody></table></div>{_notas_distritos(ds)}')
    lead = (f"Renta neta media por hogar en los {N} distritos de las {NC} ciudades españolas de más de {gw.MIN_POB} habitantes "
            f"que tienen desglose por distrito: dónde están las zonas con más y con menos ingresos.")
    desc = (f"Los distritos con más renta de España en {gw.ANIO}: {corto(ds[0])} ({ds[0]['ciudad']['nombre']}) encabeza la lista de {N}. "
            "Datos oficiales del INE.")
    met = _metodologia(gw, [NOTA_RENTA, NOTA_ALQUILER,
                            "<strong>Distritos:</strong> son los distritos censales del INE, que en algunas ciudades coinciden con los distritos municipales "
                            "y en otras no. Donde no hay nombre oficial verificado se identifican por sus barrios, "
                            "sus núcleos de población o sus calles principales; en la ficha de cada ciudad hay más detalle.",
                            "<strong>Alquiler del distrito:</strong> no se muestra si hay menos de 30 inmuebles en la muestra (—); "
                            "con 30 a 99 inmuebles se marca con *."])
    return _pagina(gw, "barrios-con-mas-renta", "Barrios y distritos con más renta de España", desc, lead, claves,
                   gw.aviso_turistico(), tabla, met, ["Renta neta media del hogar por distrito", "Renta neta media por persona"], rutas)


def _celdas_alquiler(gw, x, claves):
    out = []
    for k in claves:
        v = x.get(k) if x["ver_alquiler"] else None
        ast = "*" if (v is not None and x["pocos"]) else ""
        if k == "alquiler_mes":
            txt = "—" if v is None else f"{gw.n(v)} €{ast}"
        elif k == "eur_m2":
            txt = "—" if v is None else gw.d(v, 2) + ast
        elif k == "superficie_m2":
            v = x.get(k)
            txt = "—" if v is None else f"{gw.n(v)} m²"
        else:
            txt = "—" if v is None else gw.pc(v) + ast
        out.append(f'<td data-v="{dv(v)}">{txt}</td>')
    return "".join(out)


def _notas_distritos(ds):
    notas = []
    if any(x["pocos"] and x["ver_alquiler"] for x in ds):
        notas.append("* Pocos inmuebles en la muestra (entre 30 y 99): interpreta la cifra con cuidado.")
    if any(not x["ver_alquiler"] for x in ds):
        notas.append("— Menos de 30 inmuebles en alquiler: no se muestra el alquiler para no dar un dato poco fiable.")
    return "".join(f'<p class="sub" style="margin-top:8px">{t}</p>' for t in notas)


# ------------------------------------------------------------------ 4. distritos con el alquiler más caro
def pagina_alquiler_distritos(gw, todas, rutas):
    ds = sorted([x for x in distritos(todas) if x["ver_alquiler"]], key=lambda x: (-x["alquiler_mes"], x["ciudad"]["nombre"], x["numero"]))
    N, NC = len(ds), len({x["ciudad"]["slug"] for x in ds})
    lab = lambda x: f'{_nombre_d(gw, x)} ({gw.esc(x["ciudad"]["nombre"])}, {gw.n(x["alquiler_mes"])} €)'
    claves = [f"El distrito con el alquiler mediano más caro es {lab(ds[0])}. Le siguen {y_lista(lab(x) for x in ds[1:5])}.",
              f"Los más baratos son {y_lista(lab(x) for x in ds[:-6:-1])}."]
    top20 = {}
    for x in ds[:20]:
        top20[x["ciudad"]["nombre"]] = top20.get(x["ciudad"]["nombre"], 0) + 1
    claves.append("Los 20 distritos más caros están en " +
                  y_lista(f"{gw.esc(k)} ({v})" for k, v in sorted(top20.items(), key=lambda t: (-t[1], t[0]))) + ".")
    mil = sum(1 for x in ds if x["alquiler_mes"] >= 1000)
    med = statistics.median(x["alquiler_mes"] for x in ds)
    claves.append(f"En {mil} de los {N} distritos con dato fiable el alquiler mediano llega a 1.000 € al mes o más. "
                  f"En el distrito típico (la mediana) es de {gw.n(med)} €.")
    m2 = sorted([x for x in ds if x.get("eur_m2")], key=lambda x: (-x["eur_m2"], x["ciudad"]["nombre"], x["numero"]))
    if m2:
        claves.append(f"Por metro cuadrado, el más caro es {_nombre_d(gw, m2[0])} ({gw.esc(m2[0]['ciudad']['nombre'])}, {gw.d(m2[0]['eur_m2'], 2)} €/m²) "
                      f"y el más barato, {_nombre_d(gw, m2[-1])} ({gw.esc(m2[-1]['ciudad']['nombre'])}, {gw.d(m2[-1]['eur_m2'], 2)} €/m²). "
                      "El precio por m² permite comparar mejor zonas con pisos de distinto tamaño.")
    ocultos = sum(1 for x in distritos(todas) if not x["ver_alquiler"])
    if ocultos:
        claves.append(f"Quedan fuera {ocultos} distritos con menos de 30 pisos alquilados en la muestra.")
    filas = "".join(
        f'<tr><td data-v="{i}">{i}</td><th scope="row" data-v="{gw.esc(x["nombre"])}">{_nombre_d(gw, x)}</th>'
        f'<td data-v="{gw.esc(x["ciudad"]["nombre"])}">{_enl_ciudad(gw, x["ciudad"], ancla="#distritos")}</td>'
        + _celdas_alquiler(gw, x, ("alquiler_mes", "eur_m2", "superficie_m2")) +
        f'<td data-v="{dv(x.get("renta_hogar"), 0)}">{gw.n(x.get("renta_hogar"))}{" €" if x.get("renta_hogar") else ""}</td>'
        + _celdas_alquiler(gw, x, ("alquiler_pct_renta",)) + '</tr>'
        for i, x in enumerate(ds, 1))
    th = gw.th_orden
    tabla = (f'<h2>Alquiler por distrito</h2><p class="sub">Los {N} distritos con dato fiable de {NC} ciudades, del más caro al más barato. '
             f'Pulsa una columna para ordenar.</p>'
             f'<div class="wrap"><table class="sortable numbered"><thead><tr><th>#</th>{th(1, "Distrito", "text")}{th(2, "Ciudad", "text")}'
             f'{th(3, "Alquiler al mes")}{th(4, "€/m²")}{th(5, "Superficie mediana")}{th(6, "Renta del hogar")}{th(7, "Alquiler sobre renta")}</tr></thead>'
             f'<tbody>{filas}</tbody></table></div>{_notas_distritos(ds)}')
    lead = (f"Alquiler mediano de un piso en los {N} distritos con dato fiable de {NC} ciudades españolas de más de {gw.MIN_POB} habitantes: "
            "las zonas más caras y las más baratas para alquilar.")
    desc = (f"Barrios con el alquiler más caro de España en {gw.ANIO}: {corto(ds[0])} ({ds[0]['ciudad']['nombre']}), {gw.n(ds[0]['alquiler_mes'])} € al mes. "
            f"{N} distritos con datos oficiales.")
    met = _metodologia(gw, [NOTA_ALQUILER, NOTA_RENTA,
                            "<strong>Distritos:</strong> distritos censales del INE. Donde no hay nombre oficial verificado se identifican por sus "
                            "barrios, sus núcleos de población o sus calles principales; en la ficha de cada ciudad hay más detalle.",
                            "<strong>Fiabilidad:</strong> solo se incluyen distritos con 30 inmuebles o más en la muestra; con 30 a 99 se marcan con *."])
    return _pagina(gw, "barrios-con-el-alquiler-mas-caro", "Barrios y distritos con el alquiler más caro de España", desc, lead, claves,
                   gw.aviso_turistico(), tabla, met, ["Alquiler mensual mediano por distrito", "Alquiler mediano por m² por distrito"], rutas)


# ------------------------------------------------------------------ 5. ciudades más jóvenes
def pagina_edad(gw, todas, rutas):
    cs = sorted([c for c in todas if c.get("edad_media") is not None], key=lambda c: (c["edad_media"], c["nombre"]))
    N = len(cs)
    f = lambda c: f'{gw.esc(c["nombre"])} ({gw.d(c["edad_media"])} años)'
    claves = [f"Las ciudades con la población más joven son {y_lista(f(c) for c in cs[:5])}.",
              f"Las más envejecidas, {y_lista(f(c) for c in cs[:-6:-1])}.",
              f"La edad media típica (la mediana de las {N} ciudades) es de {gw.d(statistics.median(c['edad_media'] for c in cs))} años."]
    con = [c for c in cs if c.get("pct_65_mas") is not None and c.get("pct_menor_18") is not None]
    if con:
        mas_mayores = [c for c in con if c["pct_65_mas"] > c["pct_menor_18"]]
        claves.append(f"En {len(mas_mayores)} de {len(con)} ciudades ya hay más personas de 65 años o más que menores de 18.")
        m65 = max(con, key=lambda c: (c["pct_65_mas"], c["nombre"]))
        m18 = max(con, key=lambda c: (c["pct_menor_18"], c["nombre"]))
        claves.append(f"El porcentaje más alto de mayores de 65 está en {gw.esc(m65['nombre'])} ({gw.pc(m65['pct_65_mas'])}) "
                      f"y el de menores de 18, en {gw.esc(m18['nombre'])} ({gw.pc(m18['pct_menor_18'])}).")
    jov, vie = cs[:15], cs[-15:]
    claves.append(f"Las 15 ciudades más jóvenes tienen un alquiler mediano típico de {gw.n(statistics.median(c['alquiler_mes'] for c in jov))} € al mes "
                  f"y las 15 más envejecidas, de {gw.n(statistics.median(c['alquiler_mes'] for c in vie))} €. "
                  "Es una comparación descriptiva: no indica que una cosa cause la otra.")
    filas = "".join(
        f'<tr id="c-{c["slug"]}"><td data-v="{i}">{i}</td><th scope="row" data-v="{gw.esc(c["nombre"])}">{_enl_ciudad(gw, c)}</th>'
        f'<td data-v="{gw.esc(c["provincia"])}">{gw.esc(c["provincia"])}</td>'
        f'<td data-v="{c["edad_media"]}">{gw.d(c["edad_media"])}</td>'
        f'<td data-v="{dv(c.get("pct_menor_18"), 1)}">{gw.pc(c.get("pct_menor_18"))}</td>'
        f'<td data-v="{dv(c.get("pct_65_mas"), 1)}">{gw.pc(c.get("pct_65_mas"))}</td>'
        f'<td data-v="{dv(c.get("tam_hogar"), 1)}">{gw.d(c.get("tam_hogar"))}</td>'
        f'<td data-v="{c["alquiler_mes"]:.2f}">{gw.n(c["alquiler_mes"])} €</td>'
        f'<td data-v="{c["renta_hogar"]:.0f}">{gw.n(c["renta_hogar"])} €</td></tr>'
        for i, c in enumerate(cs, 1))
    th = gw.th_orden
    tabla = (f'<h2>Edad de la población por ciudad</h2><p class="sub">De la ciudad más joven a la más envejecida. Pulsa una columna para ordenar.</p>'
             f'<div class="wrap"><table class="sortable numbered"><thead><tr><th>#</th>{th(1, "Ciudad", "text")}{th(2, "Provincia", "text")}'
             f'{th(3, "Edad media")}{th(4, "Menores de 18")}{th(5, "65 años o más")}{th(6, "Personas por hogar")}'
             f'{th(7, "Alquiler al mes")}{th(8, "Renta del hogar")}</tr></thead><tbody>{filas}</tbody></table></div>')
    lead = (f"Edad media de la población, porcentaje de menores de 18 años y de mayores de 65 en {N} ciudades españolas de más de "
            f"{gw.MIN_POB} habitantes, junto a su alquiler y su renta.")
    desc = (f"Ciudades más jóvenes de España: {cs[0]['nombre']} tiene la edad media más baja ({gw.d(cs[0]['edad_media'])} años) "
            f"y {cs[-1]['nombre']} la más alta. Datos del INE.")
    met = _metodologia(gw, ["<strong>Edad y hogares:</strong> indicadores demográficos del Atlas de Distribución de Renta de los Hogares del INE "
                            f"({gw.ANIO}): edad media, % de menores de 18 años, % de 65 años o más y tamaño medio del hogar.",
                            NOTA_ALQUILER, NOTA_RENTA])
    return _pagina(gw, "ciudades-mas-jovenes", "Ciudades más jóvenes y más envejecidas de España", desc, lead, claves,
                   gw.aviso_turistico(), tabla, met, ["Edad media", "Población menor de 18 años", "Población de 65 años o más"], rutas)


# ------------------------------------------------------------------ principal
PAGINAS = {
    "donde-mas-sube-el-alquiler": pagina_subida,
    "sueldo-para-vivir-de-alquiler": pagina_sueldo,
    "barrios-con-mas-renta": pagina_renta_distritos,
    "barrios-con-el-alquiler-mas-caro": pagina_alquiler_distritos,
    "ciudades-mas-jovenes": pagina_edad,
}


def generar(gw, todas):
    """Escribe las páginas en web/rankings/<slug>/ y devuelve sus rutas para el sitemap.

    gw es el módulo generar_web ya en marcha (con FECHA_GEN, etc. rellenos)."""
    import alquiler_barato   # su ranking por comunidad sale también en "Más rankings"
    rutas = [(s, t) for s, _, t, _ in gw.RANKINGS] + [(s, t) for s, t, _ in TEMAS] + [(alquiler_barato.SLUG_CCAA, alquiler_barato.TITULO_CCAA)]
    urls = []
    for slug, _, _ in TEMAS:
        gw.escribir(gw.WEB / "rankings" / slug / "index.html", PAGINAS[slug](gw, todas, rutas))
        urls.append(f"rankings/{slug}/")
    return urls
