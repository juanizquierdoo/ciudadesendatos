(function(){
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
