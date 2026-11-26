"""Evolución de los precios en cada ficha de ciudad: "Evolución del precio del alquiler en <ciudad>".

Petición de Juan (24/11/2026): mostrar cómo han cambiado los precios en los últimos años.
Usa solo lo que ya está en ciudades_nivel1.json:
- serie_alquiler (SERPAVI, Ministerio de Vivienda y Agenda Urbana, 2011-ANIO): alquiler mediano
  al mes y €/m² de los pisos alquilados como vivienda habitual y declarados en el IRPF.
- serie_renta (ADRH, INE, 2015-ANIO): renta neta media por hogar.
Con la regla de fiabilidad de siempre: menos de 30 pisos = sin dato (ya viene a None del JSON);
de 30 a 99 = se muestra con *. Nada se estima: si falta un dato, sale "no disponible".

generar_web.py llama a seccion() desde pagina_ciudad(); el gráfico lo dibuja chart_svg() allí.
Test: tests/test_evolucion.py.
"""
import html

MIN_FIABLE = 100   # de 30 a 99 pisos: dato con aviso (*)


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


def filas_serie(c):
    """Una fila por año (de la serie del SERPAVI), con los cálculos ya hechos. La usa también el test."""
    renta = {s["anio"]: s["renta_hogar"] for s in c.get("serie_renta", []) if s.get("renta_hogar")}
    filas, previo = [], None
    for s in sorted(c.get("serie_alquiler", []), key=lambda s: s["anio"]):
        a, alq = s["anio"], s.get("alquiler_mes")
        r = renta.get(a)
        filas.append({
            "anio": a, "alquiler_mes": alq, "eur_m2": s.get("eur_m2"), "inmuebles": s.get("inmuebles"),
            "aviso": alq is not None and (s.get("inmuebles") or 0) < MIN_FIABLE,
            # cambio del €/m², no del alquiler al mes: el €/mes depende del tamaño de los pisos alquilados cada año
            # (Pamplona 2022: −14 % al mes con +6 % por m²)
            "cambio": cambio(previo, s.get("eur_m2")) if previo is not None and s.get("eur_m2") is not None else None,
            "renta_hogar": r,
            "pct_renta": alq * 12 / r * 100 if (alq and r) else None,
        })
        previo = s.get("eur_m2") if alq is not None else None   # si un año falta, el siguiente no lleva cambio (no se compara con dos años antes)
    while filas and filas[0]["alquiler_mes"] is None:   # años sin dato antes del primero que hay (Navarra): fuera
        filas.pop(0)
    return filas


def _frases(c, filas, anio):
    nombre = c["nombre"]
    ok = [f for f in filas if f["eur_m2"] is not None]
    if len(ok) < 3:
        return []
    m2 = {f["anio"]: f["eur_m2"] for f in ok}
    mes = {f["anio"]: f["alquiler_mes"] for f in ok if f["alquiler_mes"] is not None}
    rent = {f["anio"]: f["renta_hogar"] for f in filas if f["renta_hogar"]}
    a0, a1 = ok[0]["anio"], ok[-1]["anio"]
    t = []
    if a0 in mes and a1 in mes and a0 < a1:
        t.append(f"El alquiler mediano de un piso en {esc(nombre)} ha pasado de {n(mes[a0])} € al mes en {a0} "
                 f"a {n(mes[a1])} € en {a1}.")
    ch = cambio(m2[a0], m2[a1])
    if ch is not None and a0 < a1:
        t.append(f"Por metro cuadrado, que no depende del tamaño de los pisos, es un {d(abs(ch), 0)} % "
                 f"{'más caro' if ch >= 0 else 'más barato'} que en {a0}.")
    # punto más bajo, si no está en un extremo de la serie (p. ej., la bajada de 2011-2015)
    amin = min(m2, key=lambda a: (m2[a], a))
    if a0 < amin < a1:
        t.append(f"El precio por m² tocó fondo en {amin} ({d(m2[amin], 2)} €/m²) y desde entonces ha "
                 f"{'subido' if m2[a1] >= m2[amin] else 'bajado'} un {d(abs(cambio(m2[amin], m2[a1])), 0)} %.")
    if 2019 in m2 and anio in m2 and a0 < 2019:
        ch19 = cambio(m2[2019], m2[anio])
        t.append(f"Desde 2019, el precio por m² ha {'subido' if ch19 >= 0 else 'bajado'} un {d(abs(ch19), 0)} %.")
    # mayor subida anual del precio por m², solo entre años consecutivos con dato
    subidas = [f for f in filas if f["cambio"] is not None]
    if subidas:
        mx = max(subidas, key=lambda f: (f["cambio"], f["anio"]))
        if mx["cambio"] > 0:
            t.append(f"La mayor subida en un año fue la de {mx['anio']}: {signo(mx['cambio'])} en el precio por m².")
    if 2015 in m2 and anio in m2 and 2015 in rent and anio in rent:
        ca, cr = cambio(m2[2015], m2[anio]), cambio(rent[2015], rent[anio])
        if ca is not None and cr is not None:
            rel = "más rápido" if ca > cr else "más despacio"
            t.append(f"Entre 2015 y {anio} el alquiler por m² ha cambiado un {d(ca, 0)} % y la renta del hogar un {d(cr, 0)} %: "
                     f"el alquiler ha crecido {rel} que los ingresos.")
    return t


def seccion_sin_serie(c):
    """Ciudades con menos de 3 años de alquiler (País Vasco): se dice qué años hay y, si existe, cómo ha cambiado la renta."""
    nombre = c["nombre"]
    filas = filas_serie(c)
    con = [f["anio"] for f in filas if f["alquiler_mes"] is not None]
    t = []
    if con:
        t.append(f"La estadística de alquileres del Ministerio de Vivienda y Agenda Urbana (SERPAVI) solo tiene datos fiables de "
                 f"{esc(nombre)} para {' y '.join(str(a) for a in con)}, así que no se puede mostrar cómo ha cambiado el alquiler.")
    rr = [{"anio": x["anio"], "renta_hogar": x["renta_hogar"]} for x in c.get("serie_renta", []) if x.get("renta_hogar")]
    if len(rr) >= 2:
        ch = cambio(rr[0]["renta_hogar"], rr[-1]["renta_hogar"])
        t.append(f"La renta neta media del hogar sí tiene serie: ha pasado de {n(rr[0]['renta_hogar'])} € en {rr[0]['anio']} a "
                 f"{n(rr[-1]['renta_hogar'])} € en {rr[-1]['anio']} ({signo(ch)}; INE, Atlas de Distribución de Renta de los Hogares).")
    if not t:
        t.append(f"No hay serie histórica suficiente para {esc(nombre)}.")
    return f'<section id="evolucion"><h2>Evolución</h2><p class="sub">{" ".join(t)}</p></section>'


def seccion(c, svg, anio):
    """HTML de la sección #evolucion de la ficha. svg = gráfico del €/m² (chart_svg de generar_web)."""
    nombre = c["nombre"]
    filas = filas_serie(c)
    if not svg or not filas:
        return seccion_sin_serie(c)
    tr = []
    for f in reversed(filas):   # el año más reciente arriba
        ast = "*" if f["aviso"] else ""
        if f["alquiler_mes"] is None:
            motivo = " (menos de 30 pisos)" if f["inmuebles"] is not None and f["inmuebles"] < 30 else ""
            alq = f'<td colspan="3" style="color:var(--muted)">No disponible{motivo}</td>'
        else:
            alq = (f'<td>{n(f["alquiler_mes"])} €{ast}</td>'
                   f'<td>{d(f["eur_m2"], 2)} €</td>'
                   f'<td>{signo(f["cambio"]) if f["cambio"] is not None else "—"}</td>')
        tr.append(f'<tr><th scope="row">{f["anio"]}</th>{alq}'
                  f'<td>{n(f["inmuebles"]) if f["inmuebles"] else "—"}</td>'
                  f'<td>{n(f["renta_hogar"]) + " €" if f["renta_hogar"] else "—"}</td>'
                  f'<td>{d(f["pct_renta"]) + " %" if f["pct_renta"] is not None else "—"}</td></tr>')
    a0 = filas[0]["anio"]
    r0 = min((x["anio"] for x in c.get("serie_renta", []) if x.get("renta_hogar")), default=None)
    notas = [f"Alquiler: mediana de los alquileres de pisos alquilados como vivienda habitual y declarados en el IRPF de cada año "
             f"(SERPAVI; origen de los datos: Ministerio de Vivienda y Agenda Urbana). Son contratos reales, no precios de anuncios, "
             f"por eso suelen ser más bajos que los de los portales inmobiliarios."]
    notas.append("El cambio anual se calcula con el precio por m², que no depende del tamaño de los pisos alquilados cada año.")
    if any(f["aviso"] for f in filas):
        notas.append("* Entre 30 y 99 pisos declarados: dato menos fiable.")
    if r0:
        notas.append(f"Renta: renta neta media por hogar, Atlas de Distribución de Renta de los Hogares (elaboración propia con datos "
                     f"extraídos del sitio web del INE: www.ine.es), disponible desde {r0}.")
    notas.append("Alquiler sobre la renta: alquiler mediano × 12 / renta neta media del hogar. Es una estimación propia y aproximada "
                 "(mediana de los inquilinos frente a la media de todos los hogares).")
    frases = _frases(c, filas, anio)
    return (f'<section id="evolucion"><h2>Evolución del precio del alquiler en {esc(nombre)}</h2>'
            f'<p class="sub">Alquiler mediano de un piso, en euros por m² al mes, de {a0} a {anio}.</p>{svg}'
            + (f'<p class="sub" style="margin-top:12px">{" ".join(frases)}</p>' if frases else "")
            + f'<h3 style="margin-top:24px">El alquiler en {esc(nombre)}, año a año</h3>'
            f'<div class="wrap"><table class="evol" style="white-space:nowrap"><thead><tr><th scope="col">Año</th><th scope="col">Alquiler al mes</th>'
            f'<th scope="col">€/m²</th><th scope="col">Cambio del €/m² en un año</th><th scope="col">Pisos alquilados</th>'
            f'<th scope="col">Renta del hogar</th><th scope="col">Alquiler sobre renta</th></tr></thead>'
            f'<tbody>{"".join(tr)}</tbody></table></div>'
            f'<p class="sub" style="margin-top:12px;font-size:14px">{esc(" ".join(notas))}</p></section>')
