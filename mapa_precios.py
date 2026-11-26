"""Mapa de precios de España: /mapa/ (petición de Juan, 24/11/2026; catálogo A, "Mapa nacional interactivo").

Un mapa de toda España por municipios, coloreado por el peso del alquiler, el alquiler al mes o la renta del
hogar. Al acercarse a una zona se cargan los límites de su provincia con más detalle y, en los municipios con
más de un distrito, sus distritos (con los nombres de barrio de la ficha cuando los hay).

    /mapa/                 página (texto fijo + lienzo del mapa)
    /mapa/espana.json      municipios de toda España con poco detalle + sus datos
    /mapa/p/<prov>.json    una provincia con detalle (municipios y distritos) + datos de sus distritos

Datos: los mismos de la web (SERPAVI y ADRH del INE) leídos de municipios_<año>.csv y distritos_<año>.csv,
con la misma regla de fiabilidad que las fichas: menos de 30 inmuebles = sin alquiler; de 30 a 99 = con aviso.
Límites: datos_limpios/mapa/ (los crea preparar_mapa.py con la cartografía de secciones censales del INE).
Si esa carpeta no existe, no hay mapa y la web se genera igual.

Escala de color: la misma que el mapa de distritos de las fichas (ESCALA_MAPA en generar_web.py), para que un
color signifique lo mismo en toda la web.

Todo se dibuja en el navegador (canvas), sin mapas de terceros, sin cookies y sin llamadas a otros sitios.

generar_web.py solo hace dos cosas con este módulo: la tarjeta de la portada (tarjeta()) y generar() en main(),
que devuelve la URL para el sitemap.
"""
import csv
import json

import herramienta_sueldo

SLUG = "mapa"
TITULO = "Mapa del alquiler y la renta en España"
DESC_TARJETA = "Explora el alquiler, la renta y el peso del alquiler en cada municipio y, al acercarte, en cada distrito."
FIABLES = ("ok", "pocos_datos")


def tarjeta(root):
    if not _geo_dir(None).joinpath("espana.json").exists():
        return ""
    return (f'<a class="card" href="{root}{SLUG}/"><strong>{herramienta_sueldo._esc(TITULO)}</strong>'
            f'<span>{herramienta_sueldo._esc(DESC_TARJETA)}</span></a>')


def _geo_dir(gw):
    from config import DATOS
    return DATOS / "mapa"


def _num(v, k=None):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if x != x:
        return None
    return round(x, k) if k is not None else round(x)


def leer_municipios(gw):
    from config import MUNICIPIOS
    out = {}
    for r in csv.DictReader(open(MUNICIPIOS, encoding="utf-8-sig")):
        fiable = r["fiabilidad"] in FIABLES
        out[r["cod_muni"].zfill(5)] = {
            "nombre": r["nombre_muni"], "provincia": r["provincia"], "poblacion": _num(r["poblacion"]),
            "alq": _num(r["alquiler_mes"]) if fiable else None,
            "m2": _num(r["eur_m2"], 2) if fiable else None,
            "pct": _num(r["alquiler_pct_renta"], 1) if fiable else None,
            "renta": _num(r["renta_hogar"]),
            "inm": _num(r["inmuebles"]), "aviso": int(r["fiabilidad"] == "pocos_datos"),
        }
    return out


def leer_distritos(gw, todas):
    from config import DISTRITOS
    nombres = {}
    for c in todas:
        for x in c.get("distritos") or []:
            nombres[x["codigo"]] = herramienta_sueldo.nombre_distrito(x)
    out = {}
    for r in csv.DictReader(open(DISTRITOS, encoding="utf-8-sig")):
        cod = r["codigo"].zfill(7)
        fiable = r["fiabilidad"] in FIABLES
        out[cod] = {
            "nombre": nombres.get(cod) or f"Distrito {int(cod[5:])}",
            "alq": _num(r["alquiler_mes"]) if fiable else None,
            "m2": _num(r["eur_m2"], 2) if fiable else None,
            "pct": _num(r["alquiler_pct_renta"], 1) if fiable else None,
            "renta": _num(r["renta_hogar"]),
            "inm": _num(r["inmuebles"]), "aviso": int(r["fiabilidad"] == "pocos_datos"),
        }
    return out


def _fila(x):
    """[nombre, alquiler, €/m², renta, % alquiler/renta, inmuebles, aviso]"""
    return [x["nombre"], x["alq"], x["m2"], x["renta"], x["pct"], x["inm"], x["aviso"]]


def datos_espana(gw, todas, munis, geo):
    slugs = {c["cod_muni"]: c["slug"] for c in todas}
    out = {}
    for m in geo["municipios"]:
        x = munis.get(m)
        if x is None:
            continue
        out[m] = _fila(x) + [x["provincia"], slugs.get(m, ""), x["poblacion"] or 0]
    return out


def resumen(munis, dist, geo):
    con = [m for m in geo["municipios"] if m in munis]
    return {
        "municipios": len(con),
        "con_alquiler": sum(1 for m in con if munis[m]["alq"] is not None),
        "con_renta": sum(1 for m in con if munis[m]["renta"] is not None),
        "distritos": sum(1 for d in dist if d[:5] in munis),
        "distritos_alquiler": sum(1 for d, x in dist.items() if x["alq"] is not None),
    }


CSS_PAGINA = """<style>
.mp{position:relative;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--surface);margin-top:12px}
.mp canvas{display:block;width:100%;height:min(76vh,620px);touch-action:none;cursor:grab}
.mp canvas.arr{cursor:grabbing}
.mp-zoom{position:absolute;top:10px;right:10px;display:flex;flex-direction:column;gap:6px}
.mp-zoom button{width:38px;height:38px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--ink);font:600 20px/1 inherit;cursor:pointer}
.mp-zoom button:focus-visible{outline:3px solid var(--acc)}
.mp-est{position:absolute;left:10px;bottom:10px;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:3px 8px;font-size:13px;color:var(--muted)}
.mp-bus{position:relative;margin-top:12px;max-width:420px}
.mp-bus input{width:100%;font:inherit;padding:9px 12px;border:1px solid var(--line);border-radius:8px}
.mp-bus ul{list-style:none;margin:4px 0 0;padding:0;position:absolute;z-index:5;left:0;right:0;background:var(--bg);border:1px solid var(--line);border-radius:8px;box-shadow:0 6px 20px rgba(0,0,0,.08)}
.mp-bus ul:empty{display:none}
.mp-bus li button{display:block;width:100%;text-align:left;border:0;background:none;font:inherit;padding:8px 12px;cursor:pointer;color:var(--ink)}
.mp-bus li button:hover,.mp-bus li button:focus-visible{background:var(--tint)}
.mp-bus li span{color:var(--muted);font-size:14px}
.mp-panel{margin-top:12px;border:1px solid var(--line);border-radius:10px;padding:12px 14px;min-height:96px}
.mp-panel h3{margin:0 0 2px;font-size:18px}
.mp-panel p{margin:0 0 8px;color:var(--muted);font-size:14px}
.mp-panel dl{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:6px 16px;margin:0}
.mp-panel dt{font-size:13px;color:var(--muted)}
.mp-panel dd{margin:0;font-weight:600}
</style>"""

JS_PAGINA = r"""<script>
(function(){
var cv=document.getElementById("mp-cv");if(!cv||!cv.getContext||!window.Path2D)return;
var ctx=cv.getContext("2d"),panel=document.getElementById("mp-panel"),est=document.getElementById("mp-est"),mctl=document.getElementById("mp-ctl");
var ESC=__ESCALA__,mk="pct";
var MET=[["pct","Peso del alquiler",function(v){return df(v,0)+" %"},"Alquiler sobre renta del hogar (%)",4],["alq","Alquiler al mes",function(v){return nf(v)+" €"},"Alquiler mediano al mes (€)",1],["renta","Renta del hogar",function(v){return nf(v)+" €"},"Renta neta media del hogar (€ al año)",3]];
function nf(v){return v==null?"—":Math.round(v).toLocaleString("es-ES")}
function df(v,k){return v==null?"—":v.toLocaleString("es-ES",{minimumFractionDigits:k,maximumFractionDigits:k})}
var css=getComputedStyle(document.documentElement);
function hex(v){v=v.trim();if(v.length===4)v="#"+v[1]+v[1]+v[2]+v[2]+v[3]+v[3];return [1,3,5].map(function(i){return parseInt(v.substr(i,2),16)})}
var LO=hex(css.getPropertyValue("--lo")||"#e4edf8"),HI=hex(css.getPropertyValue("--hi")||"#1c4f8f"),
    ND=css.getPropertyValue("--track").trim()||"#e3e8ee",LINE=css.getPropertyValue("--bg").trim()||"#fff",INK=css.getPropertyValue("--ink").trim()||"#17212b";
var NB=24,COL=[];for(var b=0;b<NB;b++){var t=b/(NB-1);COL.push("rgb("+LO.map(function(l,i){return Math.round(l+(HI[i]-l)*t)}).join(",")+")")}
function bucket(v){if(v==null)return -1;var e=ESC[mk],t=Math.max(0,Math.min(1,(v-e[0])/(e[1]-e[0])));return Math.round(t*(NB-1))}
// ---- geometría
function arcos(A,u){return A.map(function(a){var x=0,y=0,o=new Float64Array(a.length*2);for(var i=0;i<a.length;i++){x+=a[i][0];y+=a[i][1];o[2*i]=x*u/1000;o[2*i+1]=-y*u/1000}return o})}
function anillo(refs,A,p,bb){var first=true;refs.forEach(function(r){var a=A[r<0?~r:r],n=a.length/2;for(var j=0;j<n;j++){var k=r<0?n-1-j:j;if(!first&&j===0)continue;var x=a[2*k],y=a[2*k+1];if(first){p.moveTo(x,y);first=false}else p.lineTo(x,y);if(x<bb[0])bb[0]=x;if(y<bb[1])bb[1]=y;if(x>bb[2])bb[2]=x;if(y>bb[3])bb[3]=y}});p.closePath()}
function forma(rs,A){var p=new Path2D(),bb=[1e9,1e9,-1e9,-1e9],big=0,c=null;rs.forEach(function(r){var b0=[1e9,1e9,-1e9,-1e9];anillo(r,A,p,b0);var s=(b0[2]-b0[0])*(b0[3]-b0[1]);if(s>big){big=s;c=b0}for(var i=0;i<2;i++){bb[i]=Math.min(bb[i],b0[i]);bb[i+2]=Math.max(bb[i+2],b0[i+2])}});return {p:p,bb:bb,c:c?[(c[0]+c[2])/2,(c[1]+c[3])/2]:[0,0]}}
function lineas(ids,A){var p=new Path2D();ids.forEach(function(i){var a=A[i];p.moveTo(a[0],a[1]);for(var j=2;j<a.length;j+=2)p.lineTo(a[j],a[j+1])});return p}
var E=null,F=[],PROV={},cargando={},sel=null,W=0,H=0,dpr=1,k=1,tx=0,ty=0,full=null;
function v(f){var d=f.d;if(!d)return null;return {pct:d[4],alq:d[1],renta:d[3]}[mk]}
function init(j){
  var A=arcos(j.arcos,j.unidad);E=j;
  Object.keys(j.municipios).forEach(function(m){var g=forma(j.municipios[m],A),d=j.datos[m];F.push({id:m,p:g.p,bb:g.bb,c:g.c,d:d,prov:m.substr(0,2)})});
  E.lim=lineas(j.limites,A);var c=j.canarias.map(function(x,i){return (i%2?-x:x)*j.unidad/1000});E.can=[c[0],c[3],c[2]-c[0],c[1]-c[3]];
  var bb=[1e9,1e9,-1e9,-1e9];F.forEach(function(f){for(var i=0;i<2;i++){bb[i]=Math.min(bb[i],f.bb[i]);bb[i+2]=Math.max(bb[i+2],f.bb[i+2])}});full=bb;
  E.byId={};F.forEach(function(f){E.byId[f.id]=f});
  agrupar();tam();encajar(full);opciones();
  var h=location.hash.match(/m=(\d{5})/);if(h&&E.byId[h[1]])ir(E.byId[h[1]]);else info(null);
  est.textContent="Pasa el cursor o toca un municipio";
}
var G=[];function agrupar(){G=[];for(var b=-1;b<NB;b++)G.push(new Path2D());F.forEach(function(f){G[bucket(v(f))+1].addPath(f.p)})}
// ---- provincias con detalle
function cargar(p){if(cargando[p])return;cargando[p]=1;fetch("p/"+p+".json").then(function(r){return r.json()}).then(function(j){
  var A=arcos(j.arcos,j.unidad),U=[],mods={};
  Object.keys(j.unidades).forEach(function(id){var g=forma(j.unidades[id],A),m=id.substr(0,5),md=E.byId[m];
    U.push({id:id,m:m,p:g.p,bb:g.bb,c:g.c,dd:id.length>5?(j.datos[id]||null):null,mu:md})});
  // en cada municipio con distritos: ¿todos tienen el dato elegido? si no, se pinta el dato del municipio
  var por={};U.forEach(function(u){if(u.id.length>5)(por[u.m]=por[u.m]||[]).push(u)});
  PROV[p]={U:U,lim:lineas(j.limites,A),todas:lineas(j.arcos.map(function(_,i){return i}),A),por:por};pintar()}).catch(function(){cargando[p]=0})}
function valU(u,P){var m=u.mu&&u.mu.d,ds=P.por[u.m];var idx={pct:4,alq:1,renta:3}[mk];
  if(ds&&ds.every(function(x){return x.dd&&x.dd[idx]!=null}))return {v:u.dd[idx],dis:true};return {v:m?m[idx]:null,dis:false}}
var DET=6;   // píxeles por km a partir de los que se usa el detalle por provincia
function visibles(){var x0=-tx/k,y0=-ty/k,x1=x0+W/k,y1=y0+H/k;return Object.keys(E.provincias).filter(function(p){var b=E.provincias[p],u=E.unidad/1000;
  var bx0=b[0]*u,bx1=b[2]*u,by0=-b[3]*u,by1=-b[1]*u;return bx1>=x0&&bx0<=x1&&by1>=y0&&by0<=y1})}
var pend=0;function pintar(){if(!pend){pend=1;requestAnimationFrame(dib)}}
function dib(){pend=0;if(!E)return;ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,cv.width,cv.height);ctx.setTransform(k*dpr,0,0,k*dpr,tx*dpr,ty*dpr);
  var det=k>=DET,vis=det?visibles():[],hecho={};
  if(det)vis.forEach(function(p){if(PROV[p])hecho[p]=1;else cargar(p)});
  // municipios de toda España (los de provincias con detalle se tapan después)
  for(var b=0;b<=NB;b++){ctx.fillStyle=b?COL[b-1]:ND;ctx.fill(G[b],"evenodd")}
  if(k>2.5){ctx.strokeStyle=LINE;ctx.lineWidth=Math.min(1,(k-2.5)/4)/k;F.forEach(function(f){if(!hecho[f.prov])ctx.stroke(f.p)})}
  Object.keys(hecho).forEach(function(p){var P=PROV[p];
    P.U.forEach(function(u){var r=valU(u,P);u.vis=r;ctx.fillStyle=r.v==null?ND:COL[bucket(r.v)];ctx.fill(u.p,"evenodd")});
    ctx.strokeStyle=LINE;ctx.lineWidth=.6/k;ctx.stroke(P.todas);ctx.lineWidth=1.6/k;ctx.stroke(P.lim)});
  ctx.strokeStyle=INK;ctx.globalAlpha=.55;ctx.lineWidth=(k>DET?1.2:.8)/k;ctx.stroke(E.lim);ctx.globalAlpha=1;
  ctx.strokeStyle=INK;ctx.lineWidth=.8/k;ctx.strokeRect(E.can[0],E.can[1],E.can[2],E.can[3]);
  if(sel){ctx.strokeStyle=INK;ctx.lineWidth=2.5/k;ctx.stroke(sel.p)}
  etiquetas();
}
function etiquetas(){var min=k<1.2?400000:k<2.5?150000:k<DET?50000:k<15?10000:2000,usadas=[];
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.font="600 12px system-ui,-apple-system,Segoe UI,sans-serif";ctx.textAlign="center";ctx.lineJoin="round";
  F.filter(function(f){return f.d&&f.d[9]>=min}).sort(function(a,b){return b.d[9]-a.d[9]}).forEach(function(f){
    var x=f.c[0]*k+tx,y=f.c[1]*k+ty;if(x<0||y<0||x>W||y>H)return;var w=ctx.measureText(f.d[0]).width/2+4;
    if(usadas.some(function(u){return Math.abs(u[0]-x)<u[2]+w&&Math.abs(u[1]-y)<16}))return;usadas.push([x,y,w]);
    ctx.strokeStyle="rgba(255,255,255,.9)";ctx.lineWidth=3;ctx.strokeText(f.d[0],x,y+4);ctx.fillStyle=INK;ctx.fillText(f.d[0],x,y+4)});
}
// ---- tamaño y vista
function tam(){var r=cv.getBoundingClientRect();dpr=Math.min(2,window.devicePixelRatio||1);W=r.width;H=r.height;cv.width=Math.round(W*dpr);cv.height=Math.round(H*dpr)}
function encajar(bb,max){var m=24,kk=Math.min((W-2*m)/(bb[2]-bb[0]),(H-2*m)/(bb[3]-bb[1]));if(max)kk=Math.min(kk,max);k=kk;tx=W/2-k*(bb[0]+bb[2])/2;ty=H/2-k*(bb[1]+bb[3])/2;pintar()}
function zoom(f,cx,cy){var nk=Math.max(kmin(),Math.min(400,k*f));tx=cx-(cx-tx)*nk/k;ty=cy-(cy-ty)*nk/k;k=nk;pintar()}
function kmin(){return Math.min((W-48)/(full[2]-full[0]),(H-48)/(full[3]-full[1]))*.8}
window.addEventListener("resize",function(){if(!E)return;var cx=(W/2-tx)/k,cy=(H/2-ty)/k;tam();tx=W/2-cx*k;ty=H/2-cy*k;pintar()});
// ---- ratón y dedos
var ptr={},mov=0,ini=null;
cv.addEventListener("pointerdown",function(e){cv.setPointerCapture(e.pointerId);ptr[e.pointerId]=[e.offsetX,e.offsetY];mov=0;ini=[e.offsetX,e.offsetY];cv.classList.add("arr")});
cv.addEventListener("pointermove",function(e){var p=ptr[e.pointerId];
  if(!p){if(e.pointerType==="mouse")buscarEn(e.offsetX,e.offsetY,false);return}
  var ids=Object.keys(ptr);
  if(ids.length===1){tx+=e.offsetX-p[0];ty+=e.offsetY-p[1];if(Math.abs(e.offsetX-ini[0])+Math.abs(e.offsetY-ini[1])>6)mov=1;pintar()}
  else if(ids.length===2){var o=ptr[ids[0]===String(e.pointerId)?ids[1]:ids[0]],d0=Math.hypot(p[0]-o[0],p[1]-o[1]),d1=Math.hypot(e.offsetX-o[0],e.offsetY-o[1]);
    if(d0>0)zoom(d1/d0,(e.offsetX+o[0])/2,(e.offsetY+o[1])/2);tx+=(e.offsetX-p[0])/2;ty+=(e.offsetY-p[1])/2;mov=1}
  ptr[e.pointerId]=[e.offsetX,e.offsetY]});
function fuera(e){var era=ptr[e.pointerId];delete ptr[e.pointerId];if(!Object.keys(ptr).length)cv.classList.remove("arr");if(era&&!mov&&e.type==="pointerup")buscarEn(e.offsetX,e.offsetY,true)}
cv.addEventListener("pointerup",fuera);cv.addEventListener("pointercancel",fuera);
cv.addEventListener("wheel",function(e){e.preventDefault();zoom(Math.exp(-e.deltaY*(e.deltaMode?0.05:0.0015)),e.offsetX,e.offsetY)},{passive:false});
cv.addEventListener("dblclick",function(e){zoom(2,e.offsetX,e.offsetY)});
document.getElementById("mp-mas").onclick=function(){zoom(1.6,W/2,H/2)};
document.getElementById("mp-menos").onclick=function(){zoom(1/1.6,W/2,H/2)};
document.getElementById("mp-todo").onclick=function(){encajar(full)};
// ---- qué hay bajo el cursor
function buscarEn(sx,sy,fijar){if(!E)return;var x=(sx-tx)/k,y=(sy-ty)/k,hit=null;
  ctx.setTransform(k*dpr,0,0,k*dpr,tx*dpr,ty*dpr);
  function den(b){return x>=b[0]&&x<=b[2]&&y>=b[1]&&y<=b[3]}
  if(k>=DET)Object.keys(PROV).forEach(function(p){if(hit)return;PROV[p].U.some(function(u){if(den(u.bb)&&ctx.isPointInPath(u.p,sx*dpr,sy*dpr,"evenodd")){hit={u:u,P:PROV[p]};return true}})});
  if(!hit)F.some(function(f){if(den(f.bb)&&ctx.isPointInPath(f.p,sx*dpr,sy*dpr,"evenodd")){hit={f:f};return true}});
  var nuevo=hit?(hit.u&&hit.u.vis&&hit.u.vis.dis?hit.u:(hit.u?hit.u.mu:hit.f)):null;
  if(nuevo!==sel){sel=nuevo;pintar();info(hit)}
  if(fijar&&hit){var m=hit.u?hit.u.m:hit.f.id;history.replaceState(null,"","#m="+m)}}
function fila(t,v){return "<dt>"+t+"</dt><dd>"+v+"</dd>"}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function info(hit){
  if(!hit){panel.innerHTML="<h3>España</h3><p>Pasa el cursor por el mapa (o tócalo) para ver los datos de cada municipio. Acércate para ver los distritos de las ciudades.</p>";return}
  var f=hit.f||hit.u.mu,m=f&&f.d,dis=hit.u&&hit.u.dd&&hit.u.vis&&hit.u.vis.dis,d=dis?hit.u.dd:m,h="";
  if(!m){panel.innerHTML="<h3>Sin datos</h3>";return}
  h+="<h3>"+esc(dis?d[0]:m[0])+"</h3><p>"+(dis?esc(m[0])+" · ":"")+esc(m[7])+(d[6]?" · Pocos inmuebles en la muestra: interpreta el alquiler con cuidado.":"")+(d[1]==null?" · Sin alquiler fiable (menos de 30 inmuebles en la muestra).":"")+"</p><dl>";
  h+=fila("Alquiler mediano",d[1]==null?"—":nf(d[1])+" €/mes")+fila("Por m²",d[2]==null?"—":df(d[2],2)+" €")+fila("Renta del hogar",d[3]==null?"—":nf(d[3])+" €/año")+fila("Alquiler sobre renta",d[4]==null?"—":df(d[4],1)+" %")+fila("Inmuebles en la muestra",nf(d[5]));
  if(dis)h+=fila("Todo "+esc(m[0]),(m[1]==null?"—":nf(m[1])+" €/mes · ")+df(m[4],1)+" %");
  h+="</dl>";if(m[8])h+='<p style="margin:10px 0 0"><a href="../'+m[8]+'/">Ficha completa de '+esc(m[0])+" →</a></p>";
  panel.innerHTML=h}
function ir(f){sel=f;var b=f.bb,w=Math.max(b[2]-b[0],12),hh=Math.max(b[3]-b[1],12),cx=(b[0]+b[2])/2,cy=(b[1]+b[3])/2;encajar([cx-w,cy-hh,cx+w,cy+hh],60);info({f:f})}
// ---- buscador de municipios
var q=document.getElementById("mp-q"),ul=document.getElementById("mp-res");
function norm(s){return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g,"").replace(/[’']/g,"")}
q.addEventListener("input",function(){var s=norm(q.value.trim());ul.innerHTML="";if(s.length<2||!E)return;
  F.filter(function(f){return f.d&&norm(f.d[0]).indexOf(s)>-1}).sort(function(a,b){return (norm(b.d[0]).indexOf(s)===0)-(norm(a.d[0]).indexOf(s)===0)||b.d[9]-a.d[9]}).slice(0,8).forEach(function(f){
    var li=document.createElement("li"),bt=document.createElement("button");bt.type="button";bt.innerHTML=esc(f.d[0])+" <span>· "+esc(f.d[7])+"</span>";
    bt.onclick=function(){ul.innerHTML="";q.value=f.d[0];ir(f);history.replaceState(null,"","#m="+f.id)};li.appendChild(bt);ul.appendChild(li)})});
q.addEventListener("keydown",function(e){if(e.key==="Enter"){e.preventDefault();var b=ul.querySelector("button");if(b)b.click()}});
// ---- selector de dato y leyenda
function opciones(){MET.forEach(function(m){var b=document.createElement("button");b.type="button";b.textContent=m[1];b.dataset.k=m[0];b.onclick=function(){mk=m[0];agrupar();ley();pintar()};mctl.appendChild(b)});ley()}
function ley(){var met=MET.filter(function(m){return m[0]===mk})[0],f=met[2];document.getElementById("mp-lnom").textContent=met[3];
  document.getElementById("mp-lmin").textContent="≤ "+f(ESC[mk][0]);document.getElementById("mp-lmax").textContent="≥ "+f(ESC[mk][1]);
  mctl.querySelectorAll("button").forEach(function(b){b.setAttribute("aria-pressed",String(b.dataset.k===mk))})}
fetch("espana.json").then(function(r){return r.json()}).then(init).catch(function(){est.textContent="No se ha podido cargar el mapa."});
})();
</script>"""


def pagina(gw, todas, r):
    root = "../"
    titulo_a = f"{TITULO} por municipios y barrios ({gw.ANIO})"
    lead = ("Explora en un mapa el alquiler mediano, la renta de los hogares y el peso del alquiler en "
            f"{gw.n(r['municipios'])} municipios de España. Acércate a una ciudad para ver sus distritos y barrios. "
            "Datos oficiales del Ministerio de Vivienda (SERPAVI) y del INE.")
    mapa = ('<div class="ctl" id="mp-ctl" role="group" aria-label="Dato del mapa"><span>Colorear por</span></div>'
            '<div class="mp-bus" role="search"><label class="sub" for="mp-q">Busca un municipio</label>'
            '<input id="mp-q" type="search" autocomplete="off" placeholder="Por ejemplo, Salamanca"><ul id="mp-res"></ul></div>'
            '<div class="mp"><canvas id="mp-cv" role="img" aria-label="Mapa de España por municipios coloreado según el dato elegido"></canvas>'
            '<div class="mp-zoom"><button type="button" id="mp-mas" aria-label="Acercar">+</button>'
            '<button type="button" id="mp-menos" aria-label="Alejar">−</button>'
            '<button type="button" id="mp-todo" aria-label="Ver toda España" style="font-size:14px">⤢</button></div>'
            '<span class="mp-est" id="mp-est" aria-live="polite">Cargando el mapa…</span></div>'
            '<div class="legend"><b id="mp-lnom"></b><span id="mp-lmin"></span><i></i><span id="mp-lmax"></span>'
            '<span style="display:inline-flex;align-items:center;gap:6px"><i style="flex:none;width:18px;max-width:18px;background:var(--track)"></i>Sin dato fiable</span></div>'
            '<div class="mp-panel" id="mp-panel" aria-live="polite"></div>'
            '<noscript><p class="sub">El mapa necesita JavaScript. Los datos de cada ciudad están también en su ficha.</p></noscript>')
    claves = (f"<p>De los {gw.n(r['municipios'])} municipios del mapa, {gw.n(r['con_renta'])} tienen dato de renta del hogar y "
              f"{gw.n(r['con_alquiler'])} tienen suficientes pisos alquilados en la muestra (30 o más) para dar un alquiler mediano fiable. "
              "En el resto, sobre todo pueblos pequeños, el mapa los deja en gris: no inventamos ni estimamos el dato.</p>"
              f"<p>Al acercarte aparecen los distritos de los municipios que tienen más de uno ({gw.n(r['distritos'])} distritos, "
              f"{gw.n(r['distritos_alquiler'])} con alquiler fiable). Si algún distrito de un municipio no tiene el dato elegido, "
              "ese municipio se pinta entero con su cifra general, para no mezclar escalas.</p>"
              "<p>Los colores usan la misma escala que los mapas de distritos de las fichas: el mismo color significa lo mismo en toda la web. "
              "Los valores por encima o por debajo de la escala toman el color del extremo.</p>")
    met = ('<section id="metodologia"><h2>Cómo se ha hecho</h2><ul class="notes">'
           "<li><strong>Alquiler:</strong> mediana de los alquileres de vivienda habitual declarados en el IRPF (SERPAVI, Ministerio de Vivienda), "
           f"solo pisos, datos de {gw.ANIO}. Son contratos vigentes, no anuncios: por eso suele ser más bajo que lo que piden hoy los portales inmobiliarios. "
           "Con menos de 30 inmuebles en la muestra no se muestra; de 30 a 99 se avisa.</li>"
           "<li><strong>Renta del hogar:</strong> renta neta media por hogar del Atlas de Distribución de Renta de los Hogares del INE.</li>"
           "<li><strong>Peso del alquiler:</strong> alquiler mediano × 12 / renta neta media del hogar. Es una estimación propia y aproximada: "
           "compara la mediana de quienes alquilan con la media de todos los hogares.</li>"
           "<li><strong>Límites:</strong> Elaboración propia con datos extraídos del sitio web del INE: www.ine.es (cartografía de secciones censales, "
           "unida por municipio y por distrito y simplificada para que el mapa pese poco). Canarias aparece desplazada en un recuadro.</li>"
           "<li><strong>Privacidad:</strong> el mapa se dibuja en tu navegador, sin mapas de otras empresas, sin cookies y sin enviar nada a ningún sitio.</li>"
           "</ul></section>")
    cuerpo = (gw.cabecera(root, [("#explorar", "Mapa"), ("#claves", "Cómo leerlo"), ("#metodologia", "Metodología")]) +
              f'<div class="hero"><div>{gw.migas_html(root, [("Inicio", "")], TITULO)}<h1>{gw.esc(TITULO)}</h1>'
              f'<p class="lead">{lead}</p></div></div><main>{CSS_PAGINA}'
              f'<section id="explorar"><h2>Explora el mapa</h2>{mapa}{gw.aviso_turistico()}</section>'
              f'<section id="claves"><h2>Cómo leer el mapa</h2>{claves}</section>{met}'
              f'<section><h2>Relacionado</h2><ul class="lnk"><li><a href="{root}{herramienta_sueldo.SLUG}/">¿Dónde puedo vivir con mi sueldo?</a></li>'
              f'<li><a href="{root}comparar-ciudades/">Compara ciudades</a></li>'
              f'<li><a href="{root}comunidades/">Alquiler por comunidad autónoma</a></li></ul></section>{gw.pie(root)}</main>')
    desc = ("Mapa interactivo del alquiler, la renta de los hogares y el peso del alquiler en cada municipio de España, "
            f"con detalle por distritos y barrios. Datos oficiales de {gw.ANIO}.")
    ld = [gw.dataset(f"{TITULO} ({gw.ANIO})", desc, f"{SLUG}/", "España",
                     ["Alquiler mensual mediano por municipio y distrito", "Renta neta media por hogar", "Alquiler sobre renta"]),
          gw.migas([("Inicio", ""), (TITULO, f"{SLUG}/")])]
    js = JS_PAGINA.replace("__ESCALA__", json.dumps(gw.ESCALA_MAPA))
    return gw.head(titulo_a, desc, root, f"{SLUG}/", ld) + cuerpo + gw.fin(root, js)


def _json(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def generar(gw, todas):
    """Escribe web/mapa/ (página y datos) y devuelve su URL para el sitemap. Sin límites, no hace nada."""
    geo_dir = _geo_dir(gw)
    if not (geo_dir / "espana.json").exists():
        print("AVISO: falta datos_limpios/mapa/espana.json (python preparar_mapa.py). Sin mapa de España.")
        return []
    geo = json.loads((geo_dir / "espana.json").read_text(encoding="utf-8"))
    munis = leer_municipios(gw)
    dist = leer_distritos(gw, todas)
    geo["datos"] = datos_espana(gw, todas, munis, geo)
    gw.escribir(gw.WEB / SLUG / "espana.json", _json(geo))
    for f in sorted((geo_dir / "p").glob("*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        p["datos"] = {u: _fila(dist[u]) for u in p["unidades"] if len(u) == 7 and u in dist}
        gw.escribir(gw.WEB / SLUG / "p" / f.name, _json(p))
    gw.escribir(gw.WEB / SLUG / "index.html", pagina(gw, todas, resumen(munis, dist, geo)))
    return [f"{SLUG}/"]
