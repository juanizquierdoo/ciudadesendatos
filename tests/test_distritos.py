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
sys.exit(1 if fallos else 0)
