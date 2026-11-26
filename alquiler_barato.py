"""Páginas para búsquedas concretas de alquiler barato (B-38).

Responden a dos búsquedas que ninguna otra página de la web contesta por sí sola:

    /rankings/ciudad-mas-barata-de-cada-comunidad/   "ciudad más barata para alquilar en <comunidad>"
        Para cada comunidad: su ciudad más barata, la más cara y el distrito más barato de
        todas sus ciudades, en una sola tabla. Incluye las comunidades sin página propia.

    /alquiler-barato/<ciudad>/   "barrios más baratos para alquilar en <ciudad>", "vivir barato cerca de <ciudad>"
        Una página por provincia: los distritos de su ciudad más poblada y las demás ciudades de
        la provincia en un único ranking, del alquiler más bajo al más alto, con el ahorro al año
        frente a la mediana de la ciudad y los ingresos necesarios con la regla del 30 %.
        Solo si la ciudad tiene MIN_DISTRITOS distritos con alquiler fiable y la provincia
        MIN_OTRAS ciudades más con datos (regla 8: nada de páginas que repitan la ficha).

Solo usa datos que ya están en ciudades_nivel1.json y comunidades.json; los distritos siguen la
regla de la ficha (menos de 30 inmuebles no se usan; de 30 a 99, con *). No hay datos de
distancia ni de transporte, y la página lo dice: "más barato" no significa "bien comunicado".

generar_web.py solo hace cuatro cosas con este módulo: importarlo, poner la tarjeta en la
portada (tarjeta()), el enlace en la ficha de cada ciudad (enlace_ficha()) y llamar a generar()
en main(), que devuelve las rutas para el sitemap.
"""
import statistics

import rankings_temas as rt

SLUG_CCAA = "ciudad-mas-barata-de-cada-comunidad"
TITULO_CCAA = "Ciudad más barata para alquilar en cada comunidad"
DESC_TARJETA = "La ciudad con el alquiler más bajo de cada comunidad, la más cara y su distrito más barato."
CARPETA = "alquiler-barato"
MIN_DISTRITOS = 5   # distritos con alquiler fiable en la ciudad principal
MIN_OTRAS = 3       # otras ciudades de la provincia con datos
U = rt.UMBRAL_ASEQUIBLE / 100


def _esc(s):
    return rt._esc(s)


def tarjeta(root):
    return (f'<a class="card" href="{root}rankings/{SLUG_CCAA}/"><strong>{_esc(TITULO_CCAA)}</strong>'
            f'<span>{_esc(DESC_TARJETA)}</span></a>')


# ------------------------------------------------------------------ datos
def visibles(c):
    """Distritos con alquiler que se puede mostrar (misma regla que la ficha)."""
    return [x for x in c.get("distritos") or []
            if x["fiabilidad"] in ("ok", "pocos_datos") and x.get("alquiler_mes") is not None]


_CACHE = {}


def provincias(todas):
    """[(ciudad principal, [otras ciudades de la provincia])] de las provincias con página, de más a menos población."""
    clave = tuple(c["slug"] for c in todas)
    if clave not in _CACHE:
        por = {}
        for c in todas:
            por.setdefault(c["provincia"], []).append(c)
        out = []
        for cs in por.values():
            cs = sorted(cs, key=lambda c: (-c["poblacion"], c["nombre"]))
            cap, otras = cs[0], cs[1:]
            if len(visibles(cap)) >= MIN_DISTRITOS and len(otras) >= MIN_OTRAS:
                out.append((cap, otras))
        _CACHE[clave] = sorted(out, key=lambda t: -t[0]["poblacion"])
    return _CACHE[clave]


def enlace_ficha(root, c, todas):
    """Enlace desde la ficha de una ciudad a la página de su provincia, si la hay."""
    for cap, otras in provincias(todas):
        if c is cap or c["slug"] == cap["slug"] or c["slug"] in {o["slug"] for o in otras}:
            return (f'<p><a href="{root}{CARPETA}/{cap["slug"]}/">Dónde alquilar más barato en {_esc(cap["nombre"])} y su provincia</a>: '
                    f'sus distritos y las demás ciudades de la provincia de {_esc(cap["provincia"])}, del alquiler más bajo al más alto.</p>')
    return ""


def nd(x):
    """Nombre de un distrito para el texto: 'Distrito 4 (Cerro-Amate, Palmete y otros barrios)' o 'Usera'."""
    if " · " in x["nombre"]:
        a, b = x["nombre"].split(" · ", 1)
        return f"{a} ({b})"
    return x["nombre"]


def ingresos(alq):
    return alq / U


# ------------------------------------------------------------------ página por provincia
def pagina_provincia(gw, cap, otras, provs, todas):
    root = "../../"
    A = gw.ANIO
    n, d, pc, esc = gw.n, gw.d, gw.pc, gw.esc
    nom, corto, prov = cap["nombre"], gw.nombre_comun(cap), cap["provincia"]
    med = cap["alquiler_mes"]
    ds = sorted(visibles(cap), key=lambda x: (x["alquiler_mes"], x["numero"]))
    ocultos = len(cap["distritos"]) - len(ds)
    bd, cd = ds[0], ds[-1]
    baratas = sorted([o for o in otras if o["alquiler_mes"] < med], key=lambda o: (o["alquiler_mes"], o["nombre"]))
    caras = sorted([o for o in otras if o["alquiler_mes"] > med], key=lambda o: (-o["alquiler_mes"], o["nombre"]))
    ahorro = lambda v: (med - v) * 12
    ast = lambda x: "*" if x.get("fiabilidad") == "pocos_datos" else ""
    eur = lambda v: f"{n(v)} €"
    nom_e = esc(nom)
    sueldo_url = f"{root}donde-vivir-con-mi-sueldo/"

    claves = [f"En {nom_e}, la mitad de los pisos alquilados como vivienda habitual cuesta menos de {eur(med)} al mes. "
              f"Entre sus {len(ds)} distritos con dato fiable, el más barato es {esc(nd(bd))}, con {eur(bd['alquiler_mes'])}{ast(bd)}: "
              f"unos {eur(ahorro(bd['alquiler_mes']))} menos al año que la mediana de la ciudad. "
              f"El más caro es {esc(nd(cd))}, con {eur(cd['alquiler_mes'])}{ast(cd)}."]

    con_m2 = [x for x in ds if x.get("eur_m2")]
    if con_m2:
        bm2 = min(con_m2, key=lambda x: (x["eur_m2"], x["numero"]))
        if bm2 is not bd:
            frase = (f"El distrito más barato al mes no es el más barato por metro cuadrado. Por m², el más económico es "
                     f"{esc(nd(bm2))} ({d(bm2['eur_m2'], 2)} €/m²)")
            if bd.get("eur_m2"):
                frase += f", mientras que en {esc(nd(bd))} el m² sale a {d(bd['eur_m2'], 2)} €"
            if bd.get("superficie_m2") and bm2.get("superficie_m2"):
                frase += (f". El piso mediano alquilado mide {n(bd['superficie_m2'])} m² en el primero y {n(bm2['superficie_m2'])} m² "
                          f"en el segundo: parte de la diferencia de precio es de tamaño")
            claves.append(frase + ".")
        else:
            claves.append(f"{esc(nd(bd))} es también el distrito más barato por metro cuadrado ({d(bd['eur_m2'], 2)} €/m²), "
                          "así que su alquiler bajo no se explica solo por tener pisos más pequeños.")

    cuantas = f"las {len(otras)} ciudades" if len(baratas) == len(otras) else f"{len(baratas)} de las {len(otras)} ciudades"
    if baratas:
        top = baratas[:3]
        claves.append(f"Fuera de la ciudad, {cuantas} de más de {gw.MIN_POB} habitantes de la provincia de {esc(prov)} "
                      f"tienen un alquiler mediano más bajo que {nom_e}. Las más baratas son "
                      f"{rt.y_lista(esc(o['nombre']) + ' (' + eur(o['alquiler_mes']) + ')' for o in top)}. "
                      f"Vivir de alquiler en {esc(baratas[0]['nombre'])} en vez de en {nom_e} supone, en la mediana, "
                      f"unos {eur(ahorro(baratas[0]['alquiler_mes']))} menos al año.")
        aun = [o for o in baratas if o["alquiler_mes"] < bd["alquiler_mes"]]
        if aun:
            claves.append(f"{len(aun)} de ellas son incluso más baratas que el distrito más barato de {nom_e}: "
                          f"{rt.y_lista(esc(o['nombre']) for o in aun[:6])}{' y otras' if len(aun) > 6 else ''}. "
                          f"En el resto, buscar dentro de {nom_e} en los distritos más baratos sale igual o mejor que salir de la ciudad.")
        else:
            claves.append(f"Ninguna ciudad de la provincia tiene un alquiler mediano más bajo que el distrito más barato de {nom_e} "
                          f"({eur(bd['alquiler_mes'])}): para pagar menos, sus distritos más económicos compiten con las ciudades de alrededor.")
    else:
        claves.append(f"Ninguna de las {len(otras)} ciudades de más de {gw.MIN_POB} habitantes de la provincia de {esc(prov)} "
                      f"tiene un alquiler mediano más bajo que {nom_e}: aquí lo más barato hay que buscarlo en sus propios distritos.")

    sue = (f"Con la regla orientativa de no dedicar al alquiler más del {rt.UMBRAL_ASEQUIBLE} % de los ingresos netos, "
           f"el alquiler mediano de {nom_e} pide unos {eur(ingresos(med))} netos al mes; el de {esc(nd(bd))}, unos {eur(ingresos(bd['alquiler_mes']))}")
    if baratas:
        sue += f", y el de {esc(baratas[0]['nombre'])}, unos {eur(ingresos(baratas[0]['alquiler_mes']))}"
    claves.append(sue + f'. Puedes hacer la cuenta con tu sueldo en la calculadora <a href="{sueldo_url}">¿Dónde puedo vivir con mi sueldo?</a>.')

    con_pc = [x for x in ds if x.get("alquiler_pct_renta") is not None]
    if con_pc:
        lp = min(con_pc, key=lambda x: (x["alquiler_pct_renta"], x["numero"]))
        hp = max(con_pc, key=lambda x: (x["alquiler_pct_renta"], -x["numero"]))
        claves.append(f"Barato no siempre quiere decir asequible para quien vive allí. Comparado con la renta media de sus hogares, "
                      f"donde menos pesa el alquiler es {esc(nd(lp))} ({pc(lp['alquiler_pct_renta'])}) y donde más, "
                      f"{esc(nd(hp))} ({pc(hp['alquiler_pct_renta'])}).")
    if caras:
        claves.append(f"En el otro extremo, {len(caras)} {'ciudad' if len(caras) == 1 else 'ciudades'} de la provincia "
                      f"{'es más cara' if len(caras) == 1 else 'son más caras'} que {nom_e}; la que más, "
                      f"{esc(caras[0]['nombre'])}, con {eur(caras[0]['alquiler_mes'])} al mes.")

    # listas resumen
    li_d = "".join(f'<li><a href="{root}{cap["slug"]}/#d{x["numero"]}">{esc(nd(x))}</a><strong>{eur(x["alquiler_mes"])}{ast(x)}</strong></li>'
                   for x in ds[:5])
    li_c = "".join(f'<li><a href="{root}{o["slug"]}/">{esc(o["nombre"])}</a><strong>{eur(o["alquiler_mes"])}</strong></li>'
                   for o in baratas[:5])
    dos = (f'<div class="two"><div><h3>Distritos más baratos de {nom_e}</h3><ol class="lnk">{li_d}</ol></div>'
           + (f'<div><h3>Ciudades de la provincia más baratas que {nom_e}</h3><ol class="lnk">{li_c}</ol></div>' if baratas else "")
           + '</div>')
    comp = ""
    if baratas:
        sel = [cap] + baratas[:3]
        comp = (f'<p><a href="{root}comparar-ciudades/?c={",".join(o["slug"] for o in sel)}">Compara {nom_e} con '
                f'{rt.y_lista(esc(o["nombre"]) for o in sel[1:])} lado a lado</a>: renta, población, edad y evolución del alquiler.</p>')

    # tabla conjunta: distritos de la ciudad + ciudades de la provincia (+ la media de la ciudad como referencia)
    filas_d = [{"nombre": nd(x), "href": f'{root}{cap["slug"]}/#d{x["numero"]}', "tipo": f"Distrito de {corto}",
                "alq": x["alquiler_mes"], "m2": x.get("eur_m2"), "sup": x.get("superficie_m2"),
                "pcr": x.get("alquiler_pct_renta"), "ast": ast(x), "zona": gw.zona_html(x)} for x in ds]
    filas_c = [{"nombre": o["nombre"] if o is not cap else f"{o['nombre']} (toda la ciudad)", "href": f'{root}{o["slug"]}/',
                "tipo": "Ciudad" if o is not cap else "Media de la ciudad",
                "alq": o["alquiler_mes"], "m2": o.get("eur_m2"), "sup": o.get("superficie_m2"),
                "pcr": o.get("alquiler_pct_renta"), "ast": "", "zona": ""} for o in [cap] + otras]
    filas = sorted(filas_d + filas_c, key=lambda r: (r["alq"], r["tipo"] != "Media de la ciudad", r["nombre"]))
    fv = lambda v, k=2: "" if v is None else f"{v:.{k}f}"
    trs = "".join(
        f'<tr><td data-v="{i}">{i}</td><th scope="row" data-v="{esc(r["nombre"])}"><a href="{r["href"]}">{esc(r["nombre"])}</a>{r["zona"]}</th>'
        f'<td data-v="{esc(r["tipo"])}">{esc(r["tipo"])}</td>'
        f'<td data-v="{fv(r["alq"])}">{eur(r["alq"])}{r["ast"]}</td>'
        f'<td data-v="{fv(r["m2"])}">{d(r["m2"], 2) if r["m2"] else "—"}</td>'
        f'<td data-v="{fv(r["sup"], 0)}">{n(r["sup"]) + " m²" if r["sup"] else "—"}</td>'
        f'<td data-v="{fv(ingresos(r["alq"]))}">{eur(ingresos(r["alq"]))}</td>'
        f'<td data-v="{fv(r["pcr"], 1)}">{pc(r["pcr"])}</td></tr>'
        for i, r in enumerate(filas, 1))
    th = gw.th_orden
    notas = []
    if any(r["ast"] for r in filas):
        notas.append("* Pocos inmuebles en la muestra (entre 30 y 99): interpreta la cifra con cuidado.")
    if ocultos:
        notas.append(f"No aparecen {ocultos} {'distrito' if ocultos == 1 else 'distritos'} de {nom} con menos de 30 pisos en alquiler "
                     "en la muestra: su cifra no sería fiable.")
    tabla = (f'<section id="tabla"><h2>Distritos de {nom_e} y ciudades de la provincia, del alquiler más bajo al más alto</h2>'
             f'<p class="sub">Alquiler mensual mediano de un piso en {A}. Pulsa una columna para ordenar.</p>'
             f'<div class="wrap"><table class="sortable numbered"><thead><tr><th>#</th>{th(1, "Zona", "text")}{th(2, "Tipo", "text")}'
             f'{th(3, "Alquiler al mes")}{th(4, "€/m²")}{th(5, "Superficie mediana")}'
             f'{th(6, f"Ingresos netos al mes para el {rt.UMBRAL_ASEQUIBLE} %")}{th(7, "Alquiler sobre renta")}</tr></thead>'
             f'<tbody>{trs}</tbody></table></div>'
             + "".join(f'<p class="proto">{esc(t)}</p>' for t in notas) + '</section>')

    # enlaces
    cc = gw.ccaa_de(cap)
    mas = [f'<li><a href="{root}{cap["slug"]}/">Ficha completa de {nom_e}</a><span>mapa, evolución y perfil</span></li>']
    if cc and cc.get("pagina"):
        mas.append(f'<li><a href="{root}comunidades/{cc["slug"]}/">Ciudades {esc(gw.de_(cc["en"]))}</a><span>{len(cc["ciudades"])} ciudades</span></li>')
    mas.append(f'<li><a href="{root}rankings/{SLUG_CCAA}/">{esc(TITULO_CCAA)}</a><span>todas las comunidades</span></li>')
    mas.append(f'<li><a href="{root}rankings/barrios-con-el-alquiler-mas-caro/">Barrios con el alquiler más caro y más barato de España</a><span>ranking nacional</span></li>')
    otras_p = "".join(f'<li><a href="{root}{CARPETA}/{c2["slug"]}/">{esc(c2["nombre"])} y su provincia</a>'
                      f'<span>desde {eur(min(x["alquiler_mes"] for x in visibles(c2) + o2))}</span></li>'
                      for c2, o2 in provs if c2 is not cap)
    enl = (f'<section id="mas"><h2>Más para comparar</h2><div class="two"><div><h3>Sobre {nom_e}</h3><ul class="lnk">{"".join(mas)}</ul></div>'
           f'<div><h3>Dónde alquilar más barato en otras provincias</h3><ul class="lnk">{otras_p}</ul></div></div></section>')

    met = rt._metodologia(gw, [
        rt.NOTA_ALQUILER, rt.NOTA_RENTA,
        f"<strong>Distritos:</strong> distritos censales del INE de {nom_e}. Solo se muestran los que tienen 30 pisos o más en la muestra; "
        "de 30 a 99, con *. El nombre y los barrios son los de la ficha de la ciudad.",
        f"<strong>Ciudades de la provincia:</strong> solo las de más de {gw.MIN_POB} habitantes con alquiler fiable. Los municipios más pequeños "
        "no aparecen, aunque alguno pueda ser más barato.",
        f"<strong>Ahorro al año:</strong> (alquiler mediano de {nom_e} − alquiler mediano de la zona) × 12. Compara medianas: "
        "no es lo que ahorraría un piso concreto.",
        f"<strong>Ingresos netos para el {rt.UMBRAL_ASEQUIBLE} %:</strong> alquiler mediano mensual ÷ {d(U, 2)}. Regla orientativa, "
        "no un umbral oficial; no incluye suministros, comunidad ni fianza.",
        "<strong>Distancias y transporte:</strong> no tenemos datos oficiales de distancia ni de tiempo de viaje. "
        "Que una ciudad sea más barata no quiere decir que esté bien comunicada con tu trabajo: compruébalo antes de decidir."])

    aviso = gw.aviso_turistico() if cc and cc.get("cod_ccaa") in gw.CCAA_COSTA else ""
    ruta = f"{CARPETA}/{cap['slug']}/"
    titulo = f"Dónde alquilar más barato en {corto}: barrios y alrededores"
    if len(titulo) > 60:
        titulo = f"Alquiler barato en {corto}: barrios y alrededores"
    if len(titulo) > 60:
        titulo = f"Alquiler barato en {corto} y su provincia"
    h1 = f"Dónde alquilar más barato en {nom} y su provincia ({A})"
    desc = (f"Distritos más baratos de {corto} (desde {n(bd['alquiler_mes'])} €/mes) y "
            + (f"{len(baratas)} ciudades de la provincia con alquiler más bajo" if baratas else "las demás ciudades de su provincia")
            + f". Datos oficiales de {A}.")
    if len(desc) > 160:
        desc = f"Distritos y ciudades más baratos para alquilar en {corto} y su provincia. Datos oficiales de {A}."
    lead = (f"Los {len(ds)} distritos de {nom_e} con dato fiable y las {len(otras)} ciudades de más de {gw.MIN_POB} habitantes de la provincia "
            f"de {esc(prov)}, ordenados del alquiler mediano más bajo al más alto, con lo que se ahorra al año frente a la mediana de la ciudad "
            "y los ingresos que hacen falta para pagarlo.")
    facts = (f'<dl class="facts">'
             f'<div><dt>Alquiler mediano en {nom_e}</dt><dd>{eur(med)}/mes<small>{d(cap.get("eur_m2"), 2)} €/m²</small></dd></div>'
             f'<div><dt>Distrito más barato</dt><dd>{eur(bd["alquiler_mes"])}{ast(bd)}<small>{esc(nd(bd))}</small></dd></div>'
             + (f'<div><dt>Ciudad más barata de la provincia</dt><dd>{eur(baratas[0]["alquiler_mes"])}<small>{esc(baratas[0]["nombre"])}</small></dd></div>'
                if baratas else
                f'<div><dt>Ciudades de la provincia más baratas</dt><dd class="big">0<small>de {len(otras)}</small></dd></div>')
             + '</dl>')
    pasos = [("Inicio", ""), (nom, f"{cap['slug']}/")]
    actual = "Dónde alquilar más barato"
    cuerpo = (gw.cabecera(root, [("#claves", "Claves"), ("#tabla", "Tabla"), ("#metodologia", "Metodología")]) +
              f'<div class="hero"><div>{gw.migas_html(root, pasos, actual)}<h1>{esc(h1)}</h1>'
              f'<p class="lead">{lead}</p>{facts}{aviso}</div></div><main>'
              f'<section id="claves"><h2>Qué dicen los datos</h2>{"".join(f"<p>{p}</p>" for p in claves)}{dos}{comp}</section>'
              f'{tabla}{enl}{met}{gw.pie(root)}</main>')
    ld = [gw.dataset(f"Alquiler en los distritos de {nom} y las ciudades de su provincia ({A})", desc, ruta,
                     f"Provincia de {prov}, España",
                     ["Alquiler mensual mediano", "Alquiler mediano por m²", "Superficie mediana",
                      "Ingresos netos necesarios para el alquiler mediano", "Alquiler sobre renta"]),
          gw.migas(pasos + [(actual, ruta)])]
    return gw.head(titulo, desc, root, ruta, ld) + cuerpo + gw.fin(root)


# ------------------------------------------------------------------ ciudad más barata de cada comunidad
def filas_ccaa(gw):
    out = []
    for cc in gw.COMUNIDADES.values():
        cs = sorted(cc["ciudades"], key=lambda c: (c["alquiler_mes"], c["nombre"]))
        if not cs:
            continue
        dd = [(x, c) for c in cs for x in visibles(c)]
        bdist = min(dd, key=lambda t: (t[0]["alquiler_mes"], t[1]["nombre"], t[0]["numero"])) if dd else None
        out.append({"cc": cc, "cs": cs, "barata": cs[0], "cara": cs[-1], "bdist": bdist})
    return sorted(out, key=lambda r: (r["barata"]["alquiler_mes"], gw.norm(r["cc"]["comun"])))


def pagina_ccaa(gw, todas, provs, rutas):
    root = "../../"
    A = gw.ANIO
    n, esc = gw.n, gw.esc
    eur = lambda v: f"{n(v)} €"
    fs = filas_ccaa(gw)
    N = len(fs)
    en = lambda r: r["cc"]["en"]
    nb = lambda c: esc(c["nombre"])

    p0, pN = fs[0], fs[-1]
    claves = [f"La ciudad de más de {gw.MIN_POB} habitantes con el alquiler mediano más bajo de España es {nb(p0['barata'])}, "
              f"{esc(en(p0))}, con {eur(p0['barata']['alquiler_mes'])} al mes. En el otro extremo está {esc(pN['cc']['comun'])}: "
              f"allí hasta la ciudad más barata, {nb(pN['barata'])}, tiene un alquiler mediano de {eur(pN['barata']['alquiler_mes'])}."]
    med_b = statistics.median(r["barata"]["alquiler_mes"] for r in fs)
    claves.append(f"En la comunidad típica, la ciudad más barata para alquilar ronda los {eur(med_b)} al mes. "
                  f"Por debajo de 450 € hay ciudades en {sum(1 for r in fs if r['barata']['alquiler_mes'] < 450)} de las {N} comunidades "
                  "y ciudades autónomas con datos.")
    varias = [r for r in fs if len(r["cs"]) >= 3]
    if varias:
        gap = lambda r: r["cara"]["alquiler_mes"] - r["barata"]["alquiler_mes"]
        g1 = max(varias, key=lambda r: (gap(r), r["cc"]["comun"]))
        g0 = min(varias, key=lambda r: (gap(r), r["cc"]["comun"]))
        claves.append(f"Dentro de una misma comunidad, la mayor distancia está {esc(en(g1))}: entre {nb(g1['cara'])} "
                      f"({eur(g1['cara']['alquiler_mes'])}) y {nb(g1['barata'])} ({eur(g1['barata']['alquiler_mes'])}) hay "
                      f"{eur(gap(g1))} al mes, unos {eur(gap(g1) * 12)} al año. La menor, {esc(en(g0))}: "
                      f"{eur(gap(g0))} al mes entre {nb(g0['cara'])} y {nb(g0['barata'])}.")
    dmas = [r for r in fs if r["bdist"] and r["bdist"][0]["alquiler_mes"] < r["barata"]["alquiler_mes"]]
    if dmas:
        ej = max(dmas, key=lambda r: (r["barata"]["alquiler_mes"] - r["bdist"][0]["alquiler_mes"], r["cc"]["comun"]))
        x, c = ej["bdist"]
        cuantas_d = f"En las {N}" if len(dmas) == N else f"En {len(dmas)} de las {N}"
        claves.append(f"{cuantas_d} hay algún distrito más barato que la ciudad más barata de la comunidad: "
                      f"la media de cada ciudad esconde zonas más económicas. El caso más claro está {esc(en(ej))}: {esc(nd(x))}, en {nb(c)}, "
                      f"tiene un alquiler mediano de {eur(x['alquiler_mes'])}, frente a los {eur(ej['barata']['alquiler_mes'])} de {nb(ej['barata'])}.")
    sobre = [r for r in fs if r["cc"].get("alquiler_mes") and r["barata"]["alquiler_mes"] > r["cc"]["alquiler_mes"]]
    if sobre:
        claves.append(f"En {len(sobre)} comunidades, incluso la ciudad más barata supera el alquiler mediano del conjunto de la comunidad, "
                      f"que incluye pueblos y ciudades pequeñas: {rt.y_lista(esc(r['cc']['comun']) for r in sobre[:8])}"
                      f"{' y otras' if len(sobre) > 8 else ''}. Es decir, allí los municipios más pequeños son, en conjunto, más baratos que sus ciudades.")
    pocas = [r for r in fs if len(r["cs"]) == 1]
    if pocas:
        claves.append(f"{rt.y_lista(esc(r['cc']['comun']) for r in pocas)} {'tiene' if len(pocas) == 1 else 'tienen'} una sola ciudad "
                      f"de más de {gw.MIN_POB} habitantes con alquiler fiable, así que su ciudad más barata y la más cara son la misma.")

    fv = lambda v: "" if v is None else f"{v:.2f}"
    trs = []
    for r in fs:
        cc = r["cc"]
        nomb = f'<a href="{root}comunidades/{cc["slug"]}/">{esc(cc["comun"])}</a>' if cc.get("pagina") else esc(cc["comun"])
        b, k = r["barata"], r["cara"]
        if r["bdist"]:
            x, c = r["bdist"]
            dist = (f'<td data-v="{fv(x["alquiler_mes"])}"><a href="{root}{c["slug"]}/#d{x["numero"]}">{esc(nd(x))}</a>, {nb(c)}: '
                    f'{eur(x["alquiler_mes"])}{"*" if x["fiabilidad"] == "pocos_datos" else ""}</td>')
        else:
            dist = '<td data-v="">—</td>'
        trs.append(f'<tr id="cc-{cc["slug"]}"><th scope="row" data-v="{esc(cc["comun"])}">{nomb}</th>'
                   f'<td data-v="{len(r["cs"])}">{len(r["cs"])}</td>'
                   f'<td data-v="{fv(b["alquiler_mes"])}"><a href="{root}{b["slug"]}/">{nb(b)}</a>: {eur(b["alquiler_mes"])}</td>'
                   f'<td data-v="{fv(k["alquiler_mes"])}"><a href="{root}{k["slug"]}/">{nb(k)}</a>: {eur(k["alquiler_mes"])}</td>'
                   f'{dist}<td data-v="{fv(cc.get("alquiler_mes"))}">{eur(cc.get("alquiler_mes")) if cc.get("alquiler_mes") else "—"}</td></tr>')
    th = gw.th_orden
    lis = "".join(f'<li><a href="{root}{CARPETA}/{c["slug"]}/">Dónde alquilar más barato en {esc(c["nombre"])} y su provincia</a>'
                  f'<span>desde {eur(min(x["alquiler_mes"] for x in visibles(c) + o))}</span></li>' for c, o in provs)
    tabla = (f'<h2>La ciudad más barata y la más cara de cada comunidad</h2>'
             f'<p class="sub">Alquiler mensual mediano de un piso en {A}, de la comunidad con la ciudad más barata a la de la más cara. '
             'Pulsa una columna para ordenar.</p>'
             f'<div class="wrap"><table class="sortable"><thead><tr>{th(0, "Comunidad", "text")}{th(1, "Ciudades")}'
             f'{th(2, "Ciudad más barata")}{th(3, "Ciudad más cara")}{th(4, "Distrito más barato")}{th(5, "Toda la comunidad")}</tr></thead>'
             f'<tbody>{"".join(trs)}</tbody></table></div>'
             '<p class="proto">Distrito más barato: entre todos los distritos de las ciudades de la comunidad con 30 pisos o más en la muestra '
             '(* de 30 a 99). Toda la comunidad: mediana de todos sus municipios, también los pequeños (SERPAVI).</p>'
             f'<h2 id="provincias">Dónde alquilar más barato en las grandes ciudades y su provincia</h2>'
             f'<p class="sub">Los distritos de la ciudad y las demás ciudades de la provincia en un solo ranking.</p><ul class="lnk">{lis}</ul>')
    desc = (f"Ciudad con el alquiler más barato de cada comunidad autónoma: desde {eur(p0['barata']['alquiler_mes'])} en "
            f"{p0['barata']['nombre']}. Datos oficiales de {A} del SERPAVI.")
    if len(desc) > 160:
        desc = f"Ciudad con el alquiler más barato y más caro de cada comunidad autónoma, y su distrito más barato. Datos oficiales de {A}."
    lead = (f"Para cada comunidad autónoma, la ciudad de más de {gw.MIN_POB} habitantes con el alquiler mediano más bajo, la más cara "
            "y el distrito más barato de todas sus ciudades, en una sola tabla.")
    met = rt._metodologia(gw, [rt.NOTA_ALQUILER,
                               f"<strong>Ciudades:</strong> solo las de más de {gw.MIN_POB} habitantes con alquiler fiable (100 inmuebles o más). "
                               "Los municipios más pequeños no aparecen, aunque alguno pueda ser más barato.",
                               "<strong>Distritos:</strong> distritos censales del INE con 30 pisos o más en la muestra; de 30 a 99, con *.",
                               "<strong>Toda la comunidad:</strong> alquiler mediano de todos los municipios de la comunidad (hoja de comunidades del SERPAVI)."])
    return rt._pagina(gw, SLUG_CCAA, TITULO_CCAA, desc, lead, claves, gw.aviso_turistico(), tabla, met,
                      ["Alquiler mensual mediano por ciudad", "Alquiler mensual mediano por distrito"], rutas)


# ------------------------------------------------------------------ principal
def generar(gw, todas):
    """Escribe las páginas y devuelve sus rutas para el sitemap."""
    provs = provincias(todas)
    rutas = [(s, t) for s, _, t, _ in gw.RANKINGS] + [(s, t) for s, t, _ in rt.TEMAS] + [(SLUG_CCAA, TITULO_CCAA)]
    urls = []
    if gw.COMUNIDADES:
        gw.escribir(gw.WEB / "rankings" / SLUG_CCAA / "index.html", pagina_ccaa(gw, todas, provs, rutas))
        urls.append(f"rankings/{SLUG_CCAA}/")
    for cap, otras in provs:
        gw.escribir(gw.WEB / CARPETA / cap["slug"] / "index.html", pagina_provincia(gw, cap, otras, provs, todas))
        urls.append(f"{CARPETA}/{cap['slug']}/")
    return urls
