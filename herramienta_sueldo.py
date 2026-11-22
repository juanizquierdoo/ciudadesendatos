"""Herramienta "¿Dónde puedo vivir con mi sueldo?" (Fase 2, funcionalidad 1 del ranking de INFORME_FASE0.md).

Escribes tus ingresos netos al mes y el porcentaje máximo que quieres dedicar al alquiler,
y la página te dice en qué ciudades, y en qué distritos y barrios de cada una, el alquiler
mediano de un piso entra en ese presupuesto.

    /donde-vivir-con-mi-sueldo/

Solo usa datos que ya están en ciudades_nivel1.json (alquiler SERPAVI y renta INE): no hay
datos nuevos ni estimaciones. El cálculo se hace en el navegador con los datos incrustados en
la página (sin cookies, sin llamadas a otros sitios). Sin JavaScript se ve igual la parte fija:
la tabla de ingresos de referencia y el texto "Qué dicen los datos", calculados aquí en Python.

Los distritos siguen la misma regla que la ficha: menos de 30 inmuebles = no se usa su alquiler;
de 30 a 99 se marca con *.

generar_web.py solo hace dos cosas con este módulo: añade la tarjeta a la portada (tarjeta())
y llama a generar() en main(), que devuelve la URL para el sitemap.
"""
import json
import re

SLUG = "donde-vivir-con-mi-sueldo"
TITULO = "¿Dónde puedo vivir con mi sueldo?"
DESC_TARJETA = "Escribe tus ingresos y mira en qué ciudades y barrios el alquiler entra en tu presupuesto."
PCT_DEFECTO = 30                  # regla orientativa: que el alquiler no pase del 30 % de los ingresos netos
PCTS = (25, 30, 35, 40)
SUELDO_DEFECTO = 1500
INGRESOS_REF = (1000, 1200, 1500, 1800, 2000, 2500, 3000)   # filas de la tabla fija (euros netos al mes)


def tarjeta(root):
    return (f'<a class="card" href="{root}{SLUG}/"><strong>{_esc(TITULO)}</strong>'
            f'<span>{_esc(DESC_TARJETA)}</span></a>')


def _esc(s):
    import html
    return html.escape(str(s).replace("'", "’"), quote=True)


_CP = re.compile(r"\s*·\s*CP\s[\d\s,y]+$")


def nombre_distrito(x):
    """Nombre que se entiende a simple vista: nunca un código postal.

    Si el nombre del JSON ya no lleva CP, se usa tal cual. Si lo lleva, se sustituye por los
    núcleos de población o, si no hay, por las dos calles principales del callejero del INE."""
    nom = x["nombre"]
    if not _CP.search(nom):
        return nom
    base = _CP.sub("", nom)
    z = x.get("zona") or {}
    if z.get("nucleos"):
        return f"{base} · {_y(z['nucleos'][:2])}"
    if z.get("calles"):
        return f"{base} · zona de {_y(z['calles'][:2])}"
    return base


def _y(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


def distritos_validos(c):
    """Distritos con alquiler publicable (misma regla que la ficha): 30 inmuebles o más."""
    return [x for x in c.get("distritos") or []
            if x["fiabilidad"] in ("ok", "pocos_datos") and x.get("alquiler_mes") is not None]


def datos_js(gw, todas):
    """Datos incrustados en la página. Por ciudad: [nombre, slug, provincia, cod_ccaa, alquiler, distritos].
    Por distrito: [número, nombre, alquiler, 1 si hay pocos datos, barrios]."""
    out = []
    for c in sorted(todas, key=lambda c: c["nombre"]):
        ds = [[x["numero"], nombre_distrito(x), round(x["alquiler_mes"], 2), int(x["fiabilidad"] == "pocos_datos"),
               x.get("barrios") or []] for x in distritos_validos(c)]
        out.append([c["nombre"], c["slug"], c["provincia"], gw.PROV_CCAA.get(c["cod_muni"][:2], ""),
                    round(c["alquiler_mes"], 2), ds])
    return out


def resumen(todas, ingresos, pct=PCT_DEFECTO):
    """Ciudades y distritos cuyo alquiler mediano no pasa de ingresos x pct. Lo usan la tabla fija y los tests."""
    tope = ingresos * pct / 100
    ciudades = [c for c in todas if c["alquiler_mes"] <= tope]
    ds = [(c, x) for c in todas for x in distritos_validos(c)]
    ds_ok = [(c, x) for c, x in ds if x["alquiler_mes"] <= tope]
    solo_distritos = [c for c in todas if c["alquiler_mes"] > tope and any(x["alquiler_mes"] <= tope for x in distritos_validos(c))]
    return {"tope": tope, "ciudades": ciudades, "n_distritos": len(ds), "distritos": ds_ok, "solo_distritos": solo_distritos}


def _claves(gw, todas):
    N = len(todas)
    orden = sorted(todas, key=lambda c: (c["alquiler_mes"], c["nombre"]))
    u = PCT_DEFECTO / 100
    out = []
    r1 = resumen(todas, 1000)
    if r1["ciudades"]:
        ej = _y([gw.esc(c["nombre"]) for c in sorted(r1["ciudades"], key=lambda c: c["alquiler_mes"])[:4]])
        out.append(f"Con 1.000 € netos al mes y sin pasar del {PCT_DEFECTO} %, el presupuesto para el alquiler es de {gw.n(r1['tope'])} €. "
                   f"El alquiler mediano de un piso solo entra en {len(r1['ciudades'])} de las {N} ciudades, como {ej}, "
                   f"y en {len(r1['distritos'])} de los {r1['n_distritos']} distritos con dato.")
    else:
        out.append(f"Con 1.000 € netos al mes y sin pasar del {PCT_DEFECTO} %, el presupuesto para el alquiler es de {gw.n(r1['tope'])} €, y el alquiler "
                   f"mediano de un piso no entra en ninguna de las {N} ciudades. La más asequible es {gw.esc(orden[0]['nombre'])}, "
                   f"con {gw.n(orden[0]['alquiler_mes'])} € al mes. Sí entra en {len(r1['distritos'])} de los {r1['n_distritos']} distritos con dato"
                   + (": " + _y([f"{gw.esc(nombre_distrito(x))} ({gw.esc(c['nombre'])}, {gw.n(x['alquiler_mes'])} €)" for c, x in r1["distritos"]]) + "."
                      if 0 < len(r1["distritos"]) <= 3 else "."))
    r15 = resumen(todas, 1500)
    out.append(f"Con 1.500 € netos ({gw.n(r15['tope'])} € para el alquiler) ya entra en {len(r15['ciudades'])} ciudades y en {len(r15['distritos'])} distritos. "
               + (f"Además, en {len(r15['solo_distritos'])} ciudades donde el alquiler mediano se pasa del presupuesto hay al menos "
                  "un distrito donde no se pasa: mirar por barrios cambia la respuesta." if r15["solo_distritos"] else ""))
    # ingresos para que entren todas
    max_c = orden[-1]
    out.append(f"Para que el alquiler mediano entre en todas las ciudades hacen falta {gw.n(max_c['alquiler_mes'] / u)} € netos al mes, "
               f"por {gw.esc(max_c['nombre'])}, la más cara ({gw.n(max_c['alquiler_mes'])} € de alquiler mediano).")
    # Madrid y Barcelona por distritos, si están
    for cod in ("28079", "08019"):
        c = next((c for c in todas if c["cod_muni"] == cod), None)
        if not c:
            continue
        ds = sorted(distritos_validos(c), key=lambda x: x["alquiler_mes"])
        if len(ds) >= 4:
            b = ds[0]
            out.append(f"En {gw.esc(c['nombre'])}, el alquiler mediano de la ciudad pide unos {gw.n(c['alquiler_mes'] / u)} € netos al mes, "
                       f"pero en su distrito más asequible, {gw.esc(nombre_distrito(b))}, bastan unos {gw.n(b['alquiler_mes'] / u)} € "
                       f"({gw.n(b['alquiler_mes'])} € de alquiler mediano).")
    out.append("Recuerda que son contratos vigentes declarados a Hacienda, no anuncios: un piso que se alquile hoy suele costar más. "
               "Úsalo para comparar zonas entre sí, no como el precio que vas a encontrar.")
    return out


def _tabla_ref(gw, todas):
    N = len(todas)
    filas = ""
    for ing in INGRESOS_REF:
        r = resumen(todas, ing)
        filas += (f'<tr><th scope="row" data-v="{ing}">{gw.n(ing)} €</th><td data-v="{r["tope"]:.0f}">{gw.n(r["tope"])} €</td>'
                  f'<td data-v="{len(r["ciudades"])}">{len(r["ciudades"])} de {N}</td>'
                  f'<td data-v="{len(r["distritos"])}">{len(r["distritos"])} de {r["n_distritos"]}</td></tr>')
    return (f'<h2>Hasta dónde llega cada sueldo</h2><p class="sub">Ciudades y distritos donde el alquiler mediano de un piso no pasa del '
            f'{PCT_DEFECTO} % de los ingresos netos.</p><div class="wrap"><table><thead><tr><th>Ingresos netos al mes</th>'
            f'<th>Presupuesto para el alquiler ({PCT_DEFECTO} %)</th><th>Ciudades donde entra</th><th>Distritos donde entra</th>'
            f'</tr></thead><tbody>{filas}</tbody></table></div>')


CSS_PAGINA = """<style>
.calc{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:18px 0 6px}
@media (max-width:640px){.calc{grid-template-columns:1fr}}
.calc label{display:flex;flex-direction:column;gap:6px;font-weight:600;font-size:15px}
.calc input,.calc select{font:inherit;font-weight:400;padding:10px 12px;border:1px solid var(--line);border-radius:6px;background:#fff;color:var(--ink);width:100%}
.calc input:focus,.calc select:focus{outline:2px solid var(--acc);outline-offset:1px}
.res-sum{font-size:18px;margin:16px 0 4px}
.res-sum strong{color:var(--acc)}
.res{list-style:none;padding:0;margin:12px 0 0;border-top:3px solid var(--ink)}
.res>li{max-width:none;padding:12px 0;border-bottom:1px solid var(--line)}
.res .fila{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 12px}
.res .fila a{font-weight:700;color:var(--ink);text-decoration:none}
.res .fila a::after{content:" ›";color:var(--acc)}
.res .fila a:hover{text-decoration:underline}
.res .prov{color:var(--muted);font-size:15px}
.res .cifra{margin-left:auto;font-variant-numeric:tabular-nums;white-space:nowrap}
.res .et{display:inline-block;font-size:13px;padding:1px 8px;border-radius:10px;background:var(--tint);color:var(--acc);font-weight:600}
.res .et.parcial{background:#fdf3e1;color:#7a4e0e}
.res details{margin-top:6px}
.res summary{cursor:pointer;color:var(--acc);font-size:15px}
.res details ul{list-style:none;padding:0;margin:8px 0 0 0}
.res details li{display:flex;gap:12px;padding:5px 0;border-top:1px dashed var(--line);font-size:15px}
.res details li a{color:var(--ink)}
.res details li .bar{color:var(--muted);display:block;font-size:13px}
.res details li .cifra{margin-left:auto}
.mas{margin:14px 0 0;font:inherit;padding:8px 14px;border:1px solid var(--acc);color:var(--acc);background:#fff;border-radius:6px;cursor:pointer}
</style>"""


JS_PAGINA = r"""<script>(function(){
var D=JSON.parse(document.getElementById("sueldo-datos").textContent);
var fs=document.getElementById("f-sueldo"),fp=document.getElementById("f-pct"),fc=document.getElementById("f-ccaa"),
    out=document.getElementById("res"),sum=document.getElementById("res-sum"),mas=document.getElementById("mas"),LIM=40,ver=LIM;
function nf(x){return String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g,".")}
function el(t,c,txt){var e=document.createElement(t);if(c)e.className=c;if(txt!=null)e.textContent=txt;return e}
var q=new URLSearchParams(location.search);
if(q.get("sueldo")&&+q.get("sueldo")>0)fs.value=+q.get("sueldo");
if(q.get("pct")&&fp.querySelector('option[value="'+q.get("pct")+'"]'))fp.value=q.get("pct");
if(q.get("ccaa")&&fc.querySelector('option[value="'+q.get("ccaa")+'"]'))fc.value=q.get("ccaa");
function calc(reset){
  if(reset)ver=LIM;
  var s=parseFloat(String(fs.value).replace(",","."))||0,p=+fp.value,cc=fc.value,tope=s*p/100;
  var p2=new URLSearchParams();if(s>0)p2.set("sueldo",Math.round(s));if(p!==30)p2.set("pct",p);if(cc)p2.set("ccaa",cc);
  try{history.replaceState(null,"",location.pathname+(p2.toString()?"?"+p2:""))}catch(e){}
  out.innerHTML="";
  if(!(s>0)){sum.textContent="Escribe tus ingresos netos al mes para ver el resultado.";mas.hidden=true;return}
  var base=D.filter(function(c){return !cc||c[3]===cc}),filas=[],nd=0,ndt=0;
  base.forEach(function(c){var ok=c[5].filter(function(d){return d[2]<=tope});nd+=ok.length;ndt+=c[5].length;
    if(c[4]<=tope||ok.length)filas.push([c,ok])});
  var nc=filas.filter(function(f){return f[0][4]<=tope}).length;
  sum.innerHTML="";
  sum.appendChild(document.createTextNode("Con "+nf(s)+" € netos al mes y un "+p+" %, tu presupuesto para el alquiler es de "));
  sum.appendChild(el("strong",null,nf(tope)+" €"));
  sum.appendChild(document.createTextNode(". El alquiler mediano entra en "));
  sum.appendChild(el("strong",null,nc+" de "+base.length+" ciudades"));
  sum.appendChild(document.createTextNode(" y en "+nd+" de "+ndt+" distritos."));
  filas.sort(function(a,b){var x=a[0][4]<=tope,y=b[0][4]<=tope;if(x!==y)return x?-1:1;return b[0][4]-a[0][4]});
  if(!filas.length){
    var cer=base.slice().sort(function(a,b){return a[4]-b[4]}).slice(0,5),li=el("li");
    li.appendChild(el("p",null,"No hay ninguna ciudad ni distrito dentro de ese presupuesto. Las más cercanas:"));
    var ul=el("ul","lnk");cer.forEach(function(c){var l=el("li"),a=el("a",null,c[0]);a.href="../"+c[1]+"/";l.appendChild(a);
      l.appendChild(el("span",null," "+nf(c[4])+" € al mes; hacen falta unos "+nf(c[4]*100/p)+" € netos"));ul.appendChild(l)});
    li.appendChild(ul);out.appendChild(li);mas.hidden=true;return}
  filas.slice(0,ver).forEach(function(f){
    var c=f[0],ok=f[1],li=el("li"),fi=el("div","fila"),a=el("a",null,c[0]);a.href="../"+c[1]+"/";
    fi.appendChild(a);fi.appendChild(el("span","prov",c[2]));
    fi.appendChild(el("span","et"+(c[4]<=tope?"":" parcial"),c[4]<=tope?"Entra":"Solo en algunos distritos"));
    fi.appendChild(el("span","cifra",nf(c[4])+" € · "+Math.round(c[4]*100/s)+" % de tus ingresos"));li.appendChild(fi);
    if(c[5].length){var dt=el("details"),sm=el("summary",null,ok.length+" de "+c[5].length+" distritos dentro de tu presupuesto");dt.appendChild(sm);
      var ul=el("ul");ok.slice().sort(function(a,b){return a[2]-b[2]}).forEach(function(d){
        var l=el("li"),w=el("span"),a2=el("a",null,d[1]);a2.href="../"+c[1]+"/#d"+d[0];w.appendChild(a2);
        if(d[4].length>3||(d[4].length&&d[1].indexOf(d[4][0])<0))w.appendChild(el("span","bar","Barrios: "+d[4].slice(0,6).join(", ")));
        l.appendChild(w);l.appendChild(el("span","cifra",nf(d[2])+" €"+(d[3]?"*":"")));ul.appendChild(l)});
      dt.appendChild(ul);li.appendChild(dt)}
    out.appendChild(li)});
  mas.hidden=filas.length<=ver;mas.textContent="Ver "+Math.min(LIM,filas.length-ver)+" más (de "+(filas.length-ver)+")";
}
fs.addEventListener("input",function(){calc(true)});fp.addEventListener("change",function(){calc(true)});fc.addEventListener("change",function(){calc(true)});
mas.addEventListener("click",function(){ver+=LIM;calc(false)});
document.getElementById("calc").addEventListener("submit",function(e){e.preventDefault()});
calc(true);
})();</script>"""


def pagina(gw, todas):
    root = "../"
    N = len(todas)
    titulo_a = f"{TITULO} Ciudades y barrios ({gw.ANIO})"
    datos = json.dumps(datos_js(gw, todas), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    ccaa = sorted({gw.PROV_CCAA.get(c["cod_muni"][:2], "") for c in todas} - {""},
                  key=lambda k: gw.COMUNIDADES[k]["comun"] if k in gw.COMUNIDADES else k)
    opc_ccaa = '<option value="">Toda España</option>' + "".join(
        f'<option value="{k}">{gw.esc(gw.COMUNIDADES[k]["comun"])}</option>' for k in ccaa if k in gw.COMUNIDADES)
    opc_pct = "".join(f'<option value="{p}"{" selected" if p == PCT_DEFECTO else ""}>{p} %</option>' for p in PCTS)
    r = resumen(todas, SUELDO_DEFECTO)
    form = (f'<form id="calc" class="calc" role="search" aria-label="Calcula dónde puedes vivir">'
            f'<label for="f-sueldo">Ingresos netos al mes (€)<input aria-describedby="f-ayuda" id="f-sueldo" type="number" inputmode="numeric" min="0" step="50" value="{SUELDO_DEFECTO}"></label>'
            f'<label for="f-pct">Máximo para el alquiler<select id="f-pct">{opc_pct}</select></label>'
            f'<label for="f-ccaa">Dónde buscar<select id="f-ccaa">{opc_ccaa}</select></label></form>'
            f'<p class="res-sum" id="res-sum" aria-live="polite">Con {gw.n(SUELDO_DEFECTO)} € netos al mes y un {PCT_DEFECTO} %, '
            f'tu presupuesto para el alquiler es de <strong>{gw.n(r["tope"])} €</strong>. El alquiler mediano entra en '
            f'<strong>{len(r["ciudades"])} de {N} ciudades</strong> y en {len(r["distritos"])} de {r["n_distritos"]} distritos.</p>'
            '<p class="sub" id="f-ayuda" style="margin:0">Si sois dos con sueldo, suma los dos: el alquiler es para el piso entero.</p>'
            '<noscript><p class="sub">Activa JavaScript para calcularlo con tus ingresos. Más abajo tienes la tabla con varios sueldos de referencia.</p></noscript>'
            '<ul class="res" id="res"></ul><button type="button" class="mas" id="mas" hidden>Ver más</button>'
            '<p class="sub" style="margin-top:10px">* Pocos inmuebles en la muestra (entre 30 y 99): interpreta la cifra con cuidado. '
            'Los distritos con menos de 30 no se tienen en cuenta.</p>'
            f'<script type="application/json" id="sueldo-datos">{datos}</script>')
    lead = (f"Escribe lo que entra en casa cada mes y el máximo que quieres dedicar al alquiler. Te decimos en cuáles de las {N} "
            "ciudades de más de 50.000 habitantes, y en qué distritos y barrios, el alquiler mediano de un piso entra en tu presupuesto. "
            "Con datos oficiales del Ministerio de Vivienda (SERPAVI) y del INE.")
    met = ('<section id="metodologia"><h2>Cómo se ha calculado</h2><ul class="notes">'
           "<li><strong>Alquiler:</strong> mediana de los alquileres de vivienda habitual declarados en el IRPF (SERPAVI, Ministerio de Vivienda), "
           f"solo pisos, datos de {gw.ANIO}. Son contratos vigentes, no anuncios: por eso suele ser más bajo que lo que piden hoy los portales inmobiliarios.</li>"
           "<li><strong>Presupuesto:</strong> tus ingresos netos al mes × el porcentaje elegido. Un piso «entra» si su alquiler mediano no pasa de ese presupuesto. "
           f"La regla del {PCT_DEFECTO} % es orientativa, no un umbral oficial, y no cuenta comunidad, suministros ni fianza.</li>"
           "<li><strong>Mediana:</strong> la mitad de los pisos alquilados de la zona cuesta menos y la otra mitad más. Que el alquiler mediano no entre "
           "no significa que no haya ningún piso a tu alcance, y al revés.</li>"
           "<li><strong>Distritos:</strong> divisiones del INE dentro de cada ciudad. Solo se usan los que tienen 30 inmuebles o más en la muestra "
           "(de 30 a 99, marcados con *). Los barrios de cada distrito vienen de la ficha de la ciudad, con su fuente.</li>"
           "<li><strong>Privacidad:</strong> el cálculo se hace en tu navegador. Lo que escribes no se envía ni se guarda en ningún sitio.</li>"
           "</ul></section>")
    cuerpo = (gw.cabecera(root, [("#calculadora", "Calculadora"), ("#claves", "Claves"), ("#tabla", "Tabla")]) +
              f'<div class="hero"><div>{gw.migas_html(root, [("Inicio", "")], TITULO)}<h1>{gw.esc(TITULO)}</h1>'
              f'<p class="lead">{lead}</p></div></div><main>{CSS_PAGINA}'
              f'<section id="calculadora"><h2>Calcula dónde te llega</h2>{form}{gw.aviso_turistico()}</section>'
              f'<section id="claves"><h2>Qué dicen los datos</h2>{"".join(f"<p>{p}</p>" for p in _claves(gw, todas))}</section>'
              f'<section id="tabla">{_tabla_ref(gw, todas)}</section>{met}'
              f'<section><h2>Relacionado</h2><ul class="lnk"><li><a href="{root}rankings/sueldo-para-vivir-de-alquiler/">Sueldo necesario para alquilar en cada ciudad</a></li>'
              f'<li><a href="{root}rankings/barrios-con-el-alquiler-mas-caro/">Barrios y distritos con el alquiler más caro de España</a></li>'
              f'<li><a href="{root}comunidades/">Alquiler por comunidad autónoma</a></li></ul></section>{gw.pie(root)}</main>')
    desc = (f"Escribe tus ingresos netos y mira en qué ciudades y barrios de España el alquiler mediano no pasa del {PCT_DEFECTO} %. "
            f"Datos oficiales de {gw.ANIO}.")
    ld = [gw.dataset(f"{TITULO} ({gw.ANIO})", desc, f"{SLUG}/", "España",
                     ["Alquiler mensual mediano por ciudad", "Alquiler mensual mediano por distrito"]),
          gw.migas([("Inicio", ""), (TITULO, f"{SLUG}/")])]
    return gw.head(titulo_a, desc, root, f"{SLUG}/", ld) + cuerpo + gw.fin(root, JS_PAGINA)


def generar(gw, todas):
    """Escribe web/<SLUG>/index.html y devuelve su URL para el sitemap."""
    gw.escribir(gw.WEB / SLUG / "index.html", pagina(gw, todas))
    return [f"{SLUG}/"]
