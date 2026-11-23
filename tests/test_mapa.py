"""Comprobaciones del mapa esquemático de distritos (mapa_distritos.py + generar_web.py).

Uso (desde la carpeta del proyecto):   python tests/test_mapa.py
Solo usa la biblioteca estándar. Imprime OK o FALLA y termina con código 1 si algo falla.
La parte interactiva (pasar el cursor, cambiar el color) se prueba en un navegador con tests/prueba_navegador.js.
"""
from pathlib import Path
import csv
import json
import re
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
import mapa_distritos as md  # noqa: E402

WEB = BASE / "web"
CSV = BASE / "datos_limpios" / "mapa_distritos.csv"
ciudades = json.load(open(BASE / "datos_limpios" / "ciudades_nivel1.json", encoding="utf-8"))["ciudades"]
resultados = []


def comprobar(descripcion, errores):
    errores = list(errores)
    estado = "OK" if not errores else "FALLA"
    resultados.append(estado)
    print(f"[{estado:5}] {descripcion}")
    for e in errores[:8]:
        print("        -", e)


if not CSV.exists():
    comprobar("Existe datos_limpios/mapa_distritos.csv (python mapa_distritos.py)", ["falta el archivo"])
    sys.exit(1)

filas = list(csv.DictReader(open(CSV, encoding="utf-8")))
por_ciudad = {}
for r in filas:
    por_ciudad.setdefault(r["codigo"][:5], []).append(r)

# 1. cada ciudad con mapa tiene todos sus distritos, cada uno en una casilla distinta
err = []
for c in ciudades:
    rs = por_ciudad.get(c["cod_muni"])
    if not rs:
        continue
    if sorted(r["codigo"] for r in rs) != sorted(x["codigo"] for x in c["distritos"]):
        err.append(f"{c['nombre']}: los distritos del mapa no son los de la ficha")
    pos = [(r["col"], r["fila"]) for r in rs]
    if len(set(pos)) != len(pos):
        err.append(f"{c['nombre']}: dos distritos en la misma casilla")
    if max(int(r["col"]) for r in rs) >= md.MAX_COL:
        err.append(f"{c['nombre']}: más de {md.MAX_COL} columnas")
comprobar(f"Mapa completo y sin casillas repetidas en {len(por_ciudad)} ciudades", err)

# 2. Madrid conserva su colocación hecha a mano
err = [f"distrito {r['codigo']}" for r in por_ciudad.get("28079", [])
       if md.MADRID[int(r["codigo"][5:])] != (int(r["col"]), int(r["fila"]))]
comprobar("Madrid conserva el mapa hecho a mano", err if por_ciudad.get("28079") else ["Madrid no tiene mapa"])

# 3. el método calculado reproduce el mapa de Madrid hecho a mano (orientación norte-sur y este-oeste)
cen = md.centros({"28079"})["28079"]
g = md.rejilla(cen)
sg = lambda v: (v > 0) - (v < 0)
ok = tot = 0
for i in md.MADRID:
    for j in md.MADRID:
        if i < j:
            for k in (0, 1):
                a = sg(md.MADRID[i][k] - md.MADRID[j][k])
                b = sg(g["28079%02d" % i][k] - g["28079%02d" % j][k])
                if a and b:
                    tot += 1
                    ok += a == b
acuerdo = ok / tot
comprobar(f"El cálculo coincide con el mapa de Madrid hecho a mano en el {acuerdo:.0%} de las comparaciones (mínimo 95 %)",
          [] if acuerdo >= 0.95 else [f"solo {acuerdo:.1%}"])

# 4. ciudades principales con mapa
principales = {"28079": "Madrid", "08019": "Barcelona", "46250": "València", "41091": "Sevilla", "29067": "Málaga",
               "48020": "Bilbao", "01059": "Vitoria-Gasteiz", "20069": "Donostia", "36057": "Vigo", "15030": "A Coruña"}
comprobar("Tienen mapa: " + ", ".join(principales.values()), [n for m, n in principales.items() if m not in por_ciudad])

# 5. la web: cada ficha con mapa lleva sus datos, con las mismas cifras que el JSON, y la cita de OpenStreetMap
err = []
for c in ciudades:
    if c["cod_muni"] not in por_ciudad:
        continue
    pag = WEB / c["slug"] / "index.html"
    s = pag.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="mapa-datos">(.*?)</script>', s, re.S)
    if not m or 'id="grid"' not in s:
        err.append(f"{c['nombre']}: sin mapa en la ficha")
        continue
    datos = json.loads(m.group(1).replace("<\\/", "</"))
    if len(datos["distritos"]) != len(c["distritos"]):
        err.append(f"{c['nombre']}: {len(datos['distritos'])} casillas para {len(c['distritos'])} distritos")
    dj = {x["numero"]: x for x in c["distritos"]}
    for t in datos["distritos"]:
        x = dj[t["n"]]
        if t["renta"] != x["renta_hogar"]:
            err.append(f"{c['nombre']} distrito {t['n']}: renta distinta")
        if x["fiabilidad"] == "no_mostrar" and t["alq"] is not None:
            err.append(f"{c['nombre']} distrito {t['n']}: muestra alquiler con menos de 30 inmuebles")
        if x["fiabilidad"] in ("ok", "pocos_datos") and t["alq"] != x["alquiler_mes"]:
            err.append(f"{c['nombre']} distrito {t['n']}: alquiler distinto")
    if c["cod_muni"] != "28079" and "OpenStreetMap" not in s.split('id="mapa"')[1].split("</section>")[0]:
        err.append(f"{c['nombre']}: falta la cita de OpenStreetMap junto al mapa")
sin_mapa = [c["nombre"] for c in ciudades if c["cod_muni"] not in por_ciudad
            and 'id="mapa-datos"' in (WEB / c["slug"] / "index.html").read_text(encoding="utf-8")]
err += [f"{n}: tiene mapa sin estar en el CSV" for n in sin_mapa]
comprobar("Fichas con mapa: datos iguales que el JSON, sin alquiler poco fiable y con la cita de OSM", err)

# 6. escala de color fija, la misma en todas las ciudades, y etiqueta de lo que se mide
import generar_web as gw  # noqa: E402
js = (WEB / "assets" / "app.js").read_text(encoding="utf-8")
err = []
if json.dumps(gw.ESCALA_MAPA) not in js or "__ESCALA__" in js:
    err.append("app.js no lleva la escala fija ESCALA_MAPA")
if "Math.min.apply" in js.split("mapa esquemático")[-1]:
    err.append("el mapa todavía calcula la escala con el mínimo y el máximo de cada ciudad")
for k in ("Alquiler sobre renta del hogar (%)", "Alquiler mediano al mes (€)", "Renta neta media del hogar (€ al año)"):
    if k not in js:
        err.append(f"falta la etiqueta «{k}»")
comprobar("Misma escala de color en todos los mapas y etiqueta junto a la barra", err)

print(f"\nResumen: {resultados.count('OK')} OK, {resultados.count('FALLA')} FALLA")
sys.exit(1 if "FALLA" in resultados else 0)
