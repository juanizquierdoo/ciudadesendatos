"""Texto explicativo de cada ficha de ciudad: "Qué dicen los datos de <ciudad>".

Cada frase se calcula a partir de los datos de la propia ciudad y de las demás
ciudades de la web (ciudades_nivel1.json). No se inventa ni se estima nada: si
falta un dato, la frase no se escribe. Así cada ficha tiene un texto propio,
distinto del de las demás, que interpreta sus cifras (B-17).

generar_web.py llama a seccion_claves() desde pagina_ciudad(), así que las
ciudades nuevas que se añadan al JSON tienen su texto sin tocar nada aquí.
"""
import html
import statistics


def esc(s):
    return html.escape(str(s).replace("'", "’"), quote=True)


def n(x):
    return f"{round(x):,}".replace(",", ".")


def d(x, k=1):
    return f"{x:.{k}f}".replace(".", ",")


def signo(x, k=1):
    return ("+" if x > 0 else "") + d(x, k) + " %"


def mediana(todas, clave):
    v = [c[clave] for c in todas if c.get(clave) is not None]
    return statistics.median(v) if v else None


def ordinal(i):
    return f"{i}.ª"


def comparar(v, ref, mas, menos, umbral=3):
    """'un 12 % más alto que' / 'un 8 % más bajo que' / 'prácticamente igual que'."""
    dif = (v / ref - 1) * 100
    if abs(dif) < umbral:
        return "prácticamente igual que", 0
    return (f"un {d(abs(dif), 0)} % {mas if dif > 0 else menos} que"), (1 if dif > 0 else -1)


def puesto_en(lista, c, clave, desc=True):
    """Puesto de c en lista ordenada por clave (1 = valor más alto si desc). Desempate por nombre."""
    orden = sorted([x for x in lista if x.get(clave) is not None], key=lambda x: ((-x[clave]) if desc else x[clave], x["nombre"]))
    return orden.index(c) + 1, len(orden)


def valor_serie(c, anio, clave="alquiler_mes"):
    for s in c.get("serie_alquiler", []):
        if s["anio"] == anio and s.get(clave):
            return s[clave]
    return None


# ------------------------------------------------------------------ párrafos
def p_alquiler_renta(c, todas, ambito):
    nombre = esc(c["nombre"])
    N = len(todas)
    med_a, med_r, med_p = mediana(todas, "alquiler_mes"), mediana(todas, "renta_hogar"), mediana(todas, "alquiler_pct_renta")
    if not (med_a and med_r and med_p):
        return None
    ca, sa = comparar(c["alquiler_mes"], med_a, "más alto", "más bajo")
    cr, sr = comparar(c["renta_hogar"], med_r, "más alta", "más baja")
    pm2, nm2 = puesto_en(todas, c, "eur_m2")
    t = (f"El alquiler mediano de {nombre}, {n(c['alquiler_mes'])} € al mes, es {ca} la mediana de las {N} {ambito} "
         f"({n(med_a)} €). Por metro cuadrado ({d(c['eur_m2'], 2)} €/m²) es la {ordinal(pm2)} ciudad más cara de las {nm2}. "
         f"La renta media de sus hogares, {n(c['renta_hogar'])} € al año, es {cr} la mediana ({n(med_r)} €).")
    cuadrante = {(1, 1): "Tanto el alquiler como los ingresos están por encima de lo habitual en estas ciudades.",
                 (1, -1): "Combina alquileres más altos que la mediana con ingresos más bajos.",
                 (-1, 1): "Combina alquileres más bajos que la mediana con ingresos más altos.",
                 (-1, -1): "Tanto el alquiler como los ingresos están por debajo de lo habitual en estas ciudades."}.get((sa, sr))
    if cuadrante:
        t += " " + cuadrante
    dif = c["alquiler_pct_renta"] - med_p
    if abs(dif) < 0.5:
        cmp_p = "prácticamente lo mismo que"
    else:
        cmp_p = f"{d(abs(dif), 1)} puntos {'más' if dif > 0 else 'menos'} que"
    t += (f" En conjunto, un año de alquiler equivale al {d(c['alquiler_pct_renta'])} % de la renta del hogar, "
          f"{cmp_p} en la ciudad mediana ({d(med_p)} %).")
    return t


def p_ultimo_anio(c, todas, anio):
    a0, a1 = valor_serie(c, anio - 1), valor_serie(c, anio)
    if not (a0 and a1):
        return None
    ch = (a1 / a0 - 1) * 100
    cambios = []
    for x in todas:
        b0, b1 = valor_serie(x, anio - 1), valor_serie(x, anio)
        if b0 and b1:
            cambios.append(((b1 / b0 - 1) * 100, x["nombre"], x is c))
    med = statistics.median([v for v, _, _ in cambios])
    verbo = "subió" if ch > 0 else ("bajó" if ch < 0 else "se mantuvo")
    nombre = esc(c["nombre"])
    t = (f"Entre {anio - 1} y {anio} el alquiler mediano de {nombre} {verbo} de {n(a0)} a {n(a1)} € al mes ({signo(ch)}). "
         if ch != 0 else f"Entre {anio - 1} y {anio} el alquiler mediano de {nombre} se mantuvo en {n(a1)} € al mes. ")
    m0, m1 = valor_serie(c, anio - 1, "eur_m2"), valor_serie(c, anio, "eur_m2")
    if m0 and m1:
        t += f"Por metro cuadrado pasó de {d(m0, 2)} a {d(m1, 2)} € ({signo((m1 / m0 - 1) * 100)}). "
    t += f"La variación mediana en las {len(cambios)} ciudades con datos de los dos años fue del {signo(med)}."
    orden = sorted(cambios, key=lambda x: (-x[0], x[1]))
    pos = next(i for i, x in enumerate(orden, 1) if x[2])
    if pos <= 10 and ch > 0:
        t += f" Es la {ordinal(pos)} ciudad donde más subió en ese año."
    elif pos > len(orden) - 10:
        t += f" Es una de las 10 ciudades donde menos {'subió' if med > 0 else 'cambió'} en ese año."
    return t


def p_rango(c):
    p25, p75 = c.get("eur_m2_p25"), c.get("eur_m2_p75")
    if not (p25 and p75):
        return None
    sup = (f" La superficie mediana de los pisos alquilados es de {n(c['superficie_m2'])} m²." if c.get("superficie_m2") else "")
    return (f"No todos los pisos cuestan lo mismo: una cuarta parte se alquila por menos de {d(p25, 2)} €/m² al mes "
            f"y otra cuarta parte por más de {d(p75, 2)} €/m². La mitad restante queda entre esos dos valores.{sup}")


def p_provincia(c, todas):
    prov = [x for x in todas if x["provincia"] == c["provincia"]]
    if len(prov) < 2:
        return None
    pos, k = puesto_en(prov, c, "eur_m2")
    if pos == 1:
        que = "la que tiene el alquiler por m² más alto"
    elif pos == k:
        que = "la que tiene el alquiler por m² más bajo"
    else:
        que = f"la {ordinal(pos)} con el alquiler por m² más alto"
    rpos, _ = puesto_en(prov, c, "renta_hogar")
    if rpos == 1:
        renta = " y la de mayor renta media por hogar"
    elif rpos == k:
        renta = " y la de menor renta media por hogar"
    else:
        renta = f"; por renta media del hogar es la {ordinal(rpos)} más alta"
    return (f"De las {k} ciudades de la provincia de {esc(c['provincia'])} que tienen ficha en esta web, "
            f"{esc(c['nombre'])} es {que}{renta}.")


def p_distritos(c):
    dist = [x for x in c.get("distritos", []) if x.get("fiabilidad") == "ok" and x.get("alquiler_mes")]
    if len(dist) < 2:
        return None
    orden = sorted(dist, key=lambda x: (-x["alquiler_mes"], -(x.get("eur_m2") or 0)))
    hi, lo = orden[0], orden[-1]
    t = ""
    if hi["alquiler_mes"] > lo["alquiler_mes"]:
        t = (f"Dentro de la ciudad, el distrito con el alquiler mediano más alto es {esc(hi['nombre'])} "
             f"({n(hi['alquiler_mes'])} € al mes) y el más bajo, {esc(lo['nombre'])} ({n(lo['alquiler_mes'])} €): "
             f"{n(round(hi['alquiler_mes']) - round(lo['alquiler_mes']))} € de diferencia al mes.")
    con_renta = [x for x in c["distritos"] if x.get("renta_hogar")]
    if len(con_renta) >= 2:
        r = sorted(con_renta, key=lambda x: -x["renta_hogar"])
        t += (f" La renta media del hogar va de {n(r[-1]['renta_hogar'])} € en {esc(r[-1]['nombre'])} "
              f"a {n(r[0]['renta_hogar'])} € en {esc(r[0]['nombre'])}.")
    return t.strip() or None


def p_poblacion(c, todas):
    partes = []
    nom = esc(c["nombre"])
    e = c.get("edad_media")
    if e is not None:
        vals = [x["edad_media"] for x in todas if x.get("edad_media") is not None]
        menos, mas, N = sum(v < e for v in vals), sum(v > e for v in vals), len(vals)
        if menos == 0:
            partes.append(f"Con una edad media de {d(e)} años, {nom} es la ciudad más joven de las {N}.")
        elif mas == 0:
            partes.append(f"Con una edad media de {d(e)} años, {nom} es la ciudad más envejecida de las {N}.")
        elif menos < N / 4:
            partes.append(f"Con una edad media de {d(e)} años, {nom} está entre las ciudades más jóvenes: solo {menos} de las {N} tienen una edad media más baja.")
        elif mas < N / 4:
            partes.append(f"Con una edad media de {d(e)} años, {nom} está entre las ciudades más envejecidas: solo {mas} de las {N} tienen una edad media más alta.")
        else:
            partes.append(f"La edad media de {nom}, {d(e)} años, está en la zona media de las {N} ciudades (mediana: {d(statistics.median(vals))} años).")
    u = c.get("pct_unipersonales")
    if u is not None:
        med = mediana(todas, "pct_unipersonales")
        rel = "más" if u > med + 1 else ("menos" if u < med - 1 else None)
        partes.append(f"El {d(u)} % de sus hogares son de una sola persona"
                      + (f", {rel} que en la ciudad mediana ({d(med)} %)." if rel else f", en línea con la ciudad mediana ({d(med)} %)."))
    return " ".join(partes) or None


def p_mercado(c, todas):
    inm, pob = c.get("inmuebles"), c.get("poblacion")
    if not (inm and pob):
        return None
    ratio = lambda x: x["inmuebles"] / x["poblacion"] * 1000
    vals = [ratio(x) for x in todas if x.get("inmuebles") and x.get("poblacion")]
    r = ratio(c)
    med = statistics.median(vals)
    mayor = sum(v > r for v in vals)
    t = (f"Las cifras de alquiler de {esc(c['nombre'])} salen de {n(inm)} pisos alquilados como vivienda habitual y declarados en el IRPF, "
         f"unos {n(r)} por cada 1.000 habitantes (en la ciudad mediana, {n(med)}).")
    if mayor < len(vals) / 4:
        t += f" Es una proporción alta: solo {mayor} de las {len(vals)} ciudades tienen más pisos alquilados declarados por habitante."
    elif len(vals) - mayor - 1 < len(vals) / 4:
        t += " Es una de las proporciones más bajas de la lista."
    return t


def p_zonas_con_mas_alquiler(c):
    """Distritos con más pisos alquilados declarados (24/11/2026). Responde a búsquedas tipo
    "zonas de <ciudad> con más alquiler". Es un recuento del SERPAVI, no una medida de demanda."""
    dist = [x for x in c.get("distritos", []) if x.get("inmuebles")]
    if len(dist) < 4:
        return None
    total = sum(x["inmuebles"] for x in dist)
    top = sorted(dist, key=lambda x: (-x["inmuebles"], x["numero"]))[:3]
    parte = sum(x["inmuebles"] for x in top) / total * 100
    if parte < 3 / len(dist) * 100 * 1.15:   # reparto casi uniforme: la frase no aportaría nada
        return None
    lista = ", ".join(f"{esc(x['nombre'])} ({n(x['inmuebles'])})" for x in top[:-1]) + f" y {esc(top[-1]['nombre'])} ({n(top[-1]['inmuebles'])})"
    return (f"¿Dónde hay más pisos en alquiler? Los distritos con más viviendas alquiladas como residencia habitual y declaradas en el IRPF son "
            f"{lista}: entre los tres reúnen el {d(parte, 0)} % de los {n(total)} pisos alquilados declarados en los {len(dist)} distritos. "
            f"Es un recuento de pisos alquilados, no una medida de cuánta gente busca piso en cada zona.")


def seccion_claves(c, todas, anio, ambito):
    """HTML de la sección. todas = ciudades con página (con alquiler y renta)."""
    parrafos = [p_alquiler_renta(c, todas, ambito), p_ultimo_anio(c, todas, anio), p_rango(c),
                p_provincia(c, todas), p_distritos(c), p_zonas_con_mas_alquiler(c), p_poblacion(c, todas), p_mercado(c, todas)]
    parrafos = [p for p in parrafos if p]
    if not parrafos:
        return ""
    cuerpo = "".join(f"<p>{p}</p>" for p in parrafos)
    return (f'<section id="claves" class="claves"><h2>Qué dicen los datos de {esc(c["nombre"])}</h2>{cuerpo}'
            f'<p class="sub" style="font-size:14px">Texto generado automáticamente a partir de los datos oficiales de esta página '
            f'(Ministerio de Vivienda e INE, {anio}). La mediana es el valor que deja la mitad de las ciudades por encima y la otra mitad por debajo.</p></section>')
