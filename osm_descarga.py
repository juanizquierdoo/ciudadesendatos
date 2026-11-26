"""Crea datos_municipales/osm/descargar_osm.html: una página que descarga de OpenStreetMap (Overpass API)
las calles (con su punto central) y los barrios (polígonos y puntos) de las ciudades con distritos sin barrios.
Juan la abre con doble clic, pulsa el botón y mueve los 4 archivos de Descargas a datos_municipales/osm.
Datos: © colaboradores de OpenStreetMap, licencia ODbL."""
import json
from config import DATOS

YA_BAJADOS = {"osm_calles_1.csv", "osm_barrios_1.json", "osm_barrios_2.json", "osm_barrios_3.json", "osm_barrios_4.json",
              "osm_barrios_5.json", "osm_calles_5.csv", "osm_calles_6.csv", "osm_barrios_7.json", "osm_calles_8.csv", "osm_barrios_8.json",
              "osm_calles_2.csv", "osm_calles_3.csv", "osm_barrios_6.json"}
PARTIR = {"osm_calles_4.csv", "osm_calles_7.csv"}   # fallaron 2 veces: se piden en trozos de 5 ciudades (4a, 4b, 4c...)
HECHAS = {"50297", "35016", "47186"}   # con fuente oficial o en otro hilo (Valladolid)
# Sevilla y Málaga se bajan también, solo para comprobar el método contra sus barrios oficiales.
# Solo calles, una ciudad por archivo, para el mapa esquemático (mapa_distritos.py). Sus barrios oficiales no se tocan:
# zonas_osm.py conserva las filas que no vienen de OpenStreetMap.
SOLO_CALLES = {"osm_calles_zaragoza.csv": "50297", "osm_calles_valladolid.csv": "47186", "osm_calles_laspalmas.csv": "35016"}
SERVIDORES = ["https://overpass-api.de/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]


def ciudades():
    d = json.load(open(DATOS / "ciudades_nivel1.json", encoding="utf-8"))["ciudades"]
    return [c["cod_muni"] for c in sorted(d, key=lambda c: -c["poblacion"]) if len(c["distritos"]) >= 2 and c["cod_muni"] not in HECHAS]


def consultas(cods):
    a = f'area["boundary"="administrative"]["admin_level"="8"]["ine:municipio"~"^({"|".join(cods)})$"]->.ms;'
    calles = ('[out:csv(::type,"ine:municipio",name,::lat,::lon;true;"|")][timeout:900][maxsize:1073741824];' + a +
              'foreach.ms->.m(.m out tags;way(area.m)["highway"]["name"];out center;);')
    barrios = ('[out:json][timeout:900][maxsize:1073741824];' + a +
               'foreach.ms->.m(.m out tags;(rel(area.m)["boundary"="administrative"]["admin_level"~"^(9|10)$"];'
               'rel(area.m)["place"~"^(suburb|neighbourhood|quarter)$"];way(area.m)["place"~"^(suburb|neighbourhood|quarter)$"];);'
               'out geom;node(area.m)["place"~"^(suburb|neighbourhood|quarter)$"];out;);')
    return calles, barrios


def main():
    cods = ciudades()
    # Grupo 1: las 35 más pobladas (bajado el 20/11/2026). El resto en grupos de 15: en un solo grupo Overpass no respondió.
    grupos = [cods[:35]] + [cods[i:i + 15] for i in range(35, len(cods), 15)]
    tareas = []
    for i, g in enumerate(grupos, 1):
        c, b = consultas(g)
        if f"osm_calles_{i}.csv" in PARTIR:
            for j in range(0, len(g), 5):
                tareas.append((f"osm_calles_{i}{'abc'[j // 5]}.csv", consultas(g[j:j + 5])[0]))
        tareas += [t for t in ((f"osm_calles_{i}.csv", c), (f"osm_barrios_{i}.json", b)) if t[0] not in YA_BAJADOS | PARTIR]
    tareas += [(n, consultas([m])[0]) for n, m in SOLO_CALLES.items()]
    carpeta = DATOS.parent / "datos_municipales" / "osm"
    tareas = [t for t in tareas if not (carpeta / t[0]).exists()]      # solo lo que falta
    html = """<!doctype html><meta charset="utf-8"><title>Descargar OpenStreetMap</title>
<body style="font-family:sans-serif;max-width:640px;margin:40px auto;line-height:1.5">
<h1>Descargar barrios y calles de OpenStreetMap</h1>
<p>Pulsa el botón y deja esta pestaña abierta. Tarda unos minutos (si el servidor está ocupado, reintenta solo). Se guardan __N__ archivos en Descargas.</p>
<button id="b" style="font-size:18px;padding:10px 20px">Descargar</button><ul id="l"></ul>
<script>
const T=__TAREAS__, S=__SERVIDORES__;
async function bajar(nombre,q,li){
  for(let i=1;i<=5;i++){
    li.textContent=nombre+': descargando (intento '+i+')...';
    try{const r=await fetch(S[(i-1)%S.length],{method:'POST',body:new URLSearchParams({data:q})});
      if(!r.ok) throw new Error('error '+r.status);
      const b=await r.blob(); if(b.size<200) throw new Error('respuesta vacía');
      const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=nombre;a.click();
      li.textContent=nombre+': listo ('+Math.round(b.size/1e6)+' MB)';return;
    }catch(e){li.textContent=nombre+': '+e.message+', reintento en 2 minutos';await new Promise(s=>setTimeout(s,120000));}
  }
  li.textContent=nombre+': no se pudo descargar';
}
document.getElementById('b').onclick=async()=>{document.getElementById('b').disabled=true;
  for(const [n,q] of T){const li=document.createElement('li');document.getElementById('l').appendChild(li);await bajar(n,q,li);await new Promise(s=>setTimeout(s,60000));}
  const li=document.createElement('li');li.innerHTML='<b>Terminado.</b> Mueve los archivos osm_* de Descargas a datos_municipales\\\\osm';document.getElementById('l').appendChild(li);};
</script>""".replace("__TAREAS__", json.dumps(tareas)).replace("__SERVIDORES__", json.dumps(SERVIDORES)).replace("__N__", str(len(tareas)))
    (carpeta / "descargar_osm.html").write_text(html, encoding="utf-8")
    print(len(cods), "ciudades;", len(tareas), "archivos por descargar:", ", ".join(t[0] for t in tareas))


if __name__ == "__main__":
    main()
