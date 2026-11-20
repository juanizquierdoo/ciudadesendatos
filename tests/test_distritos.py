"""Nombres de distrito: cada nombre lleva fuente y, si la fuente pide cita, la ficha la muestra (B-26)."""
import csv
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
fallos = []
filas = list(csv.DictReader(open(BASE / "datos_limpios" / "nombres_distritos.csv", encoding="utf-8")))
ciudades = {c["cod_muni"]: c for c in json.load(open(BASE / "datos_limpios" / "ciudades_nivel1.json", encoding="utf-8-sig"))["ciudades"]}

sin_fuente = [r["codigo"] for r in filas if not r.get("fuente", "").strip()]
print(f"[{'OK   ' if not sin_fuente else 'FALLA'}] Cada nombre de distrito tiene fuente")
fallos += sin_fuente

citas = {r["codigo"][:5]: r["cita"] for r in filas if r.get("cita", "").strip()}
mal = []
for cod, cita in citas.items():
    c = ciudades.get(cod)
    if not c:
        continue
    html = (BASE / "web" / c["slug"] / "index.html").read_text(encoding="utf-8")
    if f"Nombres de los distritos: {cita}" not in html.replace("&#x27;", "'").replace("&amp;", "&"):
        mal.append(c["slug"])
print(f"[{'OK   ' if not mal else 'FALLA'}] Las fichas con nombres citados muestran la fuente ({len(citas)} ciudades) {mal or ''}")
fallos += mal

# Distritos sin nombre oficial: deben llevar código postal (callejero del INE) para que se sepa qué zona son
import re
sin_zona = [f'{c["nombre"]}: {x["nombre"]}' for c in ciudades.values() for x in c["distritos"]
            if not x["con_nombre_oficial"] and not (x.get("barrios") and " · " in x["nombre"])
            and not (x.get("zona") and x["zona"].get("cps") and " · CP " in x["nombre"])]
print(f"[{'OK   ' if not sin_zona else 'FALLA'}] Todo distrito sin nombre oficial lleva sus barrios o su código postal {sin_zona[:5] or ''}")
fallos += sin_zona
desnudos = []
for c in ciudades.values():
    html_c = (BASE / "web" / c["slug"] / "index.html").read_text(encoding="utf-8")
    if re.search(r'<th scope="row"[^>]*>Distrito \d+</th>', html_c):
        desnudos.append(c["slug"])
print(f"[{'OK   ' if not desnudos else 'FALLA'}] Ninguna tabla muestra solo 'Distrito N' {desnudos[:5] or ''}")
fallos += desnudos
sys.exit(1 if fallos else 0)
